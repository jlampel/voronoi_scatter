import os
import re 
import bpy 

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
        sum([x.location[1] for x in selected_nodes]) / len(selected_nodes) + 150
    ]

def create_friendly_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']
    albedo_names = ['albedo', 'base color', 'base_color', 'basecolor', 'base_col', 'color', 'diffuse', 'diff', 'col', 'd']
    ao_names = ['ao', 'ambient_occlusion', 'ambient occlusion', 'occlusion']
    metal_names = ['metal', 'metallic', 'metalness', 'm', 'met', 'mt']
    rough_names = ['roughness', 'rough', 'r', 'rgh']
    gloss_names = ['gloss', 'glossiness', 'gls']
    spec_names = ['spec', 'specular', 'spc', 'refl', 'reflection']
    emit_names = ['emit', 'emission', 'emissive', 'glow', 'glw', 'e']
    alpha_names = ['alpha', 'transparent', 'transparency', 'opacity']
    normal_names = ['normal', 'nrm', 'n', 'nrlm']
    bump_names = ['bmp', 'bump', 'height', 'h', 'dp', 'displacement']
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    for word in re.split('[^a-z]', name.lower()):
        if word in albedo_names: 
            name = 'Albedo'
            break
        if word in ao_names: 
            name = 'AO'
            break
        elif word in metal_names: 
            name = 'Metallic'
            break
        elif word in rough_names:
            name = 'Roughness'
            break
        elif word in gloss_names:
            name = 'Glossiness'
            break
        elif word in spec_names:
            name = 'Specular'
            break
        elif word in emit_names:
            name = 'Emission'
            break
        elif word in alpha_names:
            name = 'Alpha'
            break
        elif word in normal_names:
            name = 'Normal'
            break
        elif word in bump_names:
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

def remove_section(nodes, title):
    for node in nodes:
        if node.parent and node.parent.name == title:
            nodes.remove(node)
    nodes.remove(nodes[title])