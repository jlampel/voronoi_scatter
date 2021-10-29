import os
import re 
import bpy 
from .defaults import file_types, texture_names

def append_node(nodes, node_tree_name):
    path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'scatter_nodes.blend\\NodeTree\\')
    node_group = nodes.new("ShaderNodeGroup")
    initial_nodetrees = set(bpy.data.node_groups)
    bpy.ops.wm.append(filename=node_tree_name, directory=path)
    appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
    appended_node = [x for x in appended_nodetrees if node_tree_name in x.name][0]
    node_group.node_tree = bpy.data.node_groups[appended_node.name].copy()
    node_group.node_tree.name = node_tree_name
    return node_group

def average_location(selected_nodes):
    return [
        sum([x.location[0] for x in selected_nodes]) / len(selected_nodes),
        sum([x.location[1] for x in selected_nodes]) / len(selected_nodes)
    ]

def create_friendly_name(x):
    name = x
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    for word in re.split('[^a-z]', name.lower()):
        if word in texture_names['albedo']: 
            name = 'Albedo'
            break
        if word in texture_names['ao']: 
            name = 'AO'
            break
        elif word in texture_names['metal']: 
            name = 'Metallic'
            break
        elif word in texture_names['rough']:
            name = 'Roughness'
            break
        elif word in texture_names['gloss']:
            name = 'Glossiness'
            break
        elif word in texture_names['spec']:
            name = 'Specular'
            break
        elif word in texture_names['emit']:
            name = 'Emission'
            break
        elif word in texture_names['alpha']:
            name = 'Alpha'
            break
        elif word in texture_names['normal']:
            name = 'Normal'
            break
        elif word in texture_names['bump']:
            name = 'Bump'
            break
    return name 

def create_sortable_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    all_words = re.split('[^\d\w]*[\(\)\_\-\s]', name.lower())
    without_spaces = []
    for word in all_words:
        if word == '':
            pass
        else: 
            without_spaces.append(word)
    name = without_spaces
    return name

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
