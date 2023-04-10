'''
Copyright (C) 2020-2023 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of Scattershot, created by Jonathan Lampel. 

All code distributed with this add-on is open source as described below. 

Scattershot is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''


import bpy
from bpy.types import (Operator)
from .utilities import append_node, mode_toggle, is_shader
from .defaults import node_names

def connect_vector(links, nodes, from_node, to_node):
    has_coordinates = False
    for input in from_node.inputs:
        if (input.name == 'Vector' or input.name == 'UV Map') and input.links:
            links.new(input.links[0].from_socket, to_node.inputs['Vector'])
            has_coordinates == True
            break

def create_randomize_node(self, context):
    nodes = context.selected_nodes[0].id_data.nodes
    links = context.selected_nodes[0].id_data.links
    for node in context.selected_nodes:
        randomize_node = append_node(self, nodes, node_names['randomize_noise_hsv'])
        connect_vector(links, nodes, node, randomize_node)
        randomize_node.width = 200
        if is_shader(node):
            randomize_node.location = [node.location[0] - randomize_node.width - 50, node.location[1]]
            if hasattr(node.inputs, 'Base Color'):
                to_socket = node.inputs['Base Color']
            elif hasattr(node.inputs, 'Color'):
                to_socket = node.inputs['Color']
            else: 
                to_socket = node.inputs[0]
            if to_socket.links:
                links.new(to_socket.links[0].from_socket, randomize_node.inputs[0])
            links.new(randomize_node.outputs[0], to_socket)
        else:
            randomize_node.location = [node.location[0] + node.width + 50, node.location[1]]
            if node.outputs[0].links:
                for link in node.outputs[0].links:
                    links.new(randomize_node.outputs[0], node.outputs[0].links[0].to_socket)
            links.new(node.outputs[0], randomize_node.inputs[0])


class NODE_OT_randomize_col(Operator):
    bl_label = "Add HSV Noise"
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
        create_randomize_node(self, context)
        mode_toggle(context, prev_mode)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NODE_OT_randomize_col)

def unregister():
    bpy.utils.unregister_class(NODE_OT_randomize_col)