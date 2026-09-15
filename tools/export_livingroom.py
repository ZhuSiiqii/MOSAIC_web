"""Run with Blender --background --factory-startup --python this_file.py.

Creates a presentation copy and cumulative web GLBs; never saves over the source.
"""
import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector

SITE = Path(__file__).resolve().parents[1]
SOURCE = SITE.parents[1] / 'scene' / 'detailed_livingroom_retry8.blend'
OUTPUT = SITE / 'assets' / 'scenes'
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene

# The south side is already open. Open the west side and roof for a two-wall cutaway.
removed = []
for name in list(bpy.data.objects.keys()):
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    if obj.name in {'ceiling_01', 'wall_west_01'} or obj.type in {'LIGHT', 'CAMERA'} or obj.name.startswith('west_wall_poster_01'):
        for child in list(obj.children_recursive):
            if child.name in bpy.data.objects:
                bpy.data.objects.remove(child, do_unlink=True)
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

attached = {'poster', 'ceiling_light'}
supported = {'book', 'small_potted_plant', 'fork', 'knife', 'plate', 'cup_of_tea', 'television'}
for obj in list(scene.objects):
    if obj.type != 'MESH':
        continue
    ancestor = obj
    while ancestor.parent and 'vrscene_entity_id' not in ancestor:
        ancestor = ancestor.parent
    category = ancestor.get('vrscene_category', 'structure')
    stage = 1 if category in attached else 3 if category in supported else 0 if category in {'floor', 'wall_segment', 'door', 'structure'} else 2
    entity = ancestor.get('vrscene_entity_id', obj.name)
    obj.name = entity + '_mesh' if obj.name.startswith('geometry_') else obj.name
    obj['display_stage'] = stage
    faces = len(obj.data.polygons)
    target = 3500 if stage == 3 else 16000
    if category == 'television':
        target = 16000
    if faces > target:
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new('Web mesh reduction', 'DECIMATE')
        modifier.ratio = target / faces
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    if faces > 100:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    for material in obj.data.materials:
        if not material or not material.use_nodes:
            continue
        material.use_backface_culling = False
        bsdf = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            bsdf.inputs['Roughness'].default_value = 0.72
            bsdf.inputs['Metallic'].default_value = 0.0
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                limit = 512 if stage == 3 else 1024
                if max(node.image.size) > limit:
                    node.image.scale(limit, limit)

def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

plaster = material('Warm ivory plaster', (0.79, 0.76, 0.70))

# A clean dark screen avoids the noisy generated screen texture in the display copy.
television = bpy.data.objects['television_01_mesh']
television.data.materials.clear()
television.data.materials.append(material('Television graphite frame', (0.018, 0.021, 0.026), 0.6))
screen_mesh = bpy.data.meshes.new('Television screen surface')
screen_mesh.from_pydata([(-0.75, -2.175, 0.57), (0.75, -2.175, 0.57), (0.75, -2.175, 1.38), (-0.75, -2.175, 1.38)], [], [(3, 2, 1, 0)])
screen = bpy.data.objects.new('Television screen', screen_mesh)
scene.collection.objects.link(screen)
screen.data.materials.append(material('Dark screen glass', (0.008, 0.014, 0.022), 0.35))
screen['display_stage'] = 3
for name in ('wall_north_01', 'wall_east_01'):
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(plaster)

# A single UV plane keeps the parquet and baked contact shadows portable to glTF.
old_floor = bpy.data.objects['floor_01']
bpy.data.objects.remove(old_floor, do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0.023))
floor = bpy.context.object
floor.name = 'floor_01'
floor.scale = (3.5, 2.5, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
floor['display_stage'] = 0
parquet = material('Parquet floor', (0.55, 0.39, 0.25), 0.72)
floor.data.materials.append(parquet)
nodes, links = parquet.node_tree.nodes, parquet.node_tree.links
uv = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value = (2.0, 2.0, 1.0)
texture = nodes.new('ShaderNodeTexImage')
texture.image = bpy.data.images['albedo.jpg']
links.new(uv.outputs['UV'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
links.new(texture.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.075))
plinth = bpy.context.object
plinth.name = 'Display foundation'
plinth.scale = (7.02, 5.02, 0.18)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
plinth.data.materials.append(material('Ivory foundation', (0.72, 0.69, 0.64)))
plinth['display_stage'] = 0
bevel = plinth.modifiers.new('Soft foundation edge', 'BEVEL')
bevel.width = 0.025
bevel.segments = 3
bpy.context.view_layer.objects.active = plinth
bpy.ops.object.modifier_apply(modifier=bevel.name)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.world = bpy.data.worlds.new('Soft studio environment')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.82, 0.87, 1.0, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45

def area(name, location, energy, color, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 0.5)) - obj.location).to_track_quat('-Z', 'Y').to_euler()

area('Warm softbox', (2, 3, 7), 1100, (1.0, 0.86, 0.71), 5)
area('Cool fill', (-3, 1, 5), 650, (0.78, 0.87, 1.0), 4)
area('Top softbox', (0, -1, 7), 800, (1.0, 0.96, 0.88), 4)

bpy.ops.object.select_all(action='DESELECT')
floor.select_set(True)
bpy.context.view_layer.objects.active = floor
ao = bpy.data.images.new('Floor contact occlusion', width=1024, height=1024, alpha=False)
ao.colorspace_settings.name = 'Non-Color'
ao_node = nodes.new('ShaderNodeTexImage')
ao_node.image = ao
nodes.active = ao_node
scene.render.bake.margin = 8
bpy.ops.object.bake(type='AO')
ao.pack()
group = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
group.interface.new_socket(name='Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
settings = nodes.new('ShaderNodeGroup')
settings.node_tree = group
links.new(ao_node.outputs['Color'], settings.inputs['Occlusion'])

camera_data = bpy.data.cameras.new('Web presentation camera')
camera = bpy.data.objects.new('Web presentation camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (10, 12, 10)
camera.rotation_euler = (Vector((0, 0, 0.9)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 10.3
scene.camera = camera
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 900, 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'
scene.render.filepath = str(OUTPUT / 'livingroom-poster.png')

# Bake is specific to the complete display. Earlier layers use an unshadowed floor.
meshes = [obj for obj in scene.objects if obj.type == 'MESH']
report = {'source': SOURCE.name, 'removed': removed, 'stages': {}}
for index, stage in enumerate(('structure', 'attached', 'primary', 'supported')):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(obj.get('display_stage', 0) <= index)
    if index == 3:
        if not settings.inputs['Occlusion'].is_linked:
            links.new(ao_node.outputs['Color'], settings.inputs['Occlusion'])
    else:
        for link in list(settings.inputs['Occlusion'].links):
            links.remove(link)
    filepath = OUTPUT / f'livingroom-{stage}.glb'
    bpy.ops.export_scene.gltf(filepath=str(filepath), export_format='GLB', use_selection=True,
        export_apply=True, export_cameras=False, export_lights=False, export_animations=False,
        export_extras=False, export_image_format='JPEG', export_image_quality=85)
    # Keep baked contact shadows subtle under the viewer's neutral environment light.
    data = filepath.read_bytes()
    json_size = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + json_size])
    for mat in gltf.get('materials', []):
        if 'occlusionTexture' in mat:
            mat['occlusionTexture']['strength'] = 0.6
    encoded = json.dumps(gltf, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    remainder = data[20 + json_size:]
    filepath.write_bytes(struct.pack('<III', 0x46546C67, 2, 20 + len(encoded) + len(remainder)) + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + remainder)
    report['stages'][stage] = {'bytes': filepath.stat().st_size, 'meshes': sum(o.select_get() for o in meshes),
        'faces': sum(len(o.data.polygons) for o in meshes if o.select_get())}

# Pack the edited presentation copy; it is kept outside the deployable website.
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE.with_name('detailed_livingroom_web.blend')))
with open(OUTPUT / 'scene-info.json', 'w') as handle:
    json.dump(report, handle, indent=2)
bpy.ops.render.render(write_still=True)
print('WEB_SCENE_EXPORT_COMPLETE', json.dumps(report))
