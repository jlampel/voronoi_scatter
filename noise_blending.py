import bpy
import os
from bpy.types import (Operator)
from operator import attrgetter

def noise_blend(nodes_to_mix):
    nodes = nodes_to_mix[0].id_data.nodes
    links = nodes_to_mix[0].id_data.links
    textures = nodes_to_mix

    def order_nodes():
        textures_sorted = sorted(textures, key=lambda x: -x.location[1])
        return textures_sorted
        
    def get_outputs():
        input_names = []
        mix_inputs = []
        for i in range(len(textures)):
            for output in textures[i].outputs:
                if output.name not in input_names:
                    input_names.append(output.name)
                    mix_inputs.append(output)
        return mix_inputs

    def create_group():
        # Add a node group
        blending_node = nodes.new("ShaderNodeGroup")
        blending_node.node_tree = bpy.data.node_groups.new("Noise Blend", "ShaderNodeTree")
        blending_node.location = [
            max([tex.location[0] for tex in textures]) + 400, 
            sum([x.location[1] for x in textures]) / len(textures)
        ]
        blending_node.width = 200
        blending_nodes = blending_node.node_tree.nodes
        blending_links = blending_node.node_tree.links
        blending_inputs = blending_node.node_tree.inputs
        # Add noise and initial nodes
        group_input = blending_nodes.new("NodeGroupInput")
        group_input.location = [-1000, 0]
        white_noise = blending_nodes.new("ShaderNodeTexWhiteNoise")
        white_noise.location = [-800, 0]
        white_noise.noise_dimensions = '2D'
        blending_links.new(group_input.outputs[-1], white_noise.inputs[0])
        blending_inputs["Vector"].hide_value = True
        vector_mix = blending_nodes.new("ShaderNodeMixRGB")
        vector_mix.location = [-600, 0]
        vector_mix.blend_type = 'LINEAR_LIGHT'
        blending_links.new(group_input.outputs[-1], vector_mix.inputs[0])
        blending_inputs["Fac"].name = "Noise Blur"
        blending_links.new(group_input.outputs[0], vector_mix.inputs[1])
        blending_links.new(white_noise.outputs["Color"], vector_mix.inputs[2])
        noise = blending_nodes.new('ShaderNodeTexNoise')
        noise.location = [-400, 0]
        noise.noise_dimensions = '2D'
        noise.inputs['Roughness'].default_value = 1
        blending_links.new(vector_mix.outputs["Color"], noise.inputs["Vector"])
        blending_links.new(group_input.outputs[-1], noise.inputs["Scale"])
        blending_inputs["Scale"].name = "Noise Scale"
        blending_links.new(group_input.outputs[-1], noise.inputs["Detail"])
        blending_inputs["Detail"].name = "Noise Detail"
        blending_links.new(group_input.outputs[-1], noise.inputs["Roughness"])
        blending_inputs["Roughness"].name = "Noise Roughness"
        blending_links.new(group_input.outputs[-1], noise.inputs["Distortion"])
        blending_inputs["Distortion"].name = "Noise Distortion"
        separate_hsv = blending_nodes.new("ShaderNodeSeparateHSV")
        separate_hsv.location = [-200, 0]
        blending_links.new(noise.outputs["Color"], separate_hsv.inputs["Color"])
        group_output = blending_nodes.new("NodeGroupOutput")
        group_output.location = [1000, 0]
        return blending_node
        
    def create_inputs(blending_node, mix_inputs):
        for i in range(len(textures)):
            tex = textures[i]
            for output in mix_inputs:
                tex_input = blending_node.node_tree.inputs.new("NodeSocketColor", output.name + str(i + 1))
                links.new(tex.outputs[output.name], blending_node.inputs[tex_input.name])
    
    def create_outputs(blending_node, mix_inputs):
        for i in range(len(mix_inputs)):
            node_output = blending_node.node_tree.outputs.new("NodeSocket")

    # Mix all inputs together 

    # Create outputs

    textures = order_nodes()
    mix_inputs = get_outputs()
    blending_node = create_group()
    create_inputs(blending_node, mix_inputs)

class NODE_OT_noise_blend(Operator):
    bl_label = "Noise Blend"
    bl_idname = "node.noise_blend"
    bl_description = "Blends any number of images based on a procedural noise"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    sockets: bpy.props.EnumProperty(
        name = "Mix Outputs",
        description = "Which node outputs get mixed together by the noise",
        items = [
            ("order", "By Order", "Mix outputs together by their socket number"),
            ("name", "By Name", "Mix outputs together based on their name"),
            ("first", "Only First", "Only mix the first outputs together")
        ],
        default = "order"
    )

    @classmethod
    def poll(cls, context):
        if len(context.selected_nodes) > 1:
            return True
        else:
            return False

    def execute(self, context):
        selected_nodes = context.selected_nodes
        noise_blend(selected_nodes)
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(NODE_OT_noise_blend.bl_idname)

def register():
    bpy.utils.register_class(NODE_OT_noise_blend)
    bpy.types.NODE_MT_node.append(draw_menu)
    bpy.types.NODE_MT_context_menu.append(draw_menu)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_noise_blend)
    bpy.types.NODE_MT_node.remove(draw_menu)
    bpy.types.NODE_MT_context_menu.remove(draw_menu)