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


import bpy

from . import voronoi_scattering, unscatter, noise_blending, randomize_color, triplanar_mapping, label_socket, bake, clear_bake, denoise_image

class NODE_MT_scattershot(bpy.types.Menu):
    bl_label = 'Scattershot'
    bl_idname = 'NODE_MT_scattershot_menu'

    def draw(self, context):
        self.layout.operator(voronoi_scattering.NODE_OT_scatter.bl_idname)
        self.layout.operator(bake.NODE_OT_bake_scatter.bl_idname)
        self.layout.operator(clear_bake.NODE_OT_clear_baked_scatter.bl_idname)
        self.layout.operator(unscatter.NODE_OT_unscatter.bl_idname)
        self.layout.operator(noise_blending.NODE_OT_noise_blend.bl_idname)
        self.layout.operator(randomize_color.NODE_OT_randomize_col.bl_idname)
        self.layout.operator(triplanar_mapping.NODE_OT_triplanar_mapping.bl_idname)

def draw_context_menu(self, context):
    if context.area.ui_type == 'ShaderNodeTree' and context.space_data.shader_type != 'LINESTYLE':
        self.layout.separator()
        self.layout.menu(NODE_MT_scattershot.bl_idname)

def draw_node_menu(self, context):
    if context.area.ui_type == 'ShaderNodeTree'and context.space_data.shader_type != 'LINESTYLE':
        self.layout.menu(NODE_MT_scattershot.bl_idname)
        self.layout.separator()

def register():
    label_socket.register()
    voronoi_scattering.register()
    unscatter.register()
    noise_blending.register()
    randomize_color.register()
    triplanar_mapping.register()
    bake.register()
    clear_bake.register()
    denoise_image.register()
    bpy.utils.register_class(NODE_MT_scattershot)
    bpy.types.NODE_MT_context_menu.append(draw_context_menu)
    bpy.types.NODE_MT_node.prepend(draw_node_menu)

def unregister():
    label_socket.unregister()
    voronoi_scattering.unregister()
    unscatter.unregister()
    noise_blending.unregister()
    randomize_color.unregister()
    triplanar_mapping.unregister()
    bake.unregister()
    clear_bake.unregister()
    denoise_image.unregister()
    bpy.utils.unregister_class(NODE_MT_scattershot)
    bpy.types.NODE_MT_context_menu.remove(draw_context_menu)
    bpy.types.NODE_MT_node.remove(draw_node_menu)