import bpy
from random import random
from pprint import pprint
from bpy.types import (Object, Operator)
from bpy.props import (BoolProperty, EnumProperty)
from . import defaults
from .noise_blending import noise_blend
from .unscatter import extract_images
from .utilities import append_node, create_friendly_name, average_location, remove_section, get_scatter_sources, mode_toggle
   
def sort_textures(self, selected_nodes):
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
        'Bump': [],
        'Normal': [],
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

    if self.layering == 'overlapping' and len(selected_nodes) > 4:
        self.report({'WARNING'}, 
            'Each texture must be computed 9 times for the overlapping method. Compilation may be slow. Try simple layering for faster renders'
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
    scatter_node.location = [average_location(selected_nodes)[0], average_location(selected_nodes)[1] + 150]
    return scatter_node

def create_scatter_coordinates(scatter_node):
    scatter_coordinates_groups = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Coordinates"]
    new_scatter_coordinates = scatter_coordinates_groups[0].node_tree.copy()
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
        scatter_source.location = [nodes['Scatter Coordinates'].location[0] + 400, - (225 * idx) - (250 * channel_idx * channel_len)]
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
            image_node.projection = 'FLAT'

            # Normal maps only work with Linear interpolation as of Blender 3.0 Alpha
            # It causes bad smoothing around tri-planar blending but can't be used at all by the overlapping method
            # https://developer.blender.org/T92589
            if channel == 'Normal' and self.layering != 'overlapping':
                image_node.interpolation = 'Linear'
            else: 
                image_node.interpolation = self.texture_interpolation

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

def blend_colors(self, scatter_node, scatter_sources):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    inputs = scatter_node.node_tree.inputs
    blending_inputs = ['Scale', 'Detail', 'Roughness', 'Blending']

    color_results = {}
    for channel in scatter_sources:
        color_results[channel] = []
        for scatter_source in scatter_sources[channel]:
            color_results[channel].append(scatter_source.outputs[0])

    if self.layering == 'blended':
        blending_results = {}

        nodes_to_mix = []
        for channel in color_results:
            for output in color_results[channel]:
                nodes_to_mix.append(output.node)
        blending_node = noise_blend(self, nodes_to_mix, color_results, 'custom')
        blending_node.name = "Noise Blend"
        links.new(nodes['Pattern Scale'].outputs[0], blending_node.inputs['Vector'])
        for output in blending_node.outputs:
            links.new(output, nodes['Group Output'].inputs[output.name])
            blending_results[output.name] = [output]
        for input_name in blending_inputs:
            links.new(nodes['Group Input'].outputs["Mix Noise " + input_name], blending_node.inputs['Noise ' + input_name])
        return blending_results
    elif self.layering != 'overlapping': 
        for input_name in blending_inputs:
            inputs.remove(inputs["Mix Noise " + input_name])
        return color_results
    else:
        return color_results

def randomize_cell_colors(self, scatter_node, scatter_sources, prev_outputs):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    inputs = scatter_node.node_tree.inputs
    color_results = {}

    def create_randomize_node(prev_node, scatter_source, channel):
        if channel in defaults.value_channels:
            randomize_node = append_node(nodes, "SS - Randomize Cell Value")
            randomize_node.location = [prev_node.location[0] + 250, prev_node.location[1]]
            links.new(prev_node.outputs[channel], randomize_node.inputs[0])
            links.new(scatter_source.outputs[1], randomize_node.inputs[1])
            links.new(nodes['Group Input'].outputs['Random Cell ' + channel], randomize_node.inputs['Random Value'])
            randomize_node.inputs['Random Seed'].default_value = random()
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        else:
            randomize_node = append_node(nodes, "SS - Randomize Cell HSV")
            randomize_node.location = [prev_node.location[0] + 250, prev_node.location[1]]
            links.new(prev_node.outputs[channel], randomize_node.inputs[0])
            links.new(scatter_source.outputs[1], randomize_node.inputs[1])
            links.new(nodes['Group Input'].outputs['Random Cell Hue'], randomize_node.inputs['Random Hue'])
            links.new(nodes['Group Input'].outputs['Random Cell Saturation'], randomize_node.inputs['Random Saturation'])
            links.new(nodes['Group Input'].outputs['Random Cell Value'], randomize_node.inputs['Random Value'])
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        return randomize_node

    def remove_unused_inputs():
        if self.use_random_col:
            channels = prev_outputs.keys()
            for value_channel in defaults.value_channels:
                if value_channel not in channels:
                    inputs.remove(inputs['Random Cell '+ value_channel])
            if 'Albedo' not in channels and 'Image' not in channels and 'Emission' not in channels:
                inputs.remove(inputs['Random Cell Hue'])
                inputs.remove(inputs['Random Cell Saturation'])
                inputs.remove(inputs['Random Cell Value'])
        else:
            for value_channel in defaults.value_channels:
                inputs.remove(inputs['Random Cell '+ value_channel])
            inputs.remove(inputs['Random Cell Hue'])
            inputs.remove(inputs['Random Cell Saturation'])
            inputs.remove(inputs['Random Cell Value'])
    
    if self.use_random_col and self.layering != 'overlapping':
        channels = [*prev_outputs]
        for channel in channels:
            color_results[channel] = []
            for output_idx, output in enumerate(prev_outputs[channel]):
                if channel != 'Normal':
                    scatter_source = scatter_sources[channel][output_idx]
                    randomize_node = create_randomize_node(output.node, scatter_source, channel)
                    color_results[channel].append(randomize_node.outputs[0])
                else:
                    color_results[channel].append(output)
        remove_unused_inputs()

    elif self.use_random_col and self.layering == 'overlapping':
        color_results['Image'] = []
        color_results['Image'].append(nodes['Color Output'].outputs[0])

    elif not self.use_random_col and self.layering == 'overlapping':
        color_results['Image'] = []
        nodes.remove(nodes['Randomize Cell HSV'])
        nodes.remove(nodes['Group Input Random Col'])
        color_results['Image'].append(nodes['Color Result'].outputs[0])
        inputs.remove(inputs['Random Cell Hue'])
        inputs.remove(inputs['Random Cell Saturation'])
        inputs.remove(inputs['Random Cell Value'])

    elif not self.use_random_col:
        for channel in prev_outputs:
            color_results[channel] = []
            for output in prev_outputs[channel]:
                color_results[channel].append(output)
        remove_unused_inputs()

    return color_results

def randomize_texture_colors(self, scatter_node, scatter_sources, prev_outputs):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    inputs = scatter_node.node_tree.inputs
    group_inputs = nodes['Group Input'].outputs
    color_results = {}

    def create_randomize_hsv(color_output, channel):
        if channel in defaults.value_channels:
            randomize_node = append_node(nodes, "SS - Noise Randomize Value")
            randomize_node.location = [color_output.node.location[0] + 250, color_output.node.location[1]]
            links.new(color_output, randomize_node.inputs[0])
            links.new(group_inputs[channel + ' Noise Scale'], randomize_node.inputs['Noise Scale'])
            links.new(group_inputs[channel + ' Noise Detail'], randomize_node.inputs['Noise Detail'])
            links.new(group_inputs[channel + ' Noise Warp'], randomize_node.inputs['Noise Warp'])
            links.new(group_inputs[channel + ' Noise'], randomize_node.inputs['Value Noise'])
            links.new(nodes['Scaled Coordinates'].outputs[0], randomize_node.inputs['Vector'])
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        else:
            randomize_node = append_node(nodes, "SS - Noise Randomize HSV")
            randomize_node.location = [color_output.node.location[0] + 250, color_output.node.location[1]]
            links.new(color_output, randomize_node.inputs[0])
            links.new(group_inputs['Color Noise Scale'], randomize_node.inputs['Noise Scale'])
            links.new(group_inputs['Color Noise Detail'], randomize_node.inputs['Noise Detail'])
            links.new(group_inputs['Color Noise Warp'], randomize_node.inputs['Noise Warp'])
            links.new(group_inputs['Hue Noise'], randomize_node.inputs['Hue Noise'])
            links.new(group_inputs['Saturation Noise'], randomize_node.inputs['Saturation Noise'])
            links.new(group_inputs['Value Noise'], randomize_node.inputs['Value Noise'])
            links.new(nodes['Scaled Coordinates'].outputs[0], randomize_node.inputs['Vector'])
            links.new(randomize_node.outputs[0], nodes['Group Output'].inputs[channel])
        return randomize_node

    def remove_unused_inputs():
        if self.use_noise_col and self.layering != 'overlapping':
            channels = scatter_sources.keys()
            for value_channel in defaults.value_channels:
                if value_channel not in channels:
                    inputs.remove(inputs[value_channel + " Noise"])
                    inputs.remove(inputs[value_channel + " Noise Scale"])
                    inputs.remove(inputs[value_channel + " Noise Detail"])
                    inputs.remove(inputs[value_channel + " Noise Warp"])
            if 'Albedo' not in channels and 'Image' not in channels and 'Emission' not in channels:
                inputs.remove(inputs['Hue Noise'])
                inputs.remove(inputs['Saturation Noise'])
                inputs.remove(inputs['Value Noise'])
                inputs.remove(inputs['Color Noise Scale'])
                inputs.remove(inputs['Color Noise Detail'])
                inputs.remove(inputs['Color Noise Warp'])

        else:
            if self.layering != 'overlapping':
                channels = ['Alpha', 'AO', 'Bump', 'Glossiness', 'Metallic', 'Roughness', 'Specular']
                for channel in channels:
                        inputs.remove(inputs[channel + ' Noise'])
                        inputs.remove(inputs[channel + ' Noise Scale'])
                        inputs.remove(inputs[channel + ' Noise Detail'])
                        inputs.remove(inputs[channel + ' Noise Warp'])
            inputs.remove(inputs['Hue Noise'])
            inputs.remove(inputs['Saturation Noise'])
            inputs.remove(inputs['Value Noise'])
            inputs.remove(inputs['Color Noise Scale'])
            inputs.remove(inputs['Color Noise Detail'])
            inputs.remove(inputs['Color Noise Warp'])

    if self.use_noise_col and self.layering != 'overlapping':
        channels = [*prev_outputs]
        for channel in channels:
            color_results[channel] = []
            for color_output in prev_outputs[channel]:
                if channel != 'Normal':
                    randomize_node = create_randomize_hsv(color_output, channel)
                    color_results[channel].append(randomize_node.outputs[0])
                else:
                    color_results[channel].append(color_output)
        remove_unused_inputs()

    elif not self.use_noise_col and self.layering != 'overlapping':
        color_results = prev_outputs
        remove_unused_inputs()

    elif self.use_noise_col and self.layering == 'overlapping':
        color_results['Image'] = []
        if not self.use_random_col:
            links.new(nodes['Color Result'].outputs[0], nodes['Randomize Texture HSV'].inputs[0])
        links.new(group_inputs['Hue Noise'], nodes['Randomize Texture HSV'].inputs['Hue Noise'])
        links.new(group_inputs['Saturation Noise'], nodes['Randomize Texture HSV'].inputs['Saturation Noise'])
        links.new(group_inputs['Value Noise'], nodes['Randomize Texture HSV'].inputs['Value Noise'])
        links.new(group_inputs['Color Noise Scale'], nodes['Randomize Texture HSV'].inputs['Noise Scale'])
        links.new(group_inputs['Color Noise Detail'], nodes['Randomize Texture HSV'].inputs['Noise Detail'])
        links.new(group_inputs['Color Noise Warp'], nodes['Randomize Texture HSV'].inputs['Noise Warp'])

    elif not self.use_noise_col and self.layering == 'overlapping':
        color_results['Image'] = []
        nodes.remove(nodes['Randomize Texture HSV'])
        if self.use_random_col:
            links.new(nodes['Randomize Cell HSV'].outputs[0], nodes['Color Output'].inputs[0])
        else:    
            links.new(nodes['Color Result'].outputs[0], nodes['Color Output'].inputs[0])
        remove_unused_inputs()

    return color_results

def correct_normals(self, scatter_node, prev_outputs):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links
    color_results = {}

    def fix_uv_normals(normal_map):
        normal_node = append_node(nodes, 'SS - UV Normal Map')
        normal_node.location = [normal_map.node.location[0] + 250, normal_map.node.location[1]]
        links.new(normal_map, normal_node.inputs[0])
        links.new(nodes['Scatter Coordinates'].outputs['Random Color'], normal_node.inputs['Random Color'])
        links.new(nodes['Group Input'].outputs['Texture Rotation'], normal_node.inputs['Rotation'])
        links.new(nodes['Group Input'].outputs['Random Texture Rotation'], normal_node.inputs['Random Rotation'])
        links.new(normal_node.outputs[0], nodes['Group Output'].inputs['Normal'])
        return normal_node.outputs[0]

    def fix_triplanar_normals(normal_map):
        normal_node = append_node(nodes, 'SS - Tri-Planar Normal Map')
        normal_node.location = [normal_map.node.location[0] + 250, normal_map.node.location[1]]
        links.new(normal_map, normal_node.inputs[0])
        links.new(nodes['Tri-Planar Mapping'].outputs['Axes'], normal_node.inputs['Axes'])
        links.new(nodes['Scatter Coordinates'].outputs['Random Color'], normal_node.inputs['Random Color'])
        links.new(nodes['Group Input'].outputs['Texture Rotation'], normal_node.inputs['Rotation'])
        links.new(nodes['Group Input'].outputs['Random Texture Rotation'], normal_node.inputs['Random Rotation'])
        links.new(normal_node.outputs[0], nodes['Group Output'].inputs['Normal'])
        return normal_node.outputs[0]

    for channel in prev_outputs:
        if channel == 'Normal':
            color_results['Normal'] = []
            for output in prev_outputs[channel]:
                if self.projection_method == 'uv':
                    color_result = fix_uv_normals(output)
                    color_results['Normal'].append(color_result)
                elif self.projection_method == 'tri-planar':
                    color_result = fix_triplanar_normals(output)
                    color_results['Normal'].append(color_result)
        else:
            color_results[channel] = prev_outputs[channel]
    
    return color_results

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
        if channel in ['Bump', 'Roughness', 'Glossiness', 'Specular', 'Albedo']:
            scatter_node.inputs[new_input_name].default_value = [0.5, 0.5, 0.5, 1]
        elif channel == 'AO':
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

    if self.layering != 'layered' and self.layering != 'overlapping':
        remove_section(nodes, 'Randomize Layers')
        links.new(nodes['Warped Coordinates'].outputs[0], nodes['Scatter Coordinates'].inputs['Vector'])

    # Optimize random locations to avoid clipping
    if self.layering != 'overlapping':
        nodes['Scatter Coordinates'].node_tree.nodes['Location Origin'].inputs[1].default_value = [0.5, 0.5, 0]
    if self.layering == 'simple' or self.layering == 'blended':
        nodes['Scatter Coordinates'].node_tree.nodes['Location Range'].inputs['To Max'].default_value = 3

def cleanup_options(self, scatter_node, scatter_coordinates):
    nodes = scatter_node.node_tree.nodes
    links = scatter_node.node_tree.links

    if self.projection_method == 'uv':
        nodes.remove(nodes['Tri-Planar Mapping'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Tri-Planar Blending'])
        links.new(nodes['Centered UVs'].outputs[0], nodes['Pattern Scale'].inputs[0])
    else:
        nodes.remove(nodes['Centered UVs'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['UV Map'])

    if not self.use_edge_blur:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Cell Blending'])
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
        remove_section(nodes, 'Texture Warp')
        links.new(nodes['Scaled Coordinates'].outputs[0], nodes['Warped Coordinates'].inputs[0])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp Scale'])

def cleanup_sockets(self, scatter_node, transparency):
    inputs = scatter_node.inputs
    node_tree_inputs = scatter_node.node_tree.inputs

    new_inputs = []
    input_count = len(inputs)
    for label in defaults.section_labels:
        count = 0
        for input in inputs:
            count += 1
            if label == input.name:
                new_input = node_tree_inputs.new('NodeSocketVirtual', label)
                inputs[input_count + len(new_inputs)].display_shape = 'DIAMOND_DOT'
                new_inputs.append([new_input, count])
                break
    for input_idx in range(len(new_inputs)):
        node_tree_inputs.move(input_count + input_idx, new_inputs[input_idx][1] + input_idx)
    for label in defaults.section_labels:
        for input in node_tree_inputs:
            if input.name == label:
                node_tree_inputs.remove(input)
                break

    if not transparency:
        node_tree_inputs.remove(node_tree_inputs['Transparency'])

    for output in scatter_node.outputs:
        if output.name in defaults.value_channels:
            output.type = 'VALUE'
        elif output.name == 'Normal':
            output.type = 'VECTOR'

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
                has_normal = False
                for output in reversed(scatter_node.outputs):
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
                        links.new(output, node.inputs['Normal'])
                        has_normal = True
                    elif output.name == 'Bump':
                        bump_node = nodes.new('ShaderNodeBump')
                        bump_node.location = [node.location[0] - 200, node.location[1] - 500]
                        bump_node.inputs['Strength'].default_value = 0.5
                        bump_node.inputs['Distance'].default_value = 0.1
                        links.new(output, bump_node.inputs['Height'])
                        links.new(bump_node.outputs[0], node.inputs['Normal'])
                        if has_normal:
                            links.new(scatter_node.outputs['Normal'], bump_node.inputs['Normal'])
            else: 
                links.new(scatter_node.outputs[0], node.inputs[0])
        elif node.type == 'BSDF_DIFFUSE':
            links.new(scatter_node.outputs[0], node.inputs[0])

def remove_images(selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    textures = [x for x in selected_nodes if x.type == 'TEX_IMAGE']
    for texture in textures: nodes.remove(texture)

def setup_scatter_node(self, selected_nodes, should_remove_images=True):
    transparency = (self.layering == 'simple_alpha' or self.layering == 'layered' or self.layering == 'overlapping')
    sorted_textures = sort_textures(self, selected_nodes)
    scatter_node = append_scatter_node(self, selected_nodes)
    scatter_coordinates = create_scatter_coordinates(scatter_node)
    scatter_sources = create_scatter_sources(self, scatter_node, sorted_textures, transparency)
    blending_results = blend_colors(self, scatter_node, scatter_sources)
    randomize_cell_outputs = randomize_cell_colors(self, scatter_node, scatter_sources, blending_results)
    randomize_color_outputs = randomize_texture_colors(self, scatter_node, scatter_sources, randomize_cell_outputs)
    corrected_normal_outputs = correct_normals(self, scatter_node, randomize_color_outputs)
    manage_alpha(self, scatter_node, scatter_sources, blending_results, transparency)
    cleanup_layering(self, scatter_node, scatter_sources)
    cleanup_options(self, scatter_node, scatter_coordinates)
    cleanup_sockets(self, scatter_node, transparency)
    connect_shader(self, selected_nodes, scatter_node)
    if should_remove_images: remove_images(selected_nodes)
    return scatter_node

def create_coordinates_node(self, selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    links = selected_nodes[0].id_data.links

    # append and attach node 
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

    # Create or attach vector coordinates
    if self.projection_method == 'uv':
        texture_coordinates = nodes.new("ShaderNodeTexCoord")
        texture_coordinates.location = [scatter_node.location[0] - 250, scatter_node.location[1] - 235]
        links.new(texture_coordinates.outputs['UV'], scatter_node.inputs['Vector'])
    else:
        tri_planar = append_node(nodes, 'SS - Tri-Planar Mapping')
        tri_planar.label = "Tri-Planar Mapping"
        tri_planar.width = 200
        tri_planar.location = [scatter_node.location[0] - 250, scatter_node.location[1] - 250]
        links.new(tri_planar.outputs['Vector'], scatter_node.inputs['Vector'])

    # clean up options 
    scatter_node_nodes = scatter_node.node_tree.nodes
    scatter_node_links = scatter_node.node_tree.links

    if not self.use_edge_blur:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Cell Blending'])
        scatter_node_nodes.remove(scatter_node_nodes['White Noise Texture'])
        scatter_node_nodes.remove(scatter_node_nodes['Blur Range'])
        scatter_node_nodes.remove(scatter_node_nodes['Edge Blur'])
        if self.use_edge_warp:
            scatter_node_links.new(scatter_node_nodes['Randomize Scatter'].outputs[0], scatter_node_nodes['Edge Warp'].inputs[1])
        else:
            scatter_node_links.new(scatter_node_nodes['Randomize Scatter'].outputs[0], scatter_node_nodes['Voronoi Texture'].inputs[0])
    if not self.use_edge_warp:
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp Scale'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Edge Warp Detail'])
        scatter_node_nodes.remove(scatter_node_nodes['Noise Texture'])
        scatter_node_nodes.remove(scatter_node_nodes['Edge Warp'])
        if self.use_edge_blur:
            scatter_node_links.new(scatter_node_nodes['Edge Blur'].outputs[0], scatter_node_nodes['Voronoi Texture'].inputs[0])
        else:
            scatter_node_links.new(scatter_node_nodes['Randomize Scatter'].outputs[0], scatter_node_nodes['Voronoi Texture'].inputs[0])
    if not self.use_texture_warp:
        remove_section(scatter_node_nodes, 'Texture Warp')
        scatter_node_links.new(scatter_node_nodes['Scaled Coordinates'].outputs[0], scatter_node_nodes['Warped Coordinates'].inputs[0])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp'])
        scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Texture Warp Scale'])

    return scatter_node

def create_layered_node(self, selected_nodes):

    def create_master_node():
        nodes = selected_nodes[0].id_data.nodes
        # creating the outer node like this is wasteful, but Blender crashes if creating so many node tree inputs via python
        master_node = setup_scatter_node(self, selected_nodes, should_remove_images=False)
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
            node.node_tree.nodes['Randomize X'].inputs[1].default_value = ((random() * 2) - 1) * 200
            node.node_tree.nodes['Randomize Y'].inputs[1].default_value = ((random() * 2) - 1) * 200
            for input in node.inputs:
                if input.name != 'Background':
                    links.new(input_node.outputs[input.name], input)
            if node_idx == 0:
                for output in node.outputs:
                    if output.name == 'Image':
                        links.new(input_node.outputs['Background'], node.inputs['Background'])
                    elif output.name != 'Random Color':
                        links.new(input_node.outputs[output.name], node.inputs[output.name])
        for node_idx, node in enumerate(scatter_nodes):
            if node_idx < last_idx:
                for output_idx, output in enumerate(node.outputs):
                    if output.name == 'Image':
                        if 'Background' in scatter_nodes[node_idx + 1].inputs:
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
    if defaults.layering.get('common'):
        for default in defaults.layering['common'].keys():
            if default in [x.name for x in scatter_node.inputs]:
                scatter_node.inputs[default].default_value = defaults.layering['common'][default]
    if defaults.layering.get(self.layering):
        for default in defaults.layering[self.layering].keys():
            if default in [x.name for x in scatter_node.inputs]:
                scatter_node.inputs[default].default_value = defaults.layering[self.layering][default]

def voronoi_scatter(self, context, prev_scatter_sources):
    selected_nodes = context.selected_nodes
    nodes = selected_nodes[0].id_data.nodes
    links = selected_nodes[0].id_data.links
    scatter_node = None

    prev_scatter_node = None
    prev_values = {}
    if prev_scatter_sources:
        # This only supports re-scattering one node at a time 
        prev_scatter_node = context.selected_nodes[0]
        for input in prev_scatter_node.inputs:
            if input.name not in defaults.section_labels:
                prev_values[input.name] = input.default_value
        selected_nodes = extract_images(self, selected_nodes)

    if self.layering == 'coordinates':
        scatter_node = create_coordinates_node(self, selected_nodes)
    elif self.layering == 'layered':
        scatter_node = create_layered_node(self, selected_nodes)
    else:
        scatter_node = setup_scatter_node(self, selected_nodes)
    setup_defaults(self, scatter_node)

    if prev_values:
        for input in scatter_node.inputs:
            if input.name in prev_values.keys():
                input.default_value = prev_values[input.name]
                if prev_scatter_node.inputs[input.name].links:
                    links.new(input, prev_scatter_node.inputs[input.name].links[0].from_socket)
        for output in scatter_node.outputs:
            if output.name in [x.name for x in prev_scatter_node.outputs]:
                for link in prev_scatter_node.outputs[output.name].links:
                    links.new(output, prev_scatter_node.outputs[output.name].links[0].to_socket)
        scatter_node.location = prev_scatter_node.location 
        nodes.remove(prev_scatter_node)

class NODE_OT_scatter(Operator):
    bl_label = "Scattershot: Voronoi Scatter"
    bl_idname = "node.scatter"
    bl_description = "Scatters all selected image textures"
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
            ("blended", "Noise Mixed", "Each texture is scattered on its own and then they are all blended together using a noise texture"),
            ("simple_alpha", "Interspersed Alpha", "A random texture is chosen per cell and adds ability to change the background, alpha clip threshold, and scatter density"),
            ("layered", "Layered Alpha", "Creates Interspersed Alpha scatter nodes for each texture and chains them all together, which allows for very a basic overlap that is faster than using Overlapping"),
            ("overlapping", "Overlapping Alpha", "All the options of Simple Alpha with the additional benefit of enabling neighboring cells to overlap each other. This increases shader compilation time since 9 cells are calculated rather than 1")
        ],
        default = defaults.scatter['layering'],
    )
    use_edge_blur: bpy.props.BoolProperty(
        name = "Cell Blending",
        description = "Adds ability to blend the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures, but requires more render samples for smooth results. Must be baked to use with true displacement",
        default = defaults.scatter['use_edge_blur'],
    )
    use_edge_warp: bpy.props.BoolProperty(
        name = "Cell Edge Warp",
        description = "Adds ability to distort the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures",
        default = defaults.scatter['use_edge_warp'],
    )
    use_texture_warp: bpy.props.BoolProperty(
        name = "Texture Warp",
        description = "Adds ability to distort the shape of the resulting texture",
        default = defaults.scatter['use_texture_warp'],
    )
    use_noise_col: bpy.props.BoolProperty(
        name = "Random Noise HSV",
        description = "Adds easy controls for varying the color based on a noise pattern",
        default = defaults.scatter['use_noise_col'],
    )
    use_random_col: bpy.props.BoolProperty(
        name = "Random Cell HSV",
        description = "Adds easy controls for varying the color of each instance",
        default = defaults.scatter['use_random_col'],
    )
    use_pbr: bpy.props.BoolProperty(
        name = "Auto Detect",
        description = "Automatically detects PBR textures based on the image name and scatters each texture set accordingly",
        default = defaults.scatter['use_pbr'],
    )
    # These three properties are only for unscattering 
    interpolation: bpy.props.EnumProperty(
        name = "Pixel Interpolation",
        description ="The pixel interpolation for each image",
        items = [
            ("Linear", "Linear", "Linear interpolation, Blender's default"),
            ("Closest", "Closest", "No interpolation"),
            ("Cubic", "Cubic", "Cubic interpolation. Smoothest option"),
            ("Smart", "Smart", "Cubic when magifying, otherwise linear (OSL use only)")
        ],
        default = defaults.unscatter['interpolation'],
    )
    projection: bpy.props.EnumProperty(
        name="Projection",
        description="Method to project texture on an object with a 3d texture vector",
        items = [
            ("FLAT", "Flat", "projected from the X Y coordiantes of the texture vector"),
            ("BOX", "Box", "Tri-planar projection"),
            ("SPHERE", "Sphere", "Image is projected spherically with the Z axis as the center"),
            ("TUBE", "Tube", "Image is projected from a cylinder with the Z axis as the center"),
        ],
        default = defaults.unscatter['projection'],
    )
    extension: bpy.props.EnumProperty(
        name="Extension",
        description="How the image is extrapolated beyond its origional bounds",
        items=[
            ("REPEAT", "Repeat", "Repeats texture horizontally and vertically"),
            ("CLIP", "Clip", "Sets pixels outside of texture as transparent"),
            ("EXTEND", "Extend", "Repeats only the boundary pixels of the texture")
        ],
        default = defaults.unscatter['extension'],
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "projection_method", expand=True)
        layout.prop(self, "layering")
        layout.prop(self, "texture_interpolation")
        pbr = layout.column(heading="PBR Channels")
        pbr_row = pbr.row()
        pbr_row.enabled = (self.layering != "coordinates" and self.layering != "overlapping")
        pbr_row.prop(self, "use_pbr")
        options = layout.column(heading="Additional Controls")
        options.prop(self, "use_edge_blur")
        options.prop(self, "use_edge_warp")
        random_col_row = options.row()
        random_col_row.enabled = self.layering != "coordinates"
        random_col_row.prop(self, "use_random_col")
        noise_col_row = options.row()
        noise_col_row.enabled = self.layering != "coordinates"
        noise_col_row.prop(self, "use_noise_col")
        options.prop(self, "use_texture_warp")

    @classmethod
    def poll(cls, context):
        if context.selected_nodes:
            nodes = context.selected_nodes[0].id_data.nodes
            return(
                [x for x in nodes if (x.select and x.type == 'TEX_IMAGE' and x.image)] 
                or (get_scatter_sources(context.selected_nodes) and len(context.selected_nodes) == 1)
            )
        else:
            return False
            
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # switching modes prevents context errors 
        prev_mode = mode_toggle(context, 'OBJECT')
        voronoi_scatter(self, context, get_scatter_sources(context.selected_nodes))
        mode_toggle(context, prev_mode)
        return {'FINISHED'}
 
def register(): 
    bpy.utils.register_class(NODE_OT_scatter)

def unregister():
    bpy.utils.unregister_class(NODE_OT_scatter)
