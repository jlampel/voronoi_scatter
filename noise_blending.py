import bpy
import os
from bpy.types import (Operator)
from . import unscatter

def noise_blend(context, nodes_to_mix, sockets_to_mix, should_combine_scatters):
    nodes = nodes_to_mix[0].id_data.nodes
    links = nodes_to_mix[0].id_data.links
    textures = nodes_to_mix

    def order_nodes():
        textures_sorted = sorted(textures, key=lambda x: -x.location[1])
        return textures_sorted
        
    def get_outputs():
        input_names = []
        mix_channels = []
        for i in range(len(textures)):
            for output in textures[i].outputs:
                if (output.name not in input_names) and (output.enabled == True):
                    input_names.append(output.name)
                    mix_channels.append(output)
        return mix_channels

    def create_group():
        # Add a node group
        blending_node = nodes.new("ShaderNodeGroup")
        blending_node.node_tree = bpy.data.node_groups.new("Noise Blend", "ShaderNodeTree")
        blending_node.location = [
            max([tex.location[0] for tex in textures]) + max([tex.width for tex in textures]) + 250, 
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
        vector_mix.inputs[0].default_value = 0
        blur_range = blending_nodes.new("ShaderNodeMapRange")
        blur_range.interpolation_type = "SMOOTHERSTEP"
        blur_range.inputs['To Max'].default_value = 0.05
        blur_range.location = [-800, -150]
        blending_links.new(blur_range.outputs[0], vector_mix.inputs[0])
        blending_links.new(group_input.outputs[0], vector_mix.inputs[1])
        blending_links.new(white_noise.outputs["Color"], vector_mix.inputs[2])
        noise = blending_nodes.new('ShaderNodeTexNoise')
        noise.location = [-400, 0]
        noise.noise_dimensions = '2D'
        noise.inputs['Roughness'].default_value = 0.75
        noise.inputs['Detail'].default_value = 5
        blending_links.new(vector_mix.outputs["Color"], noise.inputs["Vector"])
        blending_links.new(group_input.outputs[-1], noise.inputs["Scale"])
        blending_inputs["Scale"].name = "Noise Scale"
        blending_links.new(group_input.outputs[-1], noise.inputs["Detail"])
        blending_inputs["Detail"].name = "Noise Detail"
        blending_links.new(group_input.outputs[-1], noise.inputs["Roughness"])
        blending_inputs["Roughness"].name = "Noise Roughness"
        # blending_links.new(group_input.outputs[-1], noise.inputs["Distortion"])
        # blending_inputs["Distortion"].name = "Noise Distortion"
        blur_socket = blending_node.node_tree.inputs.new("NodeSocketFloatFactor", "Noise Blur")
        blur_socket.min_value = 0
        blur_socket.max_value = 1
        blending_links.new(group_input.outputs["Noise Blur"], blur_range.inputs[0])
        separate_hsv = blending_nodes.new("ShaderNodeSeparateHSV")
        separate_hsv.location = [-200, 0]
        blending_links.new(noise.outputs["Color"], separate_hsv.inputs["Color"])
        group_output = blending_nodes.new("NodeGroupOutput")
        group_output.location = [1000, 0]
        return blending_node
        
    def create_inputs(blending_node, mix_channels):
        mix_inputs = []
        for t in range(len(textures)):
            tex = textures[t]
            enabled_sockets = [x.name for x in tex.outputs if x.enabled]
            for output in mix_channels:
                tex_input = blending_node.node_tree.inputs.new("NodeSocketColor", output.name + str(t + 1))
                mix_inputs.append(tex_input)
                if output.name in enabled_sockets:
                    links.new(tex.outputs[output.name], blending_node.inputs[tex_input.name])
        return mix_inputs
    
    def create_outputs(blending_node, mix_channels):
        for output in mix_channels:
            node_output = blending_node.node_tree.outputs.new("NodeSocketColor", output.name)

    def mix_colors(blending_node, mix_channels, mix_inputs):
        blending_nodes = blending_node.node_tree.nodes
        blending_links = blending_node.node_tree.links
        for i in range(len(mix_channels)):
            mix_nodes = []
            for t in range(len(textures)):
                input_number = (t * len(mix_channels)) + i
                next_number = ((t + 1) * len(mix_channels)) + i
                if t < len(textures) - 1:
                    greater = blending_nodes.new("ShaderNodeMath")
                    greater.location = [t * 200, 175 + (i * -500) ]
                    greater.operation = 'GREATER_THAN'
                    greater.inputs[1].default_value = (1 / len(textures)) * (t + 1)
                    mix = blending_nodes.new("ShaderNodeMixRGB")
                    mix_nodes.append(mix)
                    mix.location = [t * 200, i * -500]
                    blending_links.new(blending_nodes['Separate HSV'].outputs[0], greater.inputs[0])
                    blending_links.new(greater.outputs[0], mix.inputs[0])
                if t == 0:
                    blending_links.new(blending_nodes['Group Input'].outputs[mix_inputs[input_number].name], mix.inputs[1])
                    blending_links.new(blending_nodes['Group Input'].outputs[mix_inputs[next_number].name], mix.inputs[2])
                if t > 0 and t < len(textures) - 1:
                    blending_links.new(mix_nodes[t - 1].outputs[0], mix_nodes[t].inputs[1])
                    blending_links.new(blending_nodes['Group Input'].outputs[mix_inputs[next_number].name], mix.inputs[2])
            blending_links.new(mix_nodes[-1].outputs[0], blending_nodes['Group Output'].inputs[i])

    def create_coordinates(blending_node, textures):
        has_coordinates = False
        for tex in textures:
            socket_names = [x.name for x in tex.inputs]
            if 'Vector' in socket_names and tex.inputs['Vector'].links:
                from_socket = tex.inputs['Vector'].links[0].from_socket
                links.new(from_socket, blending_node.inputs['Vector'])
                has_coordinates = True
                break
        if not has_coordinates:
            coordinates = nodes.new("ShaderNodeTexCoord")
            coordinates.location = [blending_node.location[0] - 200, blending_node.location[1]]
            links.new(coordinates.outputs['UV'], blending_node.inputs['Vector'])

    def combine_scatter_nodes(context):
        if should_combine_scatters and unscatter.has_scatter_nodes: 
            scatter_nodes = unscatter.has_scatter_nodes(context.selected_nodes)
            master_node = scatter_nodes[0]
            for scatter_node in scatter_nodes:
                scatter_sources = [x for x in scatter_node.node_tree.nodes if x.type == 'GROUP' and 'SS - Scatter Source' in x.node_tree.name]
                if scatter_node != master_node:
                    for source in scatter_sources:
                        new_source = master_node.node_tree.nodes.new('ShaderNodeGroup')
                        new_source.node_tree = source.node_tree
            # for all other scatter nodes, add their scatter sources to the master node's nodetree
            # connect all the scatter sources
            # perform a noise blend on the scatter sources 

    textures = order_nodes()
    mix_channels = get_outputs()
    blending_node = create_group()
    mix_inputs = create_inputs(blending_node, mix_channels)
    create_outputs(blending_node, mix_channels)
    mix_colors(blending_node, mix_channels, mix_inputs)
    create_coordinates(blending_node, textures)
    combine_scatter_nodes(context)

class NODE_OT_noise_blend(Operator):
    bl_label = "Noise Blend"
    bl_idname = "node.noise_blend"
    bl_description = "Blends any number of images based on a procedural noise"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    sockets_to_mix: bpy.props.EnumProperty(
        name = "Mix Outputs",
        description = "Which node outputs get mixed together by the noise",
        items = [
            ("order", "By Order", "Mix outputs together by their socket number"),
            ("name", "By Name", "Mix outputs together based on their name"),
            ("first", "Only First", "Only mix the first outputs together")
        ],
        default = "name"
    )

    should_combine_scatters: bpy.props.BoolProperty(
        name = "Combine Scatter Nodes",
        description = "Groups scatter nodes together so that all textures can be controlled by one node. This is slightly faster because it only uses one voronoi texture for all of them",
        default = True
    )

    @classmethod
    def poll(cls, context):
        if len(context.selected_nodes) > 1:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.prop(self, "sockets_to_mix")
        layout.prop(self, "should_combine_scatters")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        noise_blend(context, selected_nodes, self.sockets_to_mix, self.should_combine_scatters)
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