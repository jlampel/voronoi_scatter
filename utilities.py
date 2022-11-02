import os
import re
import bpy
from .defaults import texture_names

def append_node(self, nodes, node_tree_name):
    path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'scatter_nodes.blend\\NodeTree\\')

    node_group = nodes.new("ShaderNodeGroup")
    initial_nodetrees = set(bpy.data.node_groups)

    try:
        bpy.ops.wm.append(filename=node_tree_name, directory=path)
    except:
        self.report({'ERROR'}, 'Scattershot nodes not detected. Please download from the Blender Market and install again.')
        nodes.remove(node_group)

    appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
    appended_node = [x for x in appended_nodetrees if node_tree_name in x.name][0]
    node_group.node_tree = bpy.data.node_groups[appended_node.name].copy()
    node_group.node_tree.name = node_tree_name
    return node_group

def name_array_to_string(name_array):
    name_string = ''
    for name in name_array:
        name_string += name + ', '
    return name_string[:-2]

def name_string_to_array(name_string):
    return [x for x in re.split(', ', name_string)]

def average_location(selected_nodes):
    return [
        sum([x.location[0] for x in selected_nodes]) / len(selected_nodes),
        sum([x.location[1] for x in selected_nodes]) / len(selected_nodes)
    ]

def create_friendly_name(context, texture_name):
    preferences = context.preferences.addons[__package__].preferences
    name = texture_name
    for file_type in preferences.file_types:
        extension = '.' + file_type.lower()
        if extension in name:
            name = name.replace(extension, '')
    name_array = []
    # Preferences can only be accessed by dot notation, so iterating through each channel with bracket notation does not work
    for word in re.split('[^a-z]', name.lower()):
        if word in name_string_to_array(preferences.albedo_names):
            name_array.append('Albedo')
        elif word in name_string_to_array(preferences.ao_names):
            name_array.append('AO')
        elif word in name_string_to_array(preferences.metal_names):
            name_array.append('Metallic')
        elif word in name_string_to_array(preferences.rough_names):
            name_array.append('Roughness')
        elif word in name_string_to_array(preferences.gloss_names):
            name_array.append('Glossiness')
        elif word in name_string_to_array(preferences.spec_names):
            name_array.append('Specular')
        elif word in name_string_to_array(preferences.emit_names):
            name_array.append('Emission')
        elif word in name_string_to_array(preferences.alpha_names):
            name_array.append('Alpha')
        elif word in name_string_to_array(preferences.normal_names):
            name_array.append('Normal')
        elif word in name_string_to_array(preferences.bump_names):
            name_array.append('Bump')
        elif word in name_string_to_array(preferences.displacement_names):
            name_array.append('Displacement')
    if len(name_array):
        return name_array[-1]
    else:
        return 'Image'

#def create_sortable_name(x):
#    name = x
#    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']
#    for t in file_types:
#        if t in name:
#            name = name.replace(t, '')
#    all_words = re.split('[^\d\w]*[\(\)\_\-\s]', name.lower())
#    without_spaces = []
#    for word in all_words:
#        if word == '':
#            pass
#        else:
#            without_spaces.append(word)
#    name = without_spaces
#    return name

def get_scatter_sources(selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    if selected_nodes:
        selected_group_nodes = [x for x in nodes if x.select and x.type == 'GROUP']
        scatter_sources = []
        for group_node in selected_group_nodes:
            for node in group_node.node_tree.nodes:
                if node.type == 'GROUP':
                    if 'SS - Scatter Source' in node.node_tree.name:
                        scatter_sources.append(node)
                    elif 'SS - Scatter Fast' in node.node_tree.name:
                        for inner_node in node.node_tree.nodes:
                            if inner_node.type == 'GROUP' and 'SS - Scatter Source' in inner_node.node_tree.name:
                                scatter_sources.append(inner_node)
        return scatter_sources
    else:
        return []

def mode_toggle(context, switch_to):
    prev_mode = context.mode
    switch = {
        'EDIT_MESH': bpy.ops.object.editmode_toggle,
        'SCULPT': bpy.ops.sculpt.sculptmode_toggle,
        'PAINT_VERTEX': bpy.ops.paint.vertex_paint_toggle,
        'PAINT_WEIGHT': bpy.ops.paint.weight_paint_toggle,
        'PAINT_TEXTURE': bpy.ops.paint.texture_paint_toggle
    }
    if prev_mode != 'OBJECT':
        switch[prev_mode]()
    elif switch_to != 'OBJECT':
        switch[switch_to]()
    return prev_mode

def remove_section(nodes, title):
    for node in nodes:
        if node.parent and node.parent.name == title:
            nodes.remove(node)
    nodes.remove(nodes[title])
