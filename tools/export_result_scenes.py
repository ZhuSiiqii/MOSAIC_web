"""Export the Text-to-Scene and Image-to-Scene Blender results as self-contained web GLBs.

Run from the website repository root:
    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
      --disable-autoexec --python tools/export_result_scenes.py

The source .blend files are read from ../scene and are never modified.
"""

import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Euler


SITE = Path(__file__).resolve().parents[1]
SOURCE_ROOT = SITE.parent / "scene"
OUTPUT = SITE / "assets" / "results"
OUTPUT.mkdir(parents=True, exist_ok=True)

SCENES = {
    "text-atmosphere-livingroom": SOURCE_ROOT / "text" / "atmosphere_livingroom" / "scene(3).blend",
    "text-atmosphere-bedroom": SOURCE_ROOT / "text" / "atmosphere_bedroom" / "scene(4).blend",
    "text-detailed-cafe": SOURCE_ROOT / "text" / "detailed_cafe" / "detailed_cafe.blend",
    "text-detailed-kitchen": SOURCE_ROOT / "text" / "detailed_kitchen" / "detailed_kitchen.blend",
    "text-functional-babyroom": SOURCE_ROOT / "text" / "functional_babyroom" / "text_functional2.blend",
    "text-functional-entertainment-room": SOURCE_ROOT / "text" / "functional_entertainment_room" / "scene.blend",
    "image-bedroom": SOURCE_ROOT / "img" / "bedroom" / "bedroom.blend",
    "image-livingroom": SOURCE_ROOT / "img" / "livingroom" / "livingroom.blend",
    "image-meetingroom": SOURCE_ROOT / "img" / "meetingroom" / "meetingroom.blend",
}

DEFAULT_CUTAWAY_PREFIXES = ("wall_south_", "wall_west_")
CUTAWAY_PREFIXES = {
    "text-atmosphere-bedroom": ("wall_south_", "wall_east_"),
}


def write_room_environment(width=256, height=128):
    """Create a subdued HDR environment with soft window and ceiling highlights."""
    target = OUTPUT / "room-environment.hdr"

    def rgbe(red, green, blue):
        brightest = max(red, green, blue)
        if brightest < 1e-32:
            return (0, 0, 0, 0)
        mantissa, exponent = math.frexp(brightest)
        scale = mantissa * 256.0 / brightest
        return (
            min(255, int(red * scale)),
            min(255, int(green * scale)),
            min(255, int(blue * scale)),
            exponent + 128,
        )

    with target.open("wb") as handle:
        handle.write(f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {height} +X {width}\n".encode("ascii"))
        for y in range(height):
            elevation = (0.5 - (y + 0.5) / height) * math.pi
            scanline = []
            for x in range(width):
                azimuth = ((x + 0.5) / width * 2.0 - 1.0) * math.pi
                upper = max(0.0, math.sin(elevation))
                base = 0.006 + 0.014 * upper
                window = 0.28 * math.exp(
                    -((azimuth + 2.25) / 0.34) ** 2
                    -((elevation - 0.18) / 0.42) ** 2
                )
                ceiling = 0.05 * math.exp(
                    -((azimuth - 0.7) / 0.8) ** 2
                    -((elevation - 0.92) / 0.28) ** 2
                )
                scanline.append(rgbe(
                    base * 0.82 + window * 0.92 + ceiling,
                    base * 0.9 + window * 0.98 + ceiling * 0.78,
                    base + window + ceiling * 0.58,
                ))
            handle.write(bytes((2, 2, width >> 8, width & 255)))
            for channel in range(4):
                values = bytes(pixel[channel] for pixel in scanline)
                for start in range(0, width, 128):
                    chunk = values[start:start + 128]
                    handle.write(bytes((len(chunk),)))
                    handle.write(chunk)
    return target


def prepare_materials():
    simplified = 0
    for material in bpy.data.materials:
        if not material.use_nodes or not material.node_tree:
            continue
        material.use_backface_culling = False
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        bsdf.inputs["Metallic"].default_value = 0.0
        if not bsdf.inputs["Roughness"].is_linked:
            bsdf.inputs["Roughness"].default_value = 0.68

        if not (material.name.startswith("wall_") or material.name.startswith("floor_")):
            continue
        textures = [node for node in nodes if node.type == "TEX_IMAGE" and node.image]
        albedo = next((node for node in textures if node.label == "albedo_path" or node.image.name.lower().startswith("albedo")), None)
        roughness = next((node for node in textures if node.label == "roughness_path" or node.image.name.lower().startswith("roughness")), None)
        normal = next((node for node in textures if node.label == "normal_path" or node.image.name.lower().startswith("normal")), None)
        if albedo:
            for link in list(bsdf.inputs["Base Color"].links):
                links.remove(link)
            links.new(albedo.outputs["Color"], bsdf.inputs["Base Color"])
        if roughness:
            for link in list(bsdf.inputs["Roughness"].links):
                links.remove(link)
            links.new(roughness.outputs["Color"], bsdf.inputs["Roughness"])
        if normal:
            normal_map = next((node for node in nodes if node.type == "NORMAL_MAP"), None)
            if normal_map:
                for link in list(bsdf.inputs["Normal"].links):
                    links.remove(link)
                for link in list(normal_map.inputs["Color"].links):
                    links.remove(link)
                normal_map.inputs["Strength"].default_value = 0.45
                links.new(normal.outputs["Color"], normal_map.inputs["Color"])
                links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
        simplified += 1
    return simplified


def resize_images(limit=1024):
    resized = 0
    for image in bpy.data.images:
        if image.source != "FILE":
            continue
        width, height = image.size
        largest = max(width, height)
        if largest <= limit:
            continue
        scale = limit / largest
        image.scale(max(1, round(width * scale)), max(1, round(height * scale)))
        resized += 1
    return resized


def reduce_meshes(meshes, face_limit=16000):
    reduced = 0
    for obj in meshes:
        faces = len(obj.data.polygons)
        if faces <= face_limit:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new("Web mesh reduction", "DECIMATE")
        modifier.ratio = max(0.01, face_limit / faces)
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            reduced += 1
        except RuntimeError:
            obj.modifiers.remove(modifier)
    return reduced


def add_web_lights(scene):
    local_lights = 0
    for obj in list(scene.objects):
        if obj.type != "LIGHT":
            continue
        if obj.data.type == "AREA" or obj.name.startswith("VRSceneKey"):
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if obj.data.type == "POINT":
            obj.data.energy = min(1.0, max(0.3, obj.data.energy * 0.002))
            obj.data.color = (1.0, 0.78, 0.6)
            obj.data.shadow_soft_size = max(obj.data.shadow_soft_size, 0.28)
            local_lights += 1

    def sun(name, energy, color, rotation):
        data = bpy.data.lights.new(name, "SUN")
        data.energy = energy
        data.color = color
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.rotation_euler = Euler(rotation)

    sun("Web window key", 0.018, (1.0, 0.92, 0.82), (0.55, -0.35, -0.65))
    sun("Web cool fill", 0.004, (0.72, 0.82, 1.0), (0.9, 0.25, 2.4))

    data = bpy.data.lights.new("Web overhead fill", "POINT")
    data.energy = 0.04
    data.color = (1.0, 0.91, 0.78)
    data.shadow_soft_size = 0.8
    overhead = bpy.data.objects.new("Web overhead fill", data)
    scene.collection.objects.link(overhead)
    overhead.location = (0.0, 0.0, 2.45)
    return local_lights + 3


report = {}
write_room_environment()
for slug, source in SCENES.items():
    if not source.exists():
        report[slug] = {"source": str(source), "missing": True}
        print(f"SKIP_MISSING {slug}: {source}", flush=True)
        continue

    print(f"EXPORTING {slug}", flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    removed = []
    cutaway_prefixes = CUTAWAY_PREFIXES.get(slug, DEFAULT_CUTAWAY_PREFIXES)
    for obj in list(bpy.context.scene.objects):
        if obj.name == "ceiling_01" or obj.name.startswith(cutaway_prefixes):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    simplified_materials = prepare_materials()
    exported_lights = add_web_lights(bpy.context.scene)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    before_faces = sum(len(obj.data.polygons) for obj in meshes)
    resized_images = resize_images()
    reduced_meshes = reduce_meshes(meshes)
    after_faces = sum(len(obj.data.polygons) for obj in meshes)

    bpy.ops.object.select_all(action="DESELECT")
    lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]
    for obj in meshes + lights:
        obj.hide_set(False)
        obj.select_set(True)

    target = OUTPUT / f"{slug}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(target),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=True,
        export_animations=False,
        export_extras=False,
        export_image_format="JPEG",
        export_image_quality=75,
    )
    report[slug] = {
        "source": str(source.relative_to(SOURCE_ROOT)),
        "bytes": target.stat().st_size,
        "meshes": len(meshes),
        "faces_before": before_faces,
        "faces_after": after_faces,
        "meshes_reduced": reduced_meshes,
        "images_resized": resized_images,
        "removed_for_cutaway": removed,
        "materials_simplified": simplified_materials,
        "lights_exported": exported_lights,
    }
    print(f"EXPORTED {slug}: {target.stat().st_size} bytes", flush=True)

with (OUTPUT / "result-scenes.json").open("w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
print("RESULT_SCENE_EXPORT_COMPLETE", flush=True)
