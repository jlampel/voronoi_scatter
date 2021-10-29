import bpy
from bpy.types import (Operator)
from .utilities import append_node, mode_toggle

def connect_vector(links, nodes, from_node, to_node):
    has_coordinates = False
    for input in from_node.inputs:
        if input.name == 'Vector' and input.links:
            links.new(input.links[0].from_socket, to_node.inputs['Vector'])
            has_coordinates == True
            break
    if not has_coordinates: 
        coordinates = nodes.new("ShaderNodeTexCoord")
        coordinates.location = [to_node.location[0] - 175, to_node.location[1] - from_node.height - 200]
        links.new(coordinates.outputs['Object'], to_node.inputs['Vector'])

def create_randomize_node(context):
    nodes = context.selected_nodes[0].id_data.nodes
    links = context.selected_nodes[0].id_data.links
    for node in context.selected_nodes:
        randomize_node = append_node(nodes, 'SS - Noise Randomize HSV')
        randomize_node.width = 200
        randomize_node.location = [node.location[0] + node.width + 50, node.location[1]] 
        if node.outputs[0].links:
            for link in node.outputs[0].links:
                links.new(randomize_node.outputs[0], node.outputs[0].links[0].to_socket)
        links.new(node.outputs[0], randomize_node.inputs[0])
        connect_vector(links, nodes, node, randomize_node)


class NODE_OT_randomize_col(Operator):
    bl_label = "Scattershot: HSV Noise"
    bl_idname = "node.randomizecol"
    bl_description = "Randomizes the output of a node using a noise texture"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_nodes

    def execute(self, context):
        # switching modes prevents context errors 
        prev_mode = mode_toggle(context, 'OBJECT')
        create_randomize_node(context)
        mode_toggle(context, prev_mode)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(NODE_OT_randomize_col)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_randomize_col)