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
    "version": (1, 3),
    "blender": (2, 93, 0),
    "location": "Shader Editor > Node",
    "description": "Quickly distributes image textures around your model with several controls for randomization",
    "warning": "",
    "wiki_url": "",
    "category": "Node",
}

import bpy
from . import voronoi_scattering, unscatter, noise_blending, randomize_color, triplanar_mapping, label_socket

def draw_context_menu(self, context):
    if context.area.ui_type == 'ShaderNodeTree' and context.space_data.shader_type != 'LINESTYLE':
        self.layout.separator()
        self.layout.operator(voronoi_scattering.NODE_OT_scatter.bl_idname)
        self.layout.operator(unscatter.NODE_OT_unscatter.bl_idname)
        self.layout.operator(noise_blending.NODE_OT_noise_blend.bl_idname)
        self.layout.operator(randomize_color.NODE_OT_randomize_col.bl_idname)
        self.layout.operator(triplanar_mapping.NODE_OT_triplanar_mapping.bl_idname)

def draw_node_menu(self, context):
    if context.area.ui_type == 'ShaderNodeTree'and context.space_data.shader_type != 'LINESTYLE':
        self.layout.operator(voronoi_scattering.NODE_OT_scatter.bl_idname)
        self.layout.operator(unscatter.NODE_OT_unscatter.bl_idname)
        self.layout.operator(noise_blending.NODE_OT_noise_blend.bl_idname)
        self.layout.operator(randomize_color.NODE_OT_randomize_col.bl_idname)
        self.layout.operator(triplanar_mapping.NODE_OT_triplanar_mapping.bl_idname)
        self.layout.separator()

def register():
    label_socket.register()
    voronoi_scattering.register()
    unscatter.register()
    noise_blending.register()
    randomize_color.register()
    triplanar_mapping.register()
    bpy.types.NODE_MT_context_menu.append(draw_context_menu)
    bpy.types.NODE_MT_node.prepend(draw_node_menu)

def unregister():
    label_socket.unregister()
    voronoi_scattering.unregister()
    unscatter.unregister()
    noise_blending.unregister()
    randomize_color.unregister()
    triplanar_mapping.unregister()
    bpy.types.NODE_MT_context_menu.remove(draw_context_menu)
    bpy.types.NODE_MT_node.remove(draw_node_menu)

if __name__ == "__main__":
    register()