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


from copy import copy
import bpy
from .utilities import get_scatter_sources, get_baked_sources, mode_toggle
from .defaults import texture_names

def clear_bake(context):
  selected_nodes = context.selected_nodes
  links = selected_nodes[0].id_data.links
  baked_nodes = [x for x in selected_nodes if get_baked_sources([x])]
  for scatter_node in baked_nodes:
    # Remove images
    for node in scatter_node.node_tree.nodes:
      if node.type == 'TEX_IMAGE':
        scatter_node.node_tree.nodes.remove(node)
    # Remove baked sockets
    for output in scatter_node.outputs:
      if output.name in texture_names.keys():
        baked_output_name = f"Baked {output.name}"
        if baked_output_name in scatter_node.outputs:
          to_sockets = [x.to_socket for x in scatter_node.outputs[baked_output_name].links]
          for socket in to_sockets:
            links.new(output, socket)
          scatter_node.node_tree.outputs.remove(scatter_node.node_tree.outputs[baked_output_name])
    # Remove UV input if using tri-planar
    if 'Centered UVs' not in [x.name for x in scatter_node.node_tree.nodes]:
      scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['UV Map'])
    scatter_node.node_tree.nodes['UV Map'].uv_map = ''
    # unhide inputs and outputs
    for input in scatter_node.inputs:
      input.hide = False
    for output in scatter_node.outputs:
      output.hide = False

class NODE_OT_clear_baked_scatter(bpy.types.Operator):
  bl_label = "Clear Baked Scatter"
  bl_idname = "node.clear_bake_scatter"
  bl_description = "Removes the baked images and reverts to the origional procedural node"
  bl_space_type = "NODE_EDITOR"
  bl_region_type = "UI"
  bl_options = {'REGISTER', 'UNDO'}

  @classmethod
  def poll(cls, context):
    return get_baked_sources(context.selected_nodes)

  def execute(self, context):
    # switching modes prevents context errors
    prev_mode = mode_toggle(context, 'OBJECT')
    clear_bake(context)
    mode_toggle(context, prev_mode)

    return {'FINISHED'}

def register():
  bpy.utils.register_class(NODE_OT_clear_baked_scatter)

def unregister():
  bpy.utils.unregister_class(NODE_OT_clear_baked_scatter)