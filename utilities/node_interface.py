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

def create_socket(node_tree, in_out, socket_type, name):
  if in_out == 'INPUT' and bpy.app.version < (4, 0, 0):
    new_socket = node_tree.inputs.new(socket_type, name)
  elif in_out == 'OUTPUT' and bpy.app.version < (4, 0, 0):
    new_socket = node_tree.outputs.new(socket_type, name)
  else:
    new_socket = node_tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
  return new_socket

def remove_socket(node_tree, in_out, name):
  if in_out == 'INPUT' and bpy.app.version < (4, 0, 0):
    node_tree.inputs.remove(node_tree.inputs[name])
  elif in_out == 'OUTPUT' and bpy.app.version < (4, 0, 0):
    node_tree.outputs.remove(node_tree.outputs[name])
  else:
    node_tree.interface.remove(node_tree.interface.items_tree[name])

def get_socket(node_tree, in_out, name):
  if in_out == 'INPUT' and bpy.app.version < (4, 0, 0):
    return node_tree.inputs[name]
  elif in_out == 'OUTPUT' and bpy.app.version < (4, 0, 0):
    return node_tree.outputs[name]
  else:
    return node_tree.interface.items_tree[name]

def get_io_sockets(node_tree, in_out):
  sockets = []
  if bpy.app.version < (4, 0, 0) and in_out == 'INPUT':
    sockets = node_tree.inputs
  elif bpy.app.version < (4, 0, 0) and in_out == 'OUTPUT':
    sockets = node_tree.outputs
  else:
    for item in node_tree.interface.items_tree:
        if item.item_type == 'SOCKET':
            if item.in_out == in_out:
              sockets.append(item)
  return sockets

def move_socket(node_tree, in_out, socket, to_idx):
  if bpy.app.version < (4, 0, 0):
    if in_out == 'INPUT':
      sockets = node_tree.inputs
    else:
      sockets = node_tree.outputs
    from_idx = 0
    for idx, soc in enumerate(sockets):
      if soc == socket:
        from_idx = idx
        print('found socket')
    sockets.move(from_idx, to_idx)
  else:
    node_tree.interface.move(socket, to_idx)

def set_socket_subtype(socket, subtype):
  if bpy.app.version >= (4, 0, 0):
    socket.subtype = subtype