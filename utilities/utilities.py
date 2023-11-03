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


import os
import re
import bpy
from copy import copy
from ..defaults import texture_names, default_view_transforms, node_names, package_name

def append_node(self, nodes, node_tree_name):
  if bpy.app.version < (4, 0, 0):
    node_file = 'scatter_nodes'
  else:
    node_file = 'scatter_nodes_4-0'
  path = bpy.path.native_pathsep(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', f'assets\{node_file}.blend\\NodeTree\\'))

  node_group = nodes.new("ShaderNodeGroup")
  initial_nodetrees = set(bpy.data.node_groups)

  try:
    bpy.ops.wm.append(filename=node_tree_name, directory=path)
  except:
    self.report({'ERROR'}, 'Scattershot nodes not detected. Please download from the Blender Market and install again.')
    self.report({'ERROR'}, f'{node_tree_name} could not be appended from {path}')
    nodes.remove(node_group)

  appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
  appended_node = [x for x in appended_nodetrees if node_tree_name in x.name][0]
  node_group.node_tree = bpy.data.node_groups[appended_node.name]
  node_group.node_tree.name = node_tree_name
  return node_group

def average_location(selected_nodes):
  return [
    sum([x.location[0] for x in selected_nodes]) / len(selected_nodes),
    sum([x.location[1] for x in selected_nodes]) / len(selected_nodes)
  ]


def create_friendly_name(context, texture_name):
  preferences = context.preferences.addons[package_name].preferences
  name = texture_name
  for file_type in name_string_to_array(preferences.file_types):
    extension = '.' + file_type.lower()
    if extension in name:
      name = name.replace(extension, '')
  name_array = []
  # Preferences can only be accessed by dot notation, so iterating through each channel with bracket notation does not work
  for word in re.split('[^a-z]', name.lower()):
    if word in name_string_to_array(preferences.albedo_names):
      name_array.append('Albedo')
    elif word in name_string_to_array(preferences.ao_names):
      name_array.append('AO')
    elif word in name_string_to_array(preferences.metal_names):
      name_array.append('Metallic')
    elif word in name_string_to_array(preferences.rough_names):
      name_array.append('Roughness')
    elif word in name_string_to_array(preferences.gloss_names):
      name_array.append('Glossiness')
    elif word in name_string_to_array(preferences.spec_names):
      name_array.append('Specular')
    elif word in name_string_to_array(preferences.emit_names):
      name_array.append('Emission')
    elif word in name_string_to_array(preferences.alpha_names):
      name_array.append('Alpha')
    elif word in name_string_to_array(preferences.normal_names):
      name_array.append('Normal')
    elif word in name_string_to_array(preferences.bump_names):
      name_array.append('Bump')
    elif word in name_string_to_array(preferences.displacement_names):
      name_array.append('Displacement')
  if len(name_array):
    return name_array[-1]
  else:
    return 'Image'

def get_scatter_sources(selected_nodes):
  scatter_sources = []
  if selected_nodes:
    nodes = selected_nodes[0].id_data.nodes
    selected_group_nodes = [x for x in nodes if x.select and x.type == 'GROUP']
    for group_node in selected_group_nodes:
      for node in group_node.node_tree.nodes:
        if node.type == 'GROUP':
          if node_names['scatter_source'] in node.node_tree.name:
            scatter_sources.append(node)
          elif node_names['scatter'] in node.node_tree.name:
            for inner_node in node.node_tree.nodes:
              if inner_node.type == 'GROUP' and node_names['scatter_source'] in inner_node.node_tree.name:
                scatter_sources.append(inner_node)
  return scatter_sources


def get_groups(nodes):
    # Could be changed to use recursion
    groups = []
    for node in nodes:
        if node.bl_idname == 'ShaderNodeGroup':
            groups.append(node.node_tree)
            for sub_node in node.node_tree.nodes:
                if sub_node.bl_idname == 'ShaderNodeGroup':
                    groups.append(sub_node.node_tree)
                    for sub_sub_node in sub_node.node_tree.nodes:
                        if sub_sub_node.bl_idname == 'ShaderNodeGroup':
                            groups.append(sub_sub_node.node_tree)
                            for sub_sub_sub_node in sub_sub_node.node_tree.nodes:
                                if sub_sub_sub_node.bl_idname == 'ShaderNodeGroup':
                                    groups.append(sub_sub_sub_node.node_tree)
    return groups


def get_baked_sources(selected_nodes):
  baked_nodes = []
  if selected_nodes:
    for node in selected_nodes:
      if node.bl_idname == 'ShaderNodeGroup' and get_scatter_sources([node]) and 'TEX_IMAGE' in [x.type for x in node.node_tree.nodes]:
        baked_nodes.append(node)
  return baked_nodes


def has_scatter_uvs(selected_nodes):
  nodes = selected_nodes[0].id_data.nodes
  has_uvs = False
  if selected_nodes:
    selected_group_nodes = [x for x in nodes if x.select and x.type == 'GROUP']
    for group_node in selected_group_nodes:
      for input in group_node.inputs:
        if "UV Map" in input.name:
          has_uvs = True
          break
  return has_uvs


def is_shader(node):
  shader_types = [
    "ShaderNodeBsdfAnisotropic",
    "ShaderNodeBsdfDiffuse",
    "ShaderNodeEmission",
    "ShaderNodeBsdfGlass",
    "ShaderNodeBsdfGlossy",
    "ShaderNodeBsdfHair",
    "ShaderNodeBsdfPrincipled",
    "ShaderNodeVolumePrincipled",
    "ShaderNodeBsdfRefraction",
    "ShaderNodeSubsurfaceScattering",
    "ShaderNodeBsdfToon",
    "ShaderNodeBsdfTranslucent",
    "ShaderNodeBsdfTransparent",
    "ShaderNodeBsdfVelvet",
    "ShaderNodeVolumeAbsorption",
    "ShaderNodeVolumeScatter"
  ]
  return node.bl_idname in shader_types


def name_array_to_string(name_array):
  name_string = ''
  for name in name_array:
    name_string += name + ', '
  return name_string[:-2]


def name_string_to_array(name_string):
  return [x for x in re.split(', ', name_string)]


def mode_toggle(context, switch_to):
  prev_mode = context.mode
  switch = {
    'EDIT_MESH': bpy.ops.object.editmode_toggle,
    'SCULPT': bpy.ops.sculpt.sculptmode_toggle,
    'PAINT_VERTEX': bpy.ops.paint.vertex_paint_toggle,
    'PAINT_WEIGHT': bpy.ops.paint.weight_paint_toggle,
    'PAINT_TEXTURE': bpy.ops.paint.texture_paint_toggle
  }
  if prev_mode != 'OBJECT':
    switch[prev_mode]()
  elif switch_to != 'OBJECT':
    switch[switch_to]()
  return prev_mode


def remove_section(nodes, title):
  for node in nodes:
    if node.parent and node.parent.name == title:
      nodes.remove(node)
  nodes.remove(nodes[title])

def get_default_color_transform(user_transform):
  test_transform = 'not_a_real_transform'
  try:
      bpy.context.scene.view_settings.view_transform = test_transform
  except Exception as error_message:
      transform_list = str(error_message).replace(
          f'bpy_struct: item.attr = val: enum "{test_transform}" not found in (', '').replace("'", '')[:-1].split(',')
      for t in default_view_transforms:
        if t in transform_list:
          return t
      return user_transform


def save_image(context, image, format_properties):
  image_settings = context.scene.render.image_settings
  color_settings = context.scene.view_settings

  def get_format_properties():
    return {
      'format': image_settings.file_format,
      'color_depth': image_settings.color_depth,
      'color_mode': image_settings.color_mode,
      'quality': image_settings.quality,
      'tiff_codec': image_settings.tiff_codec,
      'transform':  color_settings.view_transform,
      'look': color_settings.look,
      'exposure': color_settings.exposure,
      'gamma': color_settings.gamma,
      'use_curve_mapping': color_settings.use_curve_mapping,
    }
  def set_format_properties(properties):
    image_settings.file_format = properties['format']
    image_settings.color_depth = properties['color_depth']
    image_settings.color_mode = properties['color_mode']
    image_settings.quality = properties['quality']
    image_settings.tiff_codec = properties['tiff_codec']
    color_settings.view_transform = properties['transform']
    color_settings.look = properties['look']
    color_settings.exposure = properties['exposure']
    color_settings.gamma = properties['gamma']
    color_settings.use_curve_mapping = properties['use_curve_mapping']

  user_format_properties = get_format_properties()
  default_properties = {
    'format': 'PNG',
    'color_depth': '16',
    'color_mode': 'RGB',
    'quality': 100,
    'tiff_codec': 'NONE',
    'transform': get_default_color_transform(user_format_properties['transform']),
    'look': 'None',
    'exposure': 0,
    'gamma': 1,
    'use_curve_mapping': False
  }
  settings = {**default_properties, **format_properties}
  print(f'Saving Texture: {image.name} - {settings}')
  set_format_properties(settings)
  image.save_render(filepath=bpy.path.abspath(image.filepath))
  set_format_properties(user_format_properties)
