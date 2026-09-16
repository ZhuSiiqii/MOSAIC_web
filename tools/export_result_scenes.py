"""Export the Text-to-Scene and Image-to-Scene Blender results as self-contained web GLBs.

Run from the website repository root:
    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
      --disable-autoexec --python tools/export_result_scenes.py

The source .blend files are read from ../scene and are never modified.
"""

import json
from pathlib import Path

import bpy


SITE = Path(__file__).resolve().parents[1]
SOURCE_ROOT = SITE.parent / "scene"
OUTPUT = SITE / "assets" / "results"
OUTPUT.mkdir(parents=True, exist_ok=True)

SCENES = {
    "text-atmosphere-bedroom": SOURCE_ROOT / "text" / "atmosphere_bedroom" / "text_atmosphere.blend",
    "text-detailed-cafe": SOURCE_ROOT / "text" / "detailed_cafe" / "detailed_cafe.blend",
    "text-detailed-kitchen": SOURCE_ROOT / "text" / "detailed_kitchen" / "detailed_kitchen.blend",
    "text-functional-babyroom": SOURCE_ROOT / "text" / "functional_babyroom" / "text_functional2.blend",
    "text-functional-entertainment-room": SOURCE_ROOT / "text" / "functional_entertainment_room" / "scene.blend",
    "image-bedroom": SOURCE_ROOT / "img" / "bedroom" / "bedroom.blend",
    "image-livingroom": SOURCE_ROOT / "img" / "livingroom" / "livingroom.blend",
    "image-meetingroom": SOURCE_ROOT / "img" / "meetingroom" / "meetingroom.blend",
}


def resize_images(limit=512):
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


def reduce_meshes(meshes, face_limit=6000):
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


report = {}
for slug, source in SCENES.items():
    if not source.exists():
        report[slug] = {"source": str(source), "missing": True}
        print(f"SKIP_MISSING {slug}: {source}", flush=True)
        continue

    print(f"EXPORTING {slug}", flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    removed = []
    for name in ("ceiling_01", "wall_west_01"):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            removed.append(name)
            bpy.data.objects.remove(obj, do_unlink=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    before_faces = sum(len(obj.data.polygons) for obj in meshes)
    resized_images = resize_images()
    reduced_meshes = reduce_meshes(meshes)
    after_faces = sum(len(obj.data.polygons) for obj in meshes)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.hide_set(False)
        obj.select_set(True)

    target = OUTPUT / f"{slug}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(target),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
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
    }
    print(f"EXPORTED {slug}: {target.stat().st_size} bytes", flush=True)

with (OUTPUT / "result-scenes.json").open("w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
print("RESULT_SCENE_EXPORT_COMPLETE", flush=True)
