import bpy
from bpy.types import (Operator)
from .utilities import append_node, average_location, mode_toggle

def check_vector_input(selected_nodes):
    has_vector = False
    for node in selected_nodes:
        for input in node.inputs:
            if input.name == 'Vector':
                has_vector = True
                break
        if has_vector: break
    return has_vector
            
def create_triplanar_node(self, context):
    nodes = context.selected_nodes[0].id_data.nodes
    links = context.selected_nodes[0].id_data.links
    textures = context.selected_nodes
    triplanar_node = append_node(nodes, 'SS - Tri-Planar Mapping')
    triplanar_node.location = [
        min([x.location[0] for x in textures]) - 250, 
        average_location(textures)[1]
    ]
    triplanar_node.width = 200
    for node in context.selected_nodes: 
        if check_vector_input([node]):
            links.new(triplanar_node.outputs['Vector'], node.inputs['Vector'])
            if node.type == 'TEX_IMAGE' and node.interpolation == 'Linear':
                self.report({'WARNING'}, 
                    'Image texture interpolation should be set to Closest or Cubic instead of Linear to avoid blending issues'
                )

class NODE_OT_triplanar_mapping(Operator):
    bl_label = "Scattershot: Tri-Planar Mapping"
    bl_idname = "node.triplanarmapping"
    bl_description = "Adds a tri-planar mapping node and connects it to the selected nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return check_vector_input(context.selected_nodes)

    def execute(self, context):
        # switching modes prevents context errors 
        prev_mode = mode_toggle(context, 'OBJECT')
        create_triplanar_node(self, context)
        mode_toggle(context, prev_mode)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(NODE_OT_triplanar_mapping)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_triplanar_mapping)