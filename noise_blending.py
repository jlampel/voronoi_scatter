import bpy
from bpy.types import (Operator)
from pprint import pprint
from .utilities import mode_toggle
from . import defaults


def noise_blend(self, nodes_to_mix, sockets_to_mix, mix_by):
    nodes = nodes_to_mix[0].id_data.nodes
    links = nodes_to_mix[0].id_data.links
    textures = nodes_to_mix

    def order_nodes():
        textures_sorted = sorted(textures, key=lambda x: -x.location[1])
        return textures_sorted

    def get_sockets():
        if mix_by == "name":
            mix_sockets = {}
            for texture_idx, texture in enumerate(textures):
                enabled_sockets = [x for x in texture.outputs if x.enabled]
                for output_idx, output in enumerate(enabled_sockets):
                    if not mix_sockets.get(output.name):
                        mix_sockets[output.name] = []
                    mix_sockets[output.name].append(output)
            return mix_sockets
        elif mix_by == "common_name":
            mix_sockets = {}
            for texture_idx, texture in enumerate(textures):
                enabled_sockets = [x for x in texture.outputs if x.enabled]
                for output_idx, output in enumerate(enabled_sockets):
                    matches_all = True
                    for tex in textures:
                        if output.name not in tex.outputs:
                            matches_all = False
                    if matches_all:
                        if not mix_sockets.get(output.name):
                            mix_sockets[output.name] = []
                        mix_sockets[output.name].append(output)
            return mix_sockets
                    
        elif mix_by == "order":
            mix_sockets = {}
            for texture_idx, texture in enumerate(textures):
                enabled_sockets = [x for x in textures[texture_idx].outputs if x.enabled]
                for output_idx, output in enumerate(enabled_sockets):
                    channel_name = "Col" + str(output_idx) + " Tex"
                    if channel_name not in mix_sockets:
                        mix_sockets[channel_name] = []
                    mix_sockets[channel_name].append(output)
            return mix_sockets
        elif mix_by == "first":
            mix_sockets = {"Color": []}
            for texture_idx, texture in enumerate(textures):
                enabled_sockets = [x for x in texture.outputs if x.enabled]
                mix_sockets["Color"].append(enabled_sockets[0])
            return mix_sockets
        elif mix_by == "custom":
            return sockets_to_mix
        else:
            self.report({'ERROR'}, "Mixing method not recognized")

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
        if mix_by == 'custom': noise.noise_dimensions = '2D'
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
        blur_socket = blending_node.node_tree.inputs.new("NodeSocketFloatFactor", "Noise Blending")
        blur_socket.min_value = 0
        blur_socket.max_value = 1
        blending_links.new(group_input.outputs["Noise Blending"], blur_range.inputs[0])
        separate_hsv = blending_nodes.new("ShaderNodeSeparateHSV")
        separate_hsv.location = [-200, 0]
        blending_links.new(noise.outputs["Color"], separate_hsv.inputs["Color"])
        group_output = blending_nodes.new("NodeGroupOutput")
        group_output.location = [1000, 0]
        return blending_node
        
    def create_inputs(blending_node, sockets):
        mix_inputs = {}
        max_sockets = max([len(sockets[x]) for x in sockets.keys()])
        for channel in sockets.keys():
            mix_inputs[channel] = []
        for socket_idx in range(max_sockets):
            for channel in sockets.keys():
                new_input = blending_node.node_tree.inputs.new("NodeSocketColor", channel + str(socket_idx + 1))
                mix_inputs[channel].append(new_input)
        return mix_inputs
    
    def link_inputs(textures, blending_node, sockets, mix_inputs):
        for channel_name in sockets:
            for idx, from_socket in enumerate(sockets[channel_name]):
                to_socket = blending_node.inputs[mix_inputs[channel_name][idx].name]
                links.new(from_socket, to_socket)

    def create_outputs(blending_node, sockets):
        for channel in sockets.keys():
            node_output = blending_node.node_tree.outputs.new("NodeSocketColor", channel)

    def mix_colors(blending_node, mix_inputs, sockets):
        blending_nodes = blending_node.node_tree.nodes
        blending_links = blending_node.node_tree.links
        channels = [x for x in mix_inputs.keys()]
        for channel_idx, channel_name in enumerate(channels):
            channel = mix_inputs[channel_name]
            mix_nodes = []
            number_of_sockets = len(sockets[channel_name])
            if number_of_sockets == 1: 
                self.report({"WARNING"}, "Skipping noise blending for %s - more than one texture is needed per PBR channel" % channel_name)
                blending_links.new(blending_nodes['Group Input'].outputs[channel[0].name], blending_nodes['Group Output'].inputs[channel_name])
            else:
                for socket_idx, socket in enumerate(channel):
                    if socket_idx < len(channel) - 1:
                        greater = blending_nodes.new("ShaderNodeMath")
                        greater.location = [socket_idx * 200, 175 + (channel_idx * -500) ]
                        greater.operation = 'GREATER_THAN'
                        greater.inputs[1].default_value = (1 / number_of_sockets) * (socket_idx + 1)
                        mix = blending_nodes.new("ShaderNodeMixRGB")
                        mix_nodes.append(mix)
                        mix.location = [socket_idx * 200, channel_idx * -500]
                        blending_links.new(blending_nodes['Separate HSV'].outputs[0], greater.inputs[0])
                        blending_links.new(greater.outputs[0], mix.inputs[0])
                    if socket_idx == 0:
                        next_socket = channel[socket_idx + 1]
                        blending_links.new(blending_nodes['Group Input'].outputs[socket.name], mix.inputs[1])
                        blending_links.new(blending_nodes['Group Input'].outputs[next_socket.name], mix.inputs[2])
                    elif socket_idx > 0 and socket_idx < number_of_sockets - 1:
                        next_socket = channel[socket_idx + 1]
                        blending_links.new(mix_nodes[socket_idx - 1].outputs[0], mix_nodes[socket_idx].inputs[1])
                        blending_links.new(blending_nodes['Group Input'].outputs[next_socket.name], mix.inputs[2])
                blending_links.new(mix_nodes[-1].outputs[0], blending_nodes['Group Output'].inputs[channel_idx])

    def create_coordinates(blending_node, textures):
        has_coordinates = False
        for tex in textures:
            socket_names = [x.name for x in tex.inputs]
            if 'Vector' in socket_names and tex.inputs['Vector'].links:
                from_socket = tex.inputs['Vector'].links[0].from_socket
                from_node = from_socket.node
                if from_node.label == 'Scatter Mapping':
                    if from_node.inputs['Vector'].links:
                        links.new(from_node.inputs['Vector'].links[0].from_socket, blending_node.inputs['Vector'])
                        has_coordinates = True
                else:
                    links.new(from_socket, blending_node.inputs['Vector'])
                    has_coordinates = True
                break
        if not has_coordinates:
            coordinates = nodes.new("ShaderNodeTexCoord")
            coordinates.location = [blending_node.location[0] - 200, blending_node.location[1]]
            links.new(coordinates.outputs['UV'], blending_node.inputs['Vector'])

    textures = order_nodes()
    sockets = get_sockets()
    if sockets: 
        blending_node = create_group()
        mix_inputs = create_inputs(blending_node, sockets)
        link_inputs(textures, blending_node, sockets, mix_inputs)
        create_outputs(blending_node, sockets)
        mix_colors(blending_node, mix_inputs, sockets)
        create_coordinates(blending_node, textures)
        return blending_node
    else:
        self.report({'ERROR'}, 'No matching output sockets found')


class NODE_OT_noise_blend(Operator):
    bl_label = "Scattershot: Noise Mix"
    bl_idname = "node.noise_blend"
    bl_description = "Blends any number of selected nodes based on a procedural noise"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    mix_by: bpy.props.EnumProperty(
        name = "Mix Outputs By",
        description = "Which node outputs get mixed together by the noise",
        items = [
            ("order", "Order", "Mix outputs together by their socket number"),
            ("name", "All Names", "Mix outputs together based on their name and create a blank input if the node doesn't have an output of that name"),
            ("common_name", "Only Common Names", "Mix outputs together based on their name if all nodes have an output of that name"),
            ("first", "Only First", "Only mix the first outputs together"),
            # can also be "custom", but that should only be used programatically
        ],
        default = defaults.noise_blend['mix_by']
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
        layout.prop(self, "mix_by")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # switching modes prevents context errors 
        prev_mode = mode_toggle(context, 'OBJECT')
        noise_blend(self, context.selected_nodes, None, self.mix_by)
        mode_toggle(context, prev_mode)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NODE_OT_noise_blend)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_noise_blend)