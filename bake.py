'''
Copyright (C) 2020-2023 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of Scattershot, created by Jonathan Lampel.

All code distributed with this add-on is open source as described below.

Scattershot is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

import bpy, mathutils
from .utilities import get_scatter_sources, has_scatter_uvs, mode_toggle, save_image
from .defaults import texture_names, data_channels, detail_channels, data_color_spaces, file_types, node_names
from .clear_bake import clear_image_bake
from .unwrap import unwrap
from .denoise_image import denoise_image
from copy import copy


def get_bake_properties(scene):
  return {
    'engine': scene.render.engine,
    'bake_type': scene.cycles.bake_type,
    'use_selected_to_active': scene.render.bake.use_selected_to_active,
    'target': scene.render.bake.target,
    'use_clear': scene.render.bake.use_clear,
    'use_bake_multires': scene.render.use_bake_multires,
    'samples': scene.cycles.samples,
    'margin_type': scene.render.bake.margin_type,
    'margin': scene.render.bake.margin,
    'denoise': scene.cycles.use_denoising
  }


def set_bake_properties(scene, properties):
  scene.render.engine = properties['engine']
  scene.cycles.bake_type = properties['bake_type']
  scene.render.bake.use_selected_to_active = properties['use_selected_to_active']
  scene.render.bake.target = properties['target']
  scene.render.bake.use_clear = properties['use_clear']
  scene.render.use_bake_multires = properties['use_bake_multires']
  scene.cycles.samples = properties['samples']
  scene.render.bake.margin_type = properties['margin_type']
  scene.render.bake.margin = properties['margin']
  scene.cycles.use_denoising = properties['denoise']


def is_in_texture_set(object, active_material):
  for slot in object.material_slots:
    if slot.material == active_material:
      return True
  return False


def create_texture(self, nodes, texture_node_name, texture_file_name, output_name, location):
  texture = nodes.new('ShaderNodeTexImage')
  texture.name = texture_node_name
  texture.location = location
  texture.image = bpy.data.images.new(texture_file_name, self.width, self.height, float_buffer = True, is_data = True)
  color_spaces = [x.name for x in bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items]
  if output_name in data_channels or output_name in detail_channels:
    for space in data_color_spaces:
      if space in color_spaces:
        texture.image.colorspace_settings.name = space
        break
  else:
    texture.image.colorspace_settings.name = 'sRGB'
  return texture


def save_bake(context, preferences, texture, texture_file_name, output_name):
  if output_name in detail_channels:
    file_format = preferences.data_format
  else:
    file_format = preferences.format

  if output_name in detail_channels and preferences.data_format == 'OPEN_EXR':
    color_depth = preferences.data_float
  elif output_name in detail_channels:
    color_depth = preferences.data_depth
  elif preferences.format == 'OPEN_EXR':
    color_depth = preferences.color_float
  else:
    color_depth = preferences.color_depth

  format_settings = {
    'format': file_format,
    'color_depth': color_depth,
  }
  texture.image.filepath_raw = f"{preferences.path}\{texture_file_name}.{file_types[file_format]}"
  save_image(context, texture.image, format_settings)
  return format_settings


def setup_bake_uvs(self, scatter_node, new_textures):
  # TODO: Make sure the right UVs are always used
  # TODO: Make sure object has UVs!
  if 'UV Map' not in [x.name for x in scatter_node.inputs]:
    uv_input = scatter_node.node_tree.inputs.new('NodeSocketVector', 'UV Map')
    uv_input.hide_value = True
  group_input = scatter_node.node_tree.nodes['Group Input']
  mixed_uvs = scatter_node.node_tree.nodes['UVs']
  scatter_node.node_tree.links.new(group_input.outputs['UV Map'], scatter_node.node_tree.nodes['User UVs'].inputs[0])
  for texture in new_textures:
    scatter_node.node_tree.links.new(mixed_uvs.outputs[0], texture.inputs[0])
  if not self.unwrap_method == 'existing':
    scatter_node.node_tree.nodes['UV Map'].uv_map = "ScattershotUVs"


def get_material_output(context):
  if context.selected_nodes[0].id_data.get_output_node('CYCLES'):
    return context.selected_nodes[0].id_data.get_output_node('CYCLES')
  else:
    return context.selected_nodes[0].id_data.nodes.new('ShaderNodeOutputMaterial')


def connect_output(context, material_output, channel_output):
  links = context.selected_nodes[0].id_data.links
  prev_output_socket = None
  if material_output.inputs[0].links:
    prev_output_socket = material_output.inputs[0].links[0].from_socket
  if channel_output.name == 'Normal':
    # TODO: Properly output tangent space normals
    pass
  links.new(channel_output, material_output.inputs[0])
  return prev_output_socket


def cleanup_output_connections(links, prev_output_socket, material_output):
  if prev_output_socket:
    links.new(prev_output_socket, material_output.inputs[0])
  else:
    links.remove(material_output.inputs[0].links[0])


def bake_image(objects, nodes, texture):
  nodes.active = texture
  # TODO: Bake just the material that has the scatter, not the entire object
  bpy.ops.object.select_all(action='DESELECT')
  for obj in objects:
    obj.select_set(True)
  bpy.ops.object.bake()


def bake_scatter(self, context, objects):
  preferences = context.preferences.addons[__package__].preferences
  selected_nodes = context.selected_nodes
  nodes = selected_nodes[0].id_data.nodes
  links = selected_nodes[0].id_data.links
  material_output = get_material_output(context)

  only_displacement = self.Displacement and all(x == False for x in [
    self.Albedo, self.AO, self.Metalness, self.Roughness, self.Glossiness,
    self.Specular, self.Emission, self.Alpha, self.Bump, self.Normal
  ])

  scatter_nodes = [x for x in selected_nodes if get_scatter_sources([x])]
  for scatter_node in scatter_nodes:
    channel_outputs = scatter_node.outputs

    new_textures = []
    bake_outputs = [x for x in channel_outputs if x.name in texture_names.keys()]

    clear_image_bake(context)

    for output_idx, output in enumerate(bake_outputs):
      if getattr(self, output.name) or output.name == 'Image':
        texture_node_name = f"Baked {output.name}"

        texture_file_name = preferences.name.replace(
          '{C}', output.name).replace(
          '{G}', scatter_node.node_tree.name).replace(
          '{L}', scatter_node.label).replace(
          '{M}', context.active_object.active_material.name).replace(
          '{N}', scatter_node.name)

        group_nodes = scatter_node.node_tree.nodes
        group_links = scatter_node.node_tree.links

        # Overwrites previous baked result or creates a new texture
        if texture_node_name in [x.name for x in group_nodes]:
          texture = group_nodes[texture_node_name]
        else:
          texture = create_texture(self, group_nodes, texture_node_name, texture_file_name, output.name, [3000, -300 * output_idx])
          new_textures.append(texture)

        current_output_socket = connect_output(context, output)

        # Bakes the texture
        bake_image(objects, group_nodes, texture)
        format_settings = save_bake(context, preferences, texture, texture_file_name, output.name)
        if self.denoise:
          denoise_image(context, texture.image, format_settings)

        cleanup_output_connections(links, current_output_socket, material_output)

        # Links texture to group node
        if texture_node_name not in [x.name for x in scatter_node.outputs]:
          if output.name == 'Normal':
            output_type = 'NodeSocketVector'
          elif output.name in data_channels:
            output_type = 'NodeSocketFloat'
          else:
            output_type = 'NodeSocketColor'
          scatter_node.node_tree.outputs.new(output_type, texture_node_name)
          scatter_node.node_tree.outputs.move(len(scatter_node.node_tree.outputs) -1, len(scatter_node.node_tree.outputs) -2)
        group_links.new(texture.outputs[0], group_nodes["Group Output"].inputs[texture_node_name])

        # Rewires socket connections
        to_sockets = [x.to_socket for x in output.links]
        for socket in to_sockets:
          links.new(scatter_node.outputs[texture_node_name], socket)

    # Moves Displacement to the bottom
    output_count = len(scatter_node.outputs)
    for output_idx, output in enumerate(scatter_node.node_tree.outputs):
      if output.name == 'Baked Displacement':
        scatter_node.node_tree.outputs.move(output_idx, len(scatter_node.node_tree.outputs) - 2)
        break

    setup_bake_uvs(self, scatter_node, new_textures)

    # Hides unused sockets
    if not only_displacement:
      for output in scatter_node.outputs:
        if output.name in texture_names.keys() or output.name == 'Random Color':
          output.hide = True
      for input in scatter_node.inputs:
        if input.name != 'UV Map':
          input.hide = True


def bake_coordinates(self, context, objects):
  preferences = context.preferences.addons[__package__].preferences
  selected_nodes = context.selected_nodes
  nodes = selected_nodes[0].id_data.nodes
  links = selected_nodes[0].id_data.links
  scatter_nodes = [x for x in selected_nodes if get_scatter_sources([x])]
  material_output = get_material_output(context)

  for scatter_node in scatter_nodes:
    group_nodes = scatter_node.node_tree.nodes
    group_links = scatter_node.node_tree.links
    new_coordinates_textures = []
    new_cell_color_textures = []
    coordinates_nodes = [x for x in group_nodes if x.label == node_names['scatter_coordinates']]
    bake_socket = scatter_node.node_tree.outputs.new('NodeSocketColor', 'Bake Output')
    prev_output_socket = connect_output(context, material_output, scatter_node.outputs['Bake Output'])

    for coordinates_node in coordinates_nodes:
      coordinates_node.hide = True

      # Bake Vectors
      group_links.new(coordinates_node.outputs[0], group_nodes['Group Output'].inputs['Bake Output'])
      bake_name = f'{scatter_node.name}_{coordinates_node.name}_vector'
      if bake_name in [x.name for x in group_nodes]:
        texture = group_nodes[bake_name]
      else:
        location = [coordinates_node.location[0], coordinates_node.location[1] - 150]
        texture = create_texture(self, group_nodes, bake_name, bake_name, 'Normal', location)
        texture.hide = True
        new_coordinates_textures.append(texture)
      bake_image(objects, group_nodes, texture)
      format_settings = save_bake(context, preferences, texture, bake_name, 'Normal')
      if self.denoise:
        denoise_image(context, texture.image, format_settings)
      # Replace outputs
      for link in coordinates_node.outputs[0].links:
        group_links.new(texture.outputs[0], link.to_socket)

      # Bake Random Colors
      '''
      if coordinates_node.outputs[1].links:
        # Set up nodes for baking
        group_links.new(coordinates_node.outputs[1], bake_output)
        bake_name = f'{scatter_node.name}_{coordinates_node.name}_color'
        if bake_name in [x.name for x in group_nodes]:
          texture = group_nodes[bake_name]
        else:
          location = [coordinates_node.location[0], coordinates_node.location[1] - 600]
          texture = create_texture(self, group_nodes, bake_name, bake_name, 'color', location)
          new_coordinates_textures.append(texture)
        # Bake Texture
        # TODO: Bake just the material that has the scatter, not the whole object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
          obj.select_set(True)
        bpy.ops.object.bake()
        format_settings = save_bake(context, preferences, texture, bake_name, 'color')
        if self.denoise:
          denoise_image(context, texture.image, format_settings)
        # Replace outputs
        for link in coordinates_node.outputs[1].links:
          group_links.new(texture.outputs[1], link.to_socket)
      '''


    setup_bake_uvs(self, scatter_node, new_coordinates_textures + new_cell_color_textures)
    cleanup_output_connections(links, prev_output_socket, material_output)
    scatter_node.node_tree.outputs.remove(bake_socket)


class NODE_OT_bake_scatter(bpy.types.Operator):
  bl_label = "Bake Scatter"
  bl_idname = "node.bake_scatter"
  bl_description = "Bakes the procedural result to new image textures using UV coordinates"
  bl_space_type = "NODE_EDITOR"
  bl_region_type = "UI"
  bl_options = {'REGISTER', 'UNDO'}


  objects: bpy.props.EnumProperty(
    name = "Objects",
    description = "Choose which objects to bake",
    items = [
      ('selected', 'Selected', 'Bakes only the selected objects'),
      ('texture_set', 'Texture Set', 'Bakes all objects containing this material')
    ],
    default = 'texture_set'
  )
  method: bpy.props.EnumProperty(
    name="Bake",
    description="Bakes either the scattered coordinates passed to the images or the final output of each channel",
    items = [
      ('coordinates', 'Coordinates', "Bakes the coordinates passed to the images. Best for scattering displacement over large surfaces when rendering in Blender"),
      ('result', 'Result', "Bakes the final output of each channel. Best for exporting the result to other apps")
    ],
    default="result"
  )
  Albedo: bpy.props.BoolProperty(
    name="Albedo",
    description="Bake the albedo channel",
    default = False
  )
  AO: bpy.props.BoolProperty(
    name="AO",
    description="Bake the ambient occlusion channel",
    default = False
  )
  Metalness: bpy.props.BoolProperty(
    name="Metalness",
    description="Bake the metalness channel",
    default = False
  )
  Roughness: bpy.props.BoolProperty(
    name="Roughness",
    description="Bake the roughness channel",
    default = False
  )
  Glossiness: bpy.props.BoolProperty(
    name="Glossiness",
    description="Bake the glossiness channel",
    default = False
  )
  Specular: bpy.props.BoolProperty(
    name="Specular",
    description="Bake the specular channel",
    default = False
  )
  Emission: bpy.props.BoolProperty(
    name="Emission",
    description="Bake the emission channel",
    default = False
  )
  Alpha: bpy.props.BoolProperty(
    name="Alpha",
    description="Bake the alpha channel",
    default = False
  )
  Bump: bpy.props.BoolProperty(
    name="Bump",
    description="Bake the bump channel",
    default = False
  )
  Normal: bpy.props.BoolProperty(
    name="Normal",
    description="Bake the normal channel. Not yet supported by Scattershot.",
    default = False
  )
  Displacement: bpy.props.BoolProperty(
    name="Displacement",
    description="Bake the displacement channel",
    default = True
  )
  should_unwrap: bpy.props.BoolProperty(
    name = 'Unwrap',
    description = 'Creates a new UV unwrap before baking',
    default = True
  )
  unwrap_method: bpy.props.EnumProperty(
    name = 'Method',
    description = 'Determines how the new UVs are projected',
    items = [
      ('smart', 'Smart UV Projection', "Creates new UVs based on Blender's Smart UV Project algorithm"),
      ('cube', 'Cube Projection', "Creates new UVs based on Blender's Cube Projection"),
      ('cylinder', 'Cylinder Projection', "Creates new UVs based on Blender's Cylinder Projection"),
      ('sphere', 'Sphere Projection', "Creates new UVs based on Blender's Sphere Projection"),
      ('side', 'Local X Projection', "Creates new UVs based on a flat projection from the local X"),
      ('front', 'Local Y Projection', "Creates new UVs based on a flat projection from the local Y"),
      ('top', 'Local Z Projection', "Creates new UVs based on a flat projection from the local Z"),
      ('x', 'Global X Projection', "Creates new UVs based on a flat projection from the global X"),
      ('y', 'Global Y Projection', "Creates new UVs based on a flat projection from the global Y"),
      ('z', 'Global Z Projection', "Creates new UVs based on a flat projection from the global Z"),
    ],
    default = 'smart'
  )
  smart_project_angle: bpy.props.FloatProperty(
    name = 'Angle Limit',
    description = "Angles higher than this threashold will act like seams",
    default = 0.78539816, #45 degrees
    min = 0,
    max = 89,
    subtype = 'ANGLE'
  )
  apply_scale: bpy.props.BoolProperty(
    name = 'Apply Scale',
    description = 'Applies scale before unwrapping so that all UVs are consistant',
    default = True
  )
  width: bpy.props.IntProperty(
    name = "Width",
    description = "Resolution in the X direction",
    default = 1080
  )
  height: bpy.props.IntProperty(
    name = "Height",
    description = "Resolution in the Y direction",
    default = 1080
  )
  samples: bpy.props.IntProperty(
    name = "Samples",
    description = "The number of Cycles samples to bake with",
    default = 6,
    min = 1,
    max = 500
  )
  denoise: bpy.props.BoolProperty(
    name = 'Denoise',
    description = 'Run denoising on the texture after it is baked.',
    default = True
  )

  def draw(self, context):

    layout = self.layout
    layout.use_property_split = True

    layout.prop(self, 'method', expand=True)
    layout.separator()

    if self.method == 'result':
      layout.prop(self, "objects")
      layout.separator()

      scatter_nodes = [x for x in context.selected_nodes if get_scatter_sources([x])]
      channels = []
      for scatter_node in scatter_nodes:
        for output in scatter_node.outputs:
          channels.append(output.name)

      channels_column = layout.column(heading = 'Channels')
      if 'Albedo' in channels:
        channels_column.prop(self, "Albedo")
      if 'AO' in channels:
        channels_column.prop(self, "AO")
      if 'Metalness' in channels:
        channels_column.prop(self, "Metalness")
      if 'Roughness' in channels:
        channels_column.prop(self, "Roughness")
      if 'Glossiness' in channels:
        channels_column.prop(self, "Glossiness")
      if 'Specular' in channels:
        channels_column.prop(self, "Specular")
      if 'Emission' in channels:
        channels_column.prop(self, "Emission")
      if 'Alpha' in channels:
        channels_column.prop(self, "Alpha")
      if 'Bump' in channels:
        channels_column.prop(self, "Bump")
      if 'Normal' in channels:
        normal_row = channels_column.row()
        normal_row.enabled = False
        normal_row.prop(self, "Normal")
      if 'Displacement' in channels:
        channels_column.prop(self, "Displacement")

      layout.separator()

    uv = layout.column(heading="UVs")
    uv.prop(self, "should_unwrap")
    uv_column = uv.column()
    uv_column.enabled = self.should_unwrap
    uv_column.prop(self, "unwrap_method")
    if self.unwrap_method == 'smart':
      uv_column.prop(self, 'smart_project_angle')
    uv_column.prop(self, 'apply_scale')

    layout.separator()

    tex = layout.column(heading='Texture')
    resolution = tex.column(align = True)
    resolution.prop(self, "width")
    resolution.prop(self, "height")

    layout.separator()

    layout.prop(self, "samples")
    layout.prop(self, "denoise")

    layout.separator()

  @classmethod
  def poll(cls, context):
    return get_scatter_sources(context.selected_nodes)

  def invoke(self, context, event):
      return context.window_manager.invoke_props_dialog(self)

  def execute(self, context):
    # switching modes prevents context errors
    prev_mode = mode_toggle(context, 'OBJECT')
    prev_bake_properties = get_bake_properties(context.scene)
    set_bake_properties(context.scene, {
      'engine': 'CYCLES',
      'bake_type': 'EMIT',
      'use_selected_to_active': False,
      'target': 'IMAGE_TEXTURES',
      'use_clear': False,
      'use_bake_multires': False,
      'samples': self.samples,
      'margin_type': 'ADJACENT_FACES',
      'denoise': False,
      'margin': int((self.width + self.height / 4) / 128)
    })
    selected_object_names = [x.name for x in context.selected_objects]
    active_material = context.active_object.active_material
    active_obj_name = copy(context.active_object.name)

    if self.method == 'coordinates' or self.objects == 'texture_set':
      objects = [x for x in context.scene.objects if x.material_slots.items() and is_in_texture_set(x, active_material)]
    else:
      objects = context.selected_objects

    # if self.unwrap_method != 'existing': unwrap(self, context, objects)

    if self.method == 'coordinates':
      bake_coordinates(self, context, objects)
    else:
      bake_scatter(self, context, objects)

    for obj in context.scene.objects:
      obj.select_set(True) if obj.name in selected_object_names else obj.select_set(False)
    context.view_layer.objects.active = bpy.data.objects[active_obj_name]
    set_bake_properties(context.scene, prev_bake_properties)
    mode_toggle(context, prev_mode)

    return {'FINISHED'}



def register():
  bpy.utils.register_class(NODE_OT_bake_scatter)

def unregister():
  bpy.utils.unregister_class(NODE_OT_bake_scatter)