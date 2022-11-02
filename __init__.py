# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Scattershot - Voronoi Image Texture Scattering",
    "author": "Jonathan Lampel",
    "version": (1, 7),
    "blender": (3, 3, 0),
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
from . utilities import name_array_to_string

class scattershot_preferences(AddonPreferences):
  bl_idname = __name__

  file_types: StringProperty(
    name = 'Texture File Types',
    description = 'File types recognized by Scattershot, excluding the period and separated by commas.',
    default = name_array_to_string(file_types)
  )

  texture_path: StringProperty(
    name = 'Texture Path',
    description = 'Folder to automatically save image textures to after baking the scatter result.',
    default = "./textures"
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

  show_keywords_list: BoolProperty(
    name = 'PBR Keywords',
    description = 'Show / hide the PBR keyword preferences',
    default = True
  )

  def draw(self, context):
    layout = self.layout
    row = layout.row()
    col = row.column()
    col.prop(self, 'file_types')
    dropdown_1 = "TRIA_RIGHT" if not self.show_keywords_list else "TRIA_DOWN"
    box = layout.box()
    box.prop(self, "show_keywords_list", emboss = False, icon = dropdown_1)
    if self.show_keywords_list:
      box.prop(self, 'albedo_names')
      box.prop(self, 'ao_names')
      box.prop(self, 'metal_names')
      box.prop(self, 'rough_names')
      box.prop(self, 'gloss_names')
      box.prop(self, 'spec_names')
      box.prop(self, 'emit_names')
      box.prop(self, 'alpha_names')
      box.prop(self, 'bump_names')
      box.prop(self, 'normal_names')
      box.prop(self, 'displacement_names')

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