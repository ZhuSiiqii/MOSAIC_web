"""Build illustrative layout proxies from the bundled GLBs, without rendering.

Run with Blender --background --factory-startup --python this_file.py.
These bounds visualize the exported scene; they are not planner execution traces.
"""
import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector

OUTPUT = Path(__file__).resolve().parents[1] / 'assets' / 'scenes'
STAGES = ('structure', 'attached', 'primary', 'supported')
membership = {}
for index, stage in enumerate(STAGES):
    data = (OUTPUT / f'livingroom-{stage}.glb').read_bytes()
    document = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
    for node in document['nodes']:
        if 'mesh' in node:
            membership.setdefault(node['name'], index)

bpy.ops.import_scene.gltf(filepath=str(OUTPUT / 'livingroom-supported.glb'))
originals = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
materials = []
for stage, color in zip(STAGES, ((0.65, 0.72, 0.81), (0.08, 0.48, 0.38), (0.25, 0.44, 0.85), (0.95, 0.49, 0.19))):
    material = bpy.data.materials.new(stage)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = 0.85
    materials.append(material)

proxies = []
for obj in originals:
    if obj.name not in membership or obj.name == 'Television screen':
        continue
    stage = membership[obj.name]
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
    upper = Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lower + upper) / 2)
    proxy = bpy.context.object
    proxy.name = obj.name + '_layout'
    proxy.scale = tuple(max(upper[i] - lower[i], 0.018) for i in range(3))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    proxy.data.materials.append(materials[stage])
    proxy['stage'] = stage
    proxies.append(proxy)

for index, stage in enumerate(STAGES):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in proxies:
        obj.select_set(obj['stage'] <= index)
    path = OUTPUT / f'livingroom-layout-{stage}.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                            export_cameras=False, export_lights=False, export_animations=False)
    print(f'LAYOUT {stage}: {path.stat().st_size} bytes')
