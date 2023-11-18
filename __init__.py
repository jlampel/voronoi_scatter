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


bl_info = {
    "name": "Scattershot - Voronoi Image Texture Scattering",
    "author": "Jonathan Lampel",
    "version": (1, 10, 0),
    "blender": (3, 4, 0),
    "location": "Shader Editor > Node",
    "description": "Quickly distributes image textures around your model with several controls for randomization",
    "warning": "",
    "wiki_url": "https://jlampel.github.io/voronoi_scatter/",
    "category": "Node",
}

import bpy, sys
from bpy.types import AddonPreferences
from bpy.props import (StringProperty, BoolProperty)
from . import interface
from . defaults import (file_types, texture_names)
from .utilities.utilities import name_array_to_string

class scattershot_preferences(AddonPreferences):
  bl_idname = __name__

  # PBR Keywords Preferences
  file_types: StringProperty(
    name = 'Texture File Types',
    description = "File types recognized by Scattershot's PBR detection, excluding the period and separated by commas.",
    default = name_array_to_string([x[1] for x in file_types.items()])
  )
  albedo_names: StringProperty(
    name = 'Albedo',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Albedo'])
  )
  ao_names: StringProperty(
    name = 'Ambient Occlusion',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['AO'])
  )
  metal_names: StringProperty(
    name = 'Metalness',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Metalness'])
  )
  rough_names: StringProperty(
    name = 'Roughness',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Roughness'])
  )
  gloss_names: StringProperty(
    name = 'Glossiness',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Glossiness'])
  )
  spec_names: StringProperty(
    name = 'Specular',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Specular'])
  )
  emit_names: StringProperty(
    name = 'Emission',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Emission'])
  )
  alpha_names: StringProperty(
    name = 'Alpha',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Alpha'])
  )
  bump_names: StringProperty(
    name = 'Bump',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Bump'])
  )
  normal_names: StringProperty(
    name = 'Normal',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Normal'])
  )
  displacement_names: StringProperty(
    name = 'Displacement',
    description = 'Used to sort PBR texture sets into channels',
    default = name_array_to_string(texture_names['Displacement'])
  )

  # Baking Preferences
  path: bpy.props.StringProperty(
    name = 'Output Folder',
    description = 'Where the textures will be saved. Use // at the beginning to make it relative to this blend file',
    default = "//textures"
  )
  name: bpy.props.StringProperty(
    name = 'File Name',
    description = 'Supported variables: C = channel, G = node group name, L = node label, M = material name, N = node name. Do not exclude the channel or the textures will overwrite each other',
    default = "{M}_{G}_{C}"
  )
  format: bpy.props.EnumProperty(
    name = 'Texture Format',
    description = 'The file format for color textures',
    items = [
      ('JPEG', 'JPG', 'A very lossy format that has a small file size'),
      ('WEBP', 'WEBP', 'A newer lossless format aming to dethrone PNG'),
      ('TARGA', 'TGA', "A lossless format with transparency that's often used in game engines"),
      ('PNG', 'PNG', 'A good lossless format with transparency that can be opened in any program'),
      ('TIFF', 'TIFF', "An uncompressed lossless format that can be rendered quickly"),
      ('OPEN_EXR', 'EXR', 'The highest quality lossless format that comes with a large file size')
    ],
    default = 'PNG'
  )
  color_depth: bpy.props.EnumProperty(
    name = 'Texture Color Depth',
    description = 'How much color information is stored in the image',
    items = [
      ('8', '8', '8 bits per color channel per pixel'),
      ('16', '16', '16 bits per color channel per pixel')
    ],
    default = '8'
  )
  color_float: bpy.props.EnumProperty(
    name = 'Texture Color Depth',
    description = 'How much color information is stored in the image',
    items = [
      ('16', '16', '16 bits per color channel per pixel'),
      ('32', '32', '32 bits per color channel per pixel')
    ],
    default = '32'
  )
  data_format: bpy.props.EnumProperty(
    name = 'Data Format',
    description = 'The file format for data textures such as normal and displacement maps',
    items = [
      ('JPEG', 'JPG', 'A very lossy format that has a small file size'),
      ('WEBP', 'WEBP', 'A newer lossless format aming to dethrone PNG'),
      ('TARGA', 'TGA', "A lossless format with transparency that's often used in game engines"),
      ('PNG', 'PNG', 'A good lossless format with transparency that can be opened in any program'),
      ('TIFF', 'TIFF', "An uncompressed lossless format that can be rendered quickly"),
      ('OPEN_EXR', 'EXR', 'The highest quality lossless format that comes with a large file size')
    ],
    default = 'OPEN_EXR'
  )
  data_depth: bpy.props.EnumProperty(
    name = 'Data Color Depth',
    description = 'How much color information is stored in the image',
    items = [
      ('8', '8 bit', '8 bits per color channel per pixel'),
      ('16', '16 bit', '16 bits per color channel per pixel')
    ],
    default = '8'
  )
  data_float: bpy.props.EnumProperty(
    name = 'Data Color Depth',
    description = 'How much color information is stored in the image',
    items = [
      ('16', '16 bit', '16 bits per color channel per pixel'),
      ('32', '32 bit', '32 bits per color channel per pixel')
    ],
    default = '32'
  )

  # Dropdown Menu Booleans
  show_keywords_list: BoolProperty(
    name = 'PBR Keywords',
    description = 'Show / hide the PBR keyword preferences',
    default = False
  )
  show_scatter_list: BoolProperty(
    name = 'Scattering',
    description = 'Show / hide the  preferences for scattering',
    default = False
  )
  show_bake_list: BoolProperty(
    name = 'Baking',
    description = 'Show / hide the preferences for baking',
    default = False
  )

  def draw(self, context):
    layout = self.layout
    dropdown_1 = "TRIA_RIGHT" if not self.show_keywords_list else "TRIA_DOWN"

    bake = layout.box()
    bake.prop(self, "show_bake_list", emboss = False, icon = dropdown_1)
    if self.show_bake_list:
      bake_prefs = bake.column()
      bake_prefs.prop(self, 'path')
      bake_prefs.prop(self, 'name')
      color_format = bake_prefs.row(heading = 'Color Format:')
      color_format.use_property_decorate = True
      color_format.prop(self, 'format', text = '')
      if self.format == 'PNG' or self.format == 'TIFF':
        color_format.prop(self, 'color_depth', expand=True)
      if self.format == 'OPEN_EXR':
        color_format.prop(self, 'color_float', expand=True)
      data_format = bake_prefs.row(heading = 'Data Format:')
      data_format.use_property_decorate = True
      data_format.prop(self, 'data_format', text = '')
      if self.data_format == 'PNG' or self.format == 'TIFF':
        data_format.row().prop(self, 'data_depth', expand=True)
      if self.data_format == 'OPEN_EXR':
        data_format.row().prop(self, 'data_float', expand=True)

    keywords = layout.box()
    keywords.prop(self, "show_keywords_list", emboss = False, icon = dropdown_1)
    if self.show_keywords_list:
      keywords.prop(self, 'file_types')
      keywords.prop(self, 'albedo_names')
      keywords.prop(self, 'ao_names')
      keywords.prop(self, 'metal_names')
      keywords.prop(self, 'rough_names')
      keywords.prop(self, 'gloss_names')
      keywords.prop(self, 'spec_names')
      keywords.prop(self, 'emit_names')
      keywords.prop(self, 'alpha_names')
      keywords.prop(self, 'bump_names')
      keywords.prop(self, 'normal_names')
      keywords.prop(self, 'displacement_names')



def cleanse_modules():
    # Based on https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    for module_name in sorted(sys.modules.keys()):
        if module_name.startswith(__name__):
            del sys.modules[module_name]

def register():
    interface.register()
    bpy.utils.register_class(scattershot_preferences)

def unregister():
    interface.unregister()
    bpy.utils.unregister_class(scattershot_preferences)
    cleanse_modules()

if __name__ == "__main__":
    register()