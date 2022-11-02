import bpy

from . import voronoi_scattering, unscatter, noise_blending, randomize_color, triplanar_mapping, label_socket, baking

class NODE_MT_scattershot(bpy.types.Menu):
    bl_label = 'Scattershot'
    bl_idname = 'NODE_MT_scattershot_menu'

    def draw(self, context):
        self.layout.operator(voronoi_scattering.NODE_OT_scatter.bl_idname)
        self.layout.operator(baking.NODE_OT_bake_scatter.bl_idname)
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
    baking.register()
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
    baking.unregister()
    bpy.utils.unregister_class(NODE_MT_scattershot)
    bpy.types.NODE_MT_context_menu.remove(draw_context_menu)
    bpy.types.NODE_MT_node.remove(draw_node_menu)