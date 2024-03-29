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
from .utilities.utilities import append_node, average_location, mode_toggle
from .defaults import node_tree_names

def check_vector_input(selected_nodes):
    has_vector = False
    for node in selected_nodes:
        for input in node.inputs:
            if input.name == 'Vector':
                has_vector = True
                break
        if has_vector: break
    return has_vector

def create_triplanar_node(self, context):
    nodes = context.selected_nodes[0].id_data.nodes
    links = context.selected_nodes[0].id_data.links
    textures = context.selected_nodes
    triplanar_node = append_node(self, nodes, node_tree_names['tri-planar'])
    triplanar_node.label = 'Tri-Planar Mapping'
    triplanar_node.location = [
        min([x.location[0] for x in textures]) - 250,
        average_location(textures)[1]
    ]
    triplanar_node.width = 200
    for node in context.selected_nodes:
        if check_vector_input([node]):
            links.new(triplanar_node.outputs['Vector'], node.inputs['Vector'])
            if node.type == 'TEX_IMAGE' and node.interpolation == 'Linear':
                self.report({'WARNING'},
                    'Image texture interpolation should be set to Closest or Cubic instead of Linear to avoid blending issues'
                )

class NODE_OT_triplanar_mapping(Operator):
    bl_label = "Tri-Planar Mapping"
    bl_idname = "node.triplanarmapping"
    bl_description = "Adds a tri-planar mapping node and connects it to the selected nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'ShaderNodeTree' and check_vector_input(context.selected_nodes)

    def execute(self, context):
        # switching modes prevents context errors
        prev_mode = mode_toggle(context, 'OBJECT')
        create_triplanar_node(self, context)
        mode_toggle(context, prev_mode)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NODE_OT_triplanar_mapping)

def unregister():
    bpy.utils.unregister_class(NODE_OT_triplanar_mapping)