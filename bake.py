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
from .utilities.node_interface import create_socket, get_io_sockets, get_socket, move_socket
from .utilities.utilities import get_scatter_sources, has_scatter_uvs, mode_toggle, save_image
from .defaults import texture_names, data_channels, detail_channels, data_color_spaces, file_types
from .clear_bake import clear_bake
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


def bake_scatter(self, context, objects):
  preferences = context.preferences.addons[__package__].preferences
  selected_nodes = context.selected_nodes
  nodes = selected_nodes[0].id_data.nodes
  links = selected_nodes[0].id_data.links

  only_displacement = self.Displacement and all(x == False for x in [
    self.Albedo, self.AO, self.Metalness, self.Roughness, self.Glossiness,
    self.Specular, self.Emission, self.Alpha, self.Bump, self.Normal
  ])

  scatter_nodes = [x for x in selected_nodes if get_scatter_sources([x])]
  for scatter_node in scatter_nodes:
    channel_outputs = scatter_node.outputs

    new_textures = []
    bake_outputs = [x for x in channel_outputs if x.name in texture_names.keys()]

    clear_bake(context)

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
          texture = group_nodes.new('ShaderNodeTexImage')
          new_textures.append(texture)
          texture.name = texture_node_name
          texture.location = [3000, -300 * output_idx]
          texture.image = bpy.data.images.new(texture_file_name, self.width, self.height, float_buffer = True, is_data = True)
          color_spaces = [x.name for x in bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items]
          if output.name in data_channels or output.name in detail_channels:
            for space in data_color_spaces:
              if space in color_spaces:
                texture.image.colorspace_settings.name = space
                break
          else:
            texture.image.colorspace_settings.name = 'sRGB'

        # Links the channel output to the material output
        if selected_nodes[0].id_data.get_output_node('CYCLES'):
          material_output = selected_nodes[0].id_data.get_output_node('CYCLES')
        else:
          material_output = nodes.new('ShaderNodeOutputMaterial')
        if material_output.inputs[0].links:
          current_output_socket = material_output.inputs[0].links[0].from_socket
        else:
          current_output_socket = ''
        if output.name == 'Normal':
          # TODO: Properly output tangent space normals
          pass
        links.new(output, material_output.inputs[0])

        # Bakes the texture
        group_nodes.active = texture
        for obj in objects: obj.select_set(True)
        bpy.ops.object.bake()

        # Saves the texture
        if output.name in detail_channels:
          file_format = preferences.data_format
        else:
          file_format = preferences.format

        if output.name in detail_channels and preferences.data_format == 'OPEN_EXR':
          color_depth = preferences.data_float
        elif output.name in detail_channels:
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

        if self.denoise:
          denoise_image(context, texture.image, format_settings)

        # Cleans up output connections
        if current_output_socket:
          links.new(current_output_socket, material_output.inputs[0])
        else:
          links.remove(material_output.inputs[0].links[0])

        # Links texture to group node
        if texture_node_name not in [x.name for x in scatter_node.outputs]:
          if output.name == 'Normal':
            output_type = 'NodeSocketVector'
          elif output.name in data_channels:
            output_type = 'NodeSocketFloat'
          else:
            output_type = 'NodeSocketColor'
          new_socket = create_socket(scatter_node.node_tree, 'OUTPUT', output_type, texture_node_name)
          output_count = len(get_io_sockets(scatter_node.node_tree, 'OUTPUT'))
          move_socket(scatter_node.node_tree, 'OUTPUT', new_socket, output_count -2)
        group_links.new(texture.outputs[0], group_nodes["Group Output"].inputs[texture_node_name])

        # Rewires socket connections
        to_sockets = [x.to_socket for x in output.links]
        for socket in to_sockets:
          links.new(scatter_node.outputs[texture_node_name], socket)

    # Moves Displacement to the bottom
    displacement_socket = get_socket(scatter_node.node_tree, 'OUTPUT', 'Baked Displacement')
    output_count = len(scatter_node.outputs)
    move_socket(scatter_node.node_tree, 'OUTPUT', displacement_socket, output_count -2)

    # Sets up nodes for UVs
    # TODO: Make sure the right UVs are always used
    # TODO: Make sure object has UVs!
    if 'UV Map' not in [x.name for x in scatter_node.inputs]:
      uv_input = create_socket(scatter_node.node_tree, 'INPUT', 'NodeSocketVector', 'UV Map')
      uv_input.hide_value = True
    group_input = scatter_node.node_tree.nodes['Group Input']
    mixed_uvs = scatter_node.node_tree.nodes['UVs']
    scatter_node.node_tree.links.new(group_input.outputs['UV Map'], scatter_node.node_tree.nodes['User UVs'].inputs[0])
    for texture in new_textures:
      scatter_node.node_tree.links.new(mixed_uvs.outputs[0], texture.inputs[0])
    if not self.unwrap_method == 'existing':
      scatter_node.node_tree.nodes['UV Map'].uv_map = "ScattershotUVs"

    # Hides unused sockets
    if not only_displacement:
      for output in scatter_node.outputs:
        if output.name in texture_names.keys() or output.name == 'Random Color':
          output.hide = True
      for input in scatter_node.inputs:
        if input.name != 'UV Map':
          input.hide = True

def bake_vectors(self, context, objects):
  selected_nodes = context.selected_nodes
  nodes = selected_nodes[0].id_data.nodes
  links = selected_nodes[0].id_data.links
  scatter_nodes = [x for x in selected_nodes if get_scatter_sources([x])]
  # TODO: Check if layered scatter nodes can bake
  for scatter_node in scatter_nodes:
    coordinates_nodes = [x for x in scatter_node.node_tree.nodes if x.label == 'Scatter Coordinates']
    for coordinates in coordinates_nodes:
      # Creates a new image
      pass

      # Bakes the vectors to the image

      # Rewires the sockets

      # Hides relavent inputs

class NODE_OT_bake_scatter(bpy.types.Operator):
  bl_label = "Bake Scatter"
  bl_idname = "node.bake_scatter"
  bl_description = "Bakes the procedural result to new image textures using UV coordinates."
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

  bake_type: bpy.props.EnumProperty(
    name="Bake Type",
    description="Bake the final scatter result or just the vector coordinates",
    items=[
      ('combined', 'Result', 'Bakes the final result of the scatter to new image textures for use in other applications'),
      ('vectors', 'Vectors', 'Bakes the vector coordinates while keeping the original textures. Useful for smoothing out cell and tri-planar blending for displacement while rendering in Blender')
    ],
    default='combined'
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
    scatter_nodes = [x for x in context.selected_nodes if get_scatter_sources([x])]
    channels = []
    for scatter_node in scatter_nodes:
      for output in scatter_node.outputs:
        channels.append(output.name)

    layout = self.layout
    layout.use_property_split = True
    layout.prop(self, "objects")

    layout.separator()

    # layout.prop(self, "bake_type", expand = True)
    if self.bake_type == 'combined':
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

    if self.objects == 'texture_set':
      objects = [x for x in context.scene.objects if x.material_slots.items() and is_in_texture_set(x, active_material)]
    else:
      objects = context.selected_objects

    if self.unwrap_method != 'existing': unwrap(self, context, objects)

    if self.bake_type == 'combined':
      bake_scatter(self, context, objects)
    else:
      pass
      # bake_vectors(self, context, objects)

    for obj in context.scene.objects:
      if obj.name in selected_object_names:
        obj.select_set(True)
      else:
        obj.select_set(False)
    context.view_layer.objects.active = bpy.data.objects[active_obj_name]
    set_bake_properties(context.scene, prev_bake_properties)
    mode_toggle(context, prev_mode)

    return {'FINISHED'}

def register():
  bpy.utils.register_class(NODE_OT_bake_scatter)

def unregister():
  bpy.utils.unregister_class(NODE_OT_bake_scatter)