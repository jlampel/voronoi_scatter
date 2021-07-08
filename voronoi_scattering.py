import bpy
from random import random
from pprint import pprint
from bpy.types import (Object, Operator)
from bpy.props import (BoolProperty, EnumProperty)
from . import defaults
from . import noise_blending
noise_blend = noise_blending.noise_blend
from . import utilities
append_node = utilities.append_node
create_friendly_name = utilities.create_friendly_name
create_sortable_name = utilities.create_sortable_name
average_location = utilities.average_location
   
def create_coordinates_node(self, selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    links = selected_nodes[0].id_data.links
    textures = [x for x in selected_nodes if x.type == 'TEX_IMAGE']
    scatter_node = append_node(nodes, 'SS - Scatter Mapping')
    scatter_node.label = "Scatter Mapping"
    scatter_node.width = 250
    scatter_node.location = [
        min([tex.location[0] for tex in textures]) - 350, 
        sum([x.location[1] for x in textures]) / len(textures) + 100
    ]
    for texture in textures:
        links.new(scatter_node.outputs[0], texture.inputs['Vector'])
        texture.interpolation = self.texture_interpolation
    texture_coordinates = nodes.new("ShaderNodeTexCoord")
    if self.projection_method == 'uv':
        texture_coordinates.location = [scatter_node.location[0] - 250, scatter_node.location[1] - 235]
        links.new(texture_coordinates.outputs['UV'], scatter_node.inputs['Vector'])
    else:
        tri_planar = append_node(nodes, 'SS - Tri-Planar Mapping')
        tri_planar.label = "Tri-Planar Mapping"
        tri_planar.width = 150
        tri_planar.location = [scatter_node.location[0] - 200, scatter_node.location[1] - 345]
        texture_coordinates.location = [scatter_node.location[0] - 400, scatter_node.location[1] - 235]
        links.new(texture_coordinates.outputs['Object'], tri_planar.inputs['Vector'])
        links.new(tri_planar.outputs['Vector'], scatter_node.inputs['Vector'])
    return scatter_node

def sort_textures(self, selected_nodes):
    if self.layering == 'overlapping':
        if len(selected_nodes) > 4:
            self.report({'WARNING'}, 'Each texture must be computed 9 times for the overlapping method. Compilation may be slow. Try simple layering for faster renders')
    textures = [x for x in selected_nodes if x.type == 'TEX_IMAGE']
    sorted_textures = {
        'Image': [],
        'Albedo': [], 
        'AO': [], 
        'Metallic': [], 
        'Specular': [], 
        'Roughness': [], 
        'Glossiness': [], 
        'Emission': [], 
        'Alpha': [], 
        'Normal': [],
        'Bump': [],
    }
    for texture in textures:
        is_map = False
        if self.use_pbr:
            map_type = create_friendly_name(texture.image.name)
            if map_type in sorted_textures.keys():
                sorted_textures[map_type].append(texture)
                is_map = True
        if not is_map:
            sorted_textures['Image'].append(texture)
    filtered_textures = {}
    for map_type in sorted_textures:
        if sorted_textures[map_type] != []:
            filtered_textures[map_type] = sorted_textures[map_type]
    if filtered_textures.get('Normal'):
        self.report({'WARNING'}, 
            'Rotating a normal map is not advised. The light will bounce in the wrong direction.'+ 
            'Try using a bump map if rotation is needed'
        )
    return filtered_textures

def append_scatter_node(self, selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    if self.layering == 'overlapping': 
        scatter_node = append_node(nodes, 'SS - Scatter Overlapping')
        scatter_node.label = "Scatter Overlapping"
    else:
        scatter_node = append_node(nodes, 'SS - Scatter Fast')
        scatter_node.label = "Scatter Fast"
    scatter_node.width = 250
    scatter_node.location = average_location(selected_nodes)
    return scatter_node

def create_scatter_coordinates(scatter_node):
    scatter_coordinates_groups = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Coordinates"]
    new_scatter_coordinates = scatter_coordinates_groups[0].node_tree.copy()
    # manage any layering options here
    for x in scatter_coordinates_groups:
        x.node_tree = new_scatter_coordinates
    return new_scatter_coordinates

def create_scatter_sources(self, scatter_node, sorted_textures, transparency):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links

    def add_scatter_source(idx, channel_idx=0, channel_len=0):
        scatter_source = nodes.new("ShaderNodeGroup")
        scatter_source.node_tree = bpy.data.node_groups['SS - Scatter Source Empty'].copy()
        scatter_source.node_tree.name = "SS - Scatter Source"
        scatter_source.name = "Scatter Source"
        scatter_source.location = [-650, - (225 * idx) - (250 * channel_idx * channel_len)]
        return scatter_source

    def setup_image_nodes(scatter_source, channel, image_nodes):
        scatter_source_nodes = scatter_source.node_tree.nodes
        scatter_source_links = scatter_source.node_tree.links
        new_image_nodes = [scatter_source_nodes.new("ShaderNodeTexImage") for x in image_nodes]
        multiply_nodes = []
        greater_nodes = []
        col_mix_nodes = []
        alpha_mix_nodes = []
        # populate nodes in scatter source
        for image_node_idx, image_node in enumerate(new_image_nodes):
            image_node.image = image_nodes[image_node_idx].image
            image_node.interpolation = self.texture_interpolation
            image_node.projection = 'FLAT'
            if transparency:
                image_node.extension = 'CLIP'
            else:
                image_node.extension = 'REPEAT'
            noncolor_channels = ['Normal', 'Bump']
            if self.use_pbr and channel in noncolor_channels:
                image_node.image.colorspace_settings.name = 'Non-Color'
            else:
                image_node.image.colorspace_settings.name = image_nodes[image_node_idx].image.colorspace_settings.name
            image_node.location = [image_node_idx * 250, -image_node_idx * 250]
            if image_node_idx > 0:
                multiply = scatter_source_nodes.new("ShaderNodeMath")
                multiply.operation = 'MULTIPLY'
                multiply.location = [(image_node_idx * 250) + 350, (-image_node_idx * 250) + 600]
                multiply_nodes.append(multiply)
                greater = scatter_source_nodes.new("ShaderNodeMath")
                greater.operation = 'GREATER_THAN'
                greater.location = [(image_node_idx * 250) + 350, (-image_node_idx * 250) + 425]
                greater_nodes.append(greater)
                col_mix = scatter_source_nodes.new("ShaderNodeMixRGB")
                col_mix.location = [(image_node_idx * 250) + 350, (-image_node_idx * 250) + 250]
                col_mix.hide = True
                col_mix_nodes.append(col_mix)
                alpha_mix = scatter_source_nodes.new("ShaderNodeMixRGB")
                alpha_mix.location = [(image_node_idx * 250) + 350, (-image_node_idx * 250) + 200]
                alpha_mix.hide = True
                alpha_mix_nodes.append(alpha_mix)
        # connect nodes in scatter source
        for image_node_idx, image_node in enumerate(new_image_nodes):
            scatter_source_nodes["Number of Images"].outputs[0].default_value = image_node_idx + 1
            scatter_source_links.new(scatter_source_nodes["Group Input"].outputs[0], image_node.inputs[0])
            if image_node_idx > 0:
                scatter_source_links.new(scatter_source_nodes["Fraction"].outputs[0], multiply_nodes[image_node_idx - 1].inputs[0])
                multiply_nodes[image_node_idx - 1].inputs[1].default_value = image_node_idx
                scatter_source_links.new(scatter_source_nodes["Group Input"].outputs[1], greater_nodes[image_node_idx - 1].inputs[0])
                scatter_source_links.new(multiply_nodes[image_node_idx - 1].outputs[0], greater_nodes[image_node_idx - 1].inputs[1])
                scatter_source_links.new(greater_nodes[image_node_idx - 1].outputs[0], col_mix_nodes[image_node_idx - 1].inputs[0])
                scatter_source_links.new(greater_nodes[image_node_idx - 1].outputs[0], alpha_mix_nodes[image_node_idx - 1].inputs[0])
                if image_node_idx == 1:
                    scatter_source_links.new(new_image_nodes[image_node_idx - 1].outputs[0], col_mix_nodes[image_node_idx - 1].inputs[1])
                    scatter_source_links.new(new_image_nodes[image_node_idx - 1].outputs[1], alpha_mix_nodes[image_node_idx - 1].inputs[1])
                else: 
                    scatter_source_links.new(new_image_nodes[image_node_idx - 1].outputs[0], col_mix_nodes[image_node_idx - 2].inputs[2])
                    scatter_source_links.new(new_image_nodes[image_node_idx - 1].outputs[1], alpha_mix_nodes[image_node_idx - 2].inputs[2])
                    scatter_source_links.new(col_mix_nodes[image_node_idx - 2].outputs[0], col_mix_nodes[image_node_idx - 1].inputs[1])
                    scatter_source_links.new(alpha_mix_nodes[image_node_idx - 2].outputs[0], alpha_mix_nodes[image_node_idx - 1].inputs[1])
                scatter_source_links.new(new_image_nodes[-1].outputs[0], col_mix_nodes[-1].inputs[2])
                scatter_source_links.new(new_image_nodes[-1].outputs[1], alpha_mix_nodes[-1].inputs[2])
                scatter_source_links.new(col_mix_nodes[-1].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                scatter_source_links.new(alpha_mix_nodes[-1].outputs[0], scatter_source_nodes["Alpha Result"].inputs[0])
            else:
                scatter_source_links.new(new_image_nodes[0].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                scatter_source_links.new(new_image_nodes[0].outputs[1], scatter_source_nodes["Alpha Result"].inputs[0])
        return new_image_nodes
        
    def copy_to_all_scatter_sources(scatter_source):
        scatter_source_groups = [x for x in nodes if x.label == "Scatter Source"]
        for x in scatter_source_groups:
            x.node_tree = scatter_source.node_tree

    def connect_scatter_source(scatter_source, channel):
        links.new(nodes['Scatter Coordinates'].outputs['Vector'], scatter_source.inputs['Vector'])
        links.new(nodes['Scatter Coordinates'].outputs['Random Color'], scatter_source.inputs['Random Color'])
        links.new(nodes['Density Input'].outputs[0], scatter_source.inputs['Density'])
        links.new(nodes['Group Input'].outputs['Alpha Clip'], scatter_source.inputs['Alpha Clip'])
        if channel not in scatter_node.node_tree.outputs:
            scatter_node.node_tree.outputs.new("NodeSocketColor", channel)
        links.new(scatter_source.outputs[0], nodes['Group Output'].inputs[channel])

    scatter_sources = {}
    for channel_idx, channel in enumerate(sorted_textures.keys()):
        scatter_sources[channel] = []
        if self.layering == 'blended':
            for image_node_idx, image_node in enumerate(sorted_textures[channel]):
                scatter_source = add_scatter_source(image_node_idx, channel_idx, len(sorted_textures[channel]))
                image_nodes = setup_image_nodes(scatter_source, channel, [image_node])
                scatter_source.node_tree.outputs[0].name = channel
                connect_scatter_source(scatter_source, channel)
                scatter_sources[channel].append(scatter_source)
        elif self.layering == 'overlapping':
            scatter_source = nodes['Scatter Source']
            image_nodes = setup_image_nodes(scatter_source, channel, sorted_textures[channel])
            copy_to_all_scatter_sources(scatter_source)
            scatter_sources[channel].append(scatter_source)
        elif channel_idx == 0:
            scatter_source = nodes['Scatter Source']
            scatter_source.node_tree = bpy.data.node_groups['SS - Scatter Source Empty'].copy()
            scatter_source.node_tree.name = "SS - Scatter Source"
            image_nodes = setup_image_nodes(scatter_source, channel, sorted_textures[channel])
            scatter_source.node_tree.outputs[0].name = channel
            scatter_node.node_tree.outputs['Image'].name = channel
            scatter_sources[channel].append(scatter_source)
        else:
            scatter_source = add_scatter_source(channel_idx)
            image_nodes = setup_image_nodes(scatter_source, channel, sorted_textures[channel])
            scatter_source.node_tree.outputs[0].name = channel
            connect_scatter_source(scatter_source, channel)
            scatter_sources[channel].append(scatter_source)
    return scatter_sources

def manage_colors(self, scatter_node, scatter_sources):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    reversed_color_results = {}

    def create_randomize_node(scatter_source, channel):
        value_channels = ['AO', 'Metallic', 'Specular', 'Roughness', 'Glossiness', 'Alpha', 'Bump']
        if channel in value_channels:
            randomize_node = append_node(nodes, "SS - Randomize Value")
            randomize_node.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
            links.new(scatter_source.outputs[0], randomize_node.inputs[0])
            links.new(scatter_source.outputs[1], randomize_node.inputs[1])
            if ('Random ' + channel) not in scatter_node.node_tree.inputs:
                new_input = scatter_node.node_tree.inputs.new('NodeSocketFloatFactor', 'Random ' + channel)
                new_input.min_value = 0
                new_input.max_value = 1
                moving_from = -1
                for input in scatter_node.node_tree.inputs:
                    moving_from += 1
                moving_to = 13
                scatter_node.node_tree.inputs.move(moving_from, moving_to)
            links.new(nodes['Group Input'].outputs['Random ' + channel], randomize_node.inputs['Random Value'])
            randomize_node.inputs['Random Seed'].default_value = random()
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        else:
            randomize_node = append_node(nodes, "SS - Randomize HSV")
            randomize_node.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
            links.new(scatter_source.outputs[0], randomize_node.inputs[0])
            links.new(scatter_source.outputs[1], randomize_node.inputs[1])
            links.new(nodes['Group Input'].outputs['Random Hue'], randomize_node.inputs['Random Hue'])
            links.new(nodes['Group Input'].outputs['Random Saturation'], randomize_node.inputs['Random Saturation'])
            links.new(nodes['Group Input'].outputs['Random Value'], randomize_node.inputs['Random Value'])
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        return randomize_node
    
    if self.use_random_col and self.layering != 'overlapping':
        # reversing the channels makes sure that any new scatter node inputs are in the right order
        channels = [*scatter_sources]
        channels.reverse()
        for channel_idx, channel in enumerate(channels):
            reversed_color_results[channel] = []
            for scatter_source in scatter_sources[channel]:
                if channel != 'Normal':
                    randomize_node = create_randomize_node(scatter_source, channel)
                    reversed_color_results[channel].append(randomize_node.outputs[0])
                else:
                    reversed_color_results[channel].append(scatter_source.outputs[0])
    elif self.use_random_col and self.layering == 'overlapping':
        reversed_color_results['Image'] = []
        reversed_color_results['Image'].append(nodes['Color Output'].outputs[0])
    elif not self.use_random_col and self.layering == 'overlapping':
        reversed_color_results['Image'] = []
        inputs = scatter_node.node_tree.inputs
        inputs.remove(inputs['Random Hue'])
        inputs.remove(inputs['Random Saturation'])
        inputs.remove(inputs['Random Value'])
        nodes.remove(nodes['SS - Randomize HSV'])
        nodes.remove(nodes['Group Input Random Col'])
        links.new(nodes['Color Result'].outputs[0], nodes['Color Output'].inputs[0])
        reversed_color_results['Image'].append(nodes['Color Result'].outputs[0])
    elif not self.use_random_col:
        for channel in scatter_sources:
            reversed_color_results[channel] = []
            for scatter_source in scatter_sources[channel]:
                reversed_color_results[channel].append(scatter_source.outputs[0])
        inputs = scatter_node.node_tree.inputs
        inputs.remove(inputs['Random Hue'])
        inputs.remove(inputs['Random Saturation'])
        inputs.remove(inputs['Random Value'])
    # the channel order needs to be fixed after flipping it above
    color_results = {}
    for channel in scatter_sources:
        color_results[channel] = reversed_color_results[channel]
    return color_results

def blend_colors(self, scatter_node, color_results):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    nodes_to_mix = []
    for channel in color_results:
        for output in color_results[channel]:
            nodes_to_mix.append(output.node)
    blending_node = noise_blend(self, nodes_to_mix, color_results, 'custom')
    links.new(nodes['Pattern Scale'].outputs[0], blending_node.inputs['Vector'])
    for output in blending_node.outputs:
        links.new(output, nodes['Group Output'].inputs[output.name])
    blending_inputs = ['Scale', 'Detail', 'Roughness', 'Blur']
    input_count = len(scatter_node.inputs)
    for input_name in blending_inputs:
        links.new(nodes['Group Input'].outputs[-1], blending_node.inputs['Noise ' + input_name])
        scatter_node.node_tree.inputs['Noise ' + input_name].name = 'Blending ' + input_name
    for input_idx, input in enumerate(blending_inputs):
         scatter_node.node_tree.inputs.move(input_count + input_idx, 2 + input_idx)

def manage_alpha(self, scatter_node, scatter_sources, color_results, transparency):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links

    def mix_background(channel, output):
        get_alpha_node = nodes.new("ShaderNodeMath")
        get_alpha_node.operation = 'GREATER_THAN'
        get_alpha_node.inputs[1].default_value = 0
        get_alpha_node.location = [0, output.node.location[1]]
        links.new(nodes['Scatter Source'].outputs[1], get_alpha_node.inputs[0])
        alpha_over_node = nodes.new("ShaderNodeMixRGB")
        alpha_over_node.location = [get_alpha_node.location[0] + 175, get_alpha_node.location[1] - 50]
        links.new(get_alpha_node.outputs[0], alpha_over_node.inputs[0])
        links.new(output, alpha_over_node.inputs[2])
        links.new(alpha_over_node.outputs[0], nodes['Group Output'].inputs[channel])
        if channel == 'Image':
            new_input_name = 'Background'
        else:
            new_input_name = channel
        if new_input_name not in scatter_node.inputs:
            scatter_node.inputs.new('NodeSocketColor', new_input_name)
        links.new(nodes['Group Input'].outputs[new_input_name], alpha_over_node.inputs[1])
        if channel == 'Bump' or channel == 'Roughness' or channel == 'Glossiness' or channel == 'Specular':
            scatter_node.inputs[new_input_name].default_value = [0.5, 0.5, 0.5, 1]
        elif channel == 'AO' or channel == 'Albedo':
            scatter_node.inputs[new_input_name].default_value = [1, 1, 1, 1]
        elif channel == 'Normal':
            scatter_node.inputs[new_input_name].default_value = [0.5, 0.5, 1, 1]

    if transparency and self.layering != 'overlapping':
        for channel_idx, channel in enumerate(color_results.keys()):
            for output_idx, output in enumerate(color_results[channel]):
                mix_background(channel, output)
    elif not transparency:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Density'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Alpha Clip'])
        nodes.remove(nodes['Density Input'])
        for channel in scatter_sources:
            for scatter_source in scatter_sources[channel]:
                source_nodes =  scatter_source.node_tree.nodes
                transparency_nodes = [x for x in source_nodes if x.parent and x.parent.name == 'Transparency Options']
                for x in transparency_nodes: source_nodes.remove(x)
                source_nodes.remove(source_nodes['Transparency Options'])
                scatter_source.node_tree.links.new(source_nodes['Group Input'].outputs['Random Color'], source_nodes['Group Output'].inputs['Random Color'])

def cleanup_layering(self, scatter_node, scatter_sources):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links

    if self.layering == 'blended':
        nodes.remove(nodes['Scatter Source'])
        scatter_source = scatter_sources[[*scatter_sources][0]][0]
        links.new(scatter_source.outputs[1], nodes['Group Output'].inputs['Random Color'])
        if self.use_pbr and 'Image' not in scatter_sources.keys():
            scatter_node.node_tree.outputs.remove(scatter_node.node_tree.outputs['Image'])
            outputs = scatter_node.node_tree.outputs
            output_count = len(outputs)
            outputs.move(0, output_count - 1) 

    if (self.layering == 'simple' or self.layering == 'simple_alpha' or self.layering == 'layered') and self.use_pbr:
        outputs = scatter_node.node_tree.outputs
        output_count = len(outputs)
        outputs.move(1, output_count - 1) 

def cleanup_options(self, scatter_node, scatter_coordinates):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links

    if self.projection_method == 'uv':
        nodes.remove(nodes['Tri-Planar Mapping'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Tri-Planar Blending'])
        links.new(nodes['Centered UVs'].outputs[0], nodes['Pattern Scale'].inputs[0])
    else:
        nodes.remove(nodes['Centered UVs'])

    if not self.use_edge_blur:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Blur'])
        nodes.remove(nodes['White Noise Texture'])
        scatter_coordinates.inputs.remove(scatter_coordinates.inputs['Edge Blur'])
        scatter_coordinates.inputs.remove(scatter_coordinates.inputs['Edge Blur Noise'])
        scatter_coordinates.nodes.remove(scatter_coordinates.nodes['Blur Range'])
        scatter_coordinates.nodes.remove(scatter_coordinates.nodes['Edge Blur'])
        if self.use_edge_warp:
            scatter_coordinates.links.new(scatter_coordinates.nodes['Shift Cells'].outputs[0], scatter_coordinates.nodes['Edge Warp'].inputs[1])
        else:
            scatter_coordinates.links.new(scatter_coordinates.nodes['Shift Cells'].outputs[0], scatter_coordinates.nodes['Voronoi Texture'].inputs[0])

    if not self.use_edge_warp:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp Scale'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp Detail'])
        nodes.remove(nodes['Noise Texture'])
        scatter_coordinates.inputs.remove(scatter_coordinates.inputs['Edge Warp'])
        scatter_coordinates.inputs.remove(scatter_coordinates.inputs['Edge Warp Noise'])
        scatter_coordinates.nodes.remove(scatter_coordinates.nodes['Edge Warp'])
        if self.use_edge_blur:
            scatter_coordinates.links.new(scatter_coordinates.nodes['Edge Blur'].outputs[0], scatter_coordinates.nodes['Voronoi Texture'].inputs[0])
        else:
            scatter_coordinates.links.new(scatter_coordinates.nodes['Shift Cells'].outputs[0], scatter_coordinates.nodes['Voronoi Texture'].inputs[0])

    if not self.use_texture_warp:
        for node in nodes:
            if node.parent and node.parent.name == 'Texture Warp':
                nodes.remove(node)
        nodes.remove(nodes['Texture Warp'])
        links.new(nodes['Scaled Coordinates'].outputs[0], nodes['Warped Coordinates'].inputs[0])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp Scale'])

def connect_shader(self, selected_nodes, scatter_node):
    nodes = selected_nodes[0].id_data.nodes
    links = selected_nodes[0].id_data.links
    for node in selected_nodes:
        if node.type == 'TEX_IMAGE':
            for output in node.outputs:
                for link in output.links:
                    if link.to_node.name == 'Emission Viewer':
                        links.new(scatter_node.outputs[0], nodes['Emission Viewer'].inputs[0])
        elif node.type == 'BSDF_PRINCIPLED':
            if self.use_pbr:
                nrm_node = None
                for output in scatter_node.outputs:
                    if output.name == 'Albedo' or output.name == 'Image':
                        links.new(output, node.inputs['Base Color'])
                    elif output.name == 'Metallic':
                        links.new(output, node.inputs['Metallic'])
                    elif output.name == 'Roughness':
                        links.new(output, node.inputs['Roughness'])
                    elif output.name == 'Emission':
                        links.new(output, node.inputs['Emission'])
                    elif output.name == 'Alpha':
                        links.new(output, node.inputs['Alpha'])
                    elif output.name == 'Normal':
                        nrm_node = nodes.new('ShaderNodeNormalMap')
                        nrm_node.location = [node.location[0] - 200, node.location[1] - 350]
                        links.new(output, nrm_node.inputs['Color'])
                        links.new(nrm_node.outputs[0], node.inputs['Normal'])
                    elif output.name == 'Bump':
                        bump_node = nodes.new('ShaderNodeBump')
                        bump_node.location = [node.location[0] - 200, node.location[1] - 500]
                        bump_node.inputs['Distance'].default_value = 0.025
                        links.new(output, bump_node.inputs['Height'])
                        links.new(bump_node.outputs[0], node.inputs['Normal'])
                        if nrm_node:
                            links.new(nrm_node.outputs[0], bump_node.inputs['Normal'])
            else: 
                links.new(scatter_node.outputs[0], node.inputs[0])
        elif node.type == 'BSDF_DIFFUSE':
            links.new(scatter_node.outputs[0], node.inputs[0])

def remove_images(selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    textures = [x for x in selected_nodes if x.type == 'TEX_IMAGE']
    for texture in textures: nodes.remove(texture)

def setup_scatter_node(self, selected_nodes, should_remove=True):
    transparency = (self.layering == 'simple_alpha' or self.layering == 'layered' or self.layering == 'overlapping')
    sorted_textures = sort_textures(self, selected_nodes)
    scatter_node = append_scatter_node(self, selected_nodes)
    scatter_coordinates = create_scatter_coordinates(scatter_node)
    scatter_sources = create_scatter_sources(self, scatter_node, sorted_textures, transparency)
    color_results = manage_colors(self, scatter_node, scatter_sources)
    if self.layering == 'blended': blend_colors(self, scatter_node, color_results)
    manage_alpha(self, scatter_node, scatter_sources, color_results, transparency)
    cleanup_layering(self, scatter_node, scatter_sources)
    cleanup_options(self, scatter_node, scatter_coordinates)
    connect_shader(self, selected_nodes, scatter_node)
    if should_remove: remove_images(selected_nodes)
    return scatter_node

def create_layered_node(self, selected_nodes):

    def create_master_node():
        nodes = selected_nodes[0].id_data.nodes
        # creating the outer node like this is wasteful, but Blender crashes if creating so many node tree inputs via python
        master_node = setup_scatter_node(self, selected_nodes, False)
        master_node.node_tree.name = 'SS - Scatter Layered'
        master_node.location = average_location(selected_nodes)
        for node in master_node.node_tree.nodes:
            if node.name != 'Group Input' and node.name != 'Group Output':
                master_node.node_tree.nodes.remove(node)
        return master_node

    def create_inner_nodes(master_node):
        nodes = master_node.node_tree.nodes
        textures = [x for x in selected_nodes if x.type == 'TEX_IMAGE']
        nodes_to_scatter = []
        for node_idx, node in enumerate(textures):
            inner_node = nodes.new("ShaderNodeTexImage")
            inner_node.image = node.image
            inner_node.interpolation = node.interpolation
            inner_node.projection = node.projection
            inner_node.extension = node.extension
            inner_node.interpolation = node.interpolation
            nodes_to_scatter.append(inner_node)
        sorted_textures = sort_textures(self, nodes_to_scatter)
        max_nodes = max([ len(sorted_textures[x]) for x in sorted_textures ])
        tex_sets = []
        for idx in range(max_nodes):
            tex_set = []
            for channel in sorted_textures:
                if len(sorted_textures[channel]) > idx:
                    tex_set.append(sorted_textures[channel][idx])
            tex_sets.append(tex_set)
        scatter_nodes = []
        for set_idx, set in enumerate(tex_sets):
            scatter_node = setup_scatter_node(self, set)
            scatter_node.location = [300 * set_idx, 0]
            scatter_nodes.append(scatter_node)
        return scatter_nodes

    def link_inner_nodes(master_node, scatter_nodes):
        nodes = master_node.node_tree.nodes
        links = master_node.node_tree.links
        input_node = nodes['Group Input']
        input_node.location = [-500, 100]
        output_node = nodes['Group Output']
        output_node.location = [len(scatter_nodes) * 300 + 300, 100]
        last_idx = len(scatter_nodes) - 1
        for node_idx, node in enumerate(scatter_nodes):
            for input in node.inputs:
                if input.name != 'Background':
                    links.new(input_node.outputs[input.name], input)
            if node_idx == 0:
                for output in node.outputs:
                    if output.name == 'Image':
                        links.new(input_node.outputs['Background'], node.inputs['Background'])
                    elif output.name != 'Random Color':
                        links.new(input_node.outputs[output.name], node.inputs[output.name])
            elif node_idx > 0:
                seed = nodes.new("ShaderNodeMath")
                seed.location = [node.location[0] - 200, node.location[1] - 800]
                seed.operation = 'MULTIPLY'
                seed.inputs[1].default_value = 1 / (node_idx + 1)
                links.new(input_node.outputs['Random Seed'], seed.inputs[0])
                links.new(seed.outputs[0], node.inputs['Random Seed'])
        for node_idx, node in enumerate(scatter_nodes):
            if node_idx < last_idx:
                for output_idx, output in enumerate(node.outputs):
                    if output.name == 'Image':
                        if 'Image' in scatter_nodes[node_idx + 1].inputs:
                            links.new(output, scatter_nodes[node_idx + 1].inputs['Background'])
                        else:
                            self.report(
                                {'ERROR'}, 
                                'Please make sure each texture set has the same types of textures.' +
                                'One set does not have an Image channel. Inner nodes have not be set correctly'
                            )
                    elif output.name != 'Random Color':
                        if output.name in scatter_nodes[node_idx + 1].inputs:
                            links.new(output, scatter_nodes[node_idx + 1].inputs[output.name])
                        else:
                            self.report(
                                {'ERROR'}, 
                                'Please make sure each texture set has the same types of textures.' +
                                'One set does not have a %s channel. Inner nodes have not be set correctly' 
                                %(output.name)
                            )
            elif node_idx == last_idx:
                for output_idx, output in enumerate(node.outputs):
                    links.new(output, nodes['Group Output'].inputs[output_idx])

    master_node = create_master_node()
    scatter_nodes = create_inner_nodes(master_node)
    link_inner_nodes(master_node, scatter_nodes)
    connect_shader(self, selected_nodes, master_node)
    remove_images(selected_nodes)
    return master_node
    
def setup_defaults(self, scatter_node):
    pass

class NODE_OT_scatter(Operator):
    bl_label = "Voronoi Scatter"
    bl_idname = "node.scatter"
    bl_description = "Scatters image and procedural textures in one click"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    projection_method: bpy.props.EnumProperty(
        name = "Mapping",
        description = "How the texture is projected onto the model. The performance difference is negligible",
        items = [
            ("uv", "UV", "Scatter based on UV coordinates"),
            ("tri-planar", "Tri-Planar", "Scatter based on generated object coordinates")
        ],
        default = defaults.scatter['projection_method'],
    )
    texture_interpolation: bpy.props.EnumProperty(
        name = "Pixel Interpolation",
        description = "The pixel interpolation for each image",
        items = [
            ("Closest", "Closest", "Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee"),
            ("Cubic", "Cubic", "Pixels are smoothed but may cause artifacts between voronoi cells in Eevee. Only recommended for Cycles")
        ],
        default = defaults.scatter['texture_interpolation'], 
    )
    layering: bpy.props.EnumProperty(
        name = "Scatter Method",
        description = "How the texture interacts with the background and the other scattered textures around it",
        items = [
            ("coordinates", "Just Coordinates", "Creates a scatter node that only outputs the scattered vectors for greater flexibility"),
            ("simple", "Interspersed", "A random texture is chosen per cell and each texture is set to repeat to prevent gaps and all transparency settings are removed to improve performance"),
            ("blended", "Noise Blended", "Each texture is scattered on its own and then they are all blended together using a noise texture"),
            ("simple_alpha", "Interspersed Alpha", "A random texture is chosen per cell and adds ability to change the background, alpha clip threshold, and scatter density"),
            ("layered", "Layered Alpha", "Creates Interspersed Alpha scatter nodes for each texture and chains them all together, which allows for very a basic overlap that is faster than using Overlapping"),
            ("overlapping", "Overlapping Alpha", "All the options of Simple Alpha with the additional benefit of enabling neighboring cells to overlap each other. This increases shader compilation time since 9 cells are calculated rather than 1")
        ],
        default = defaults.scatter['layering'],
    )
    use_edge_blur: bpy.props.BoolProperty(
        name = "Enable Edge Blur",
        description = "Adds ability to blend the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures",
        default = defaults.scatter['use_edge_blur'],
    )
    use_edge_warp: bpy.props.BoolProperty(
        name = "Enable Edge Warp",
        description = "Adds ability to distort the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures",
        default = defaults.scatter['use_edge_warp'],
    )
    use_texture_warp: bpy.props.BoolProperty(
        name = "Enable Texture Warp",
        description = "Adds ability to distort the shape of the resulting texture",
        default = defaults.scatter['use_texture_warp'],
    )
    use_random_col: bpy.props.BoolProperty(
        name = "Enable Random Color",
        description = "Adds easy controls for varying the color of each instance",
        default = defaults.scatter['use_random_col'],
    )
    use_pbr: bpy.props.BoolProperty(
        name = "Detect PBR Channels",
        description = "Automatically detects PBR textures based on the image name and scatters each texture set accordingly",
        default = defaults.scatter['use_pbr'],
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "projection_method", expand=True)
        layout.prop(self, "layering")
        layout.prop(self, "texture_interpolation")
        layout.prop(self, "use_edge_blur")
        layout.prop(self, "use_edge_warp")
        layout.prop(self, "use_texture_warp")
        random_col_row = layout.row()
        random_col_row.enabled = self.layering != "coordinates"
        random_col_row.prop(self, "use_random_col")
        pbr_row = layout.row()
        pbr_row.enabled = (self.layering != "coordinates" and self.layering != "overlapping")
        pbr_row.prop(self, "use_pbr")

    @classmethod
    def poll(cls, context):
        if context.selected_nodes:
            nodes = context.selected_nodes[0].id_data.nodes
            return [x for x in nodes if (x.select and x.type == 'TEX_IMAGE' and x.image)]
        else:
            return False
            
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        if self.layering == 'coordinates':
            create_coordinates_node(self, selected_nodes)
        elif self.layering == 'layered':
            create_layered_node(self, selected_nodes)
        else:
            setup_scatter_node(self, selected_nodes)
        setup_defaults(self)
        return {'FINISHED'}
 
def draw_menu(self, context):
    self.layout.separator()
    self.layout.operator(NODE_OT_scatter.bl_idname)
    
def register():
    bpy.utils.register_class(NODE_OT_scatter)
    bpy.types.NODE_MT_node.append(draw_menu)
    bpy.types.NODE_MT_context_menu.append(draw_menu)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_scatter)
    bpy.types.NODE_MT_node.remove(draw_menu)
    bpy.types.NODE_MT_context_menu.remove(draw_menu)
