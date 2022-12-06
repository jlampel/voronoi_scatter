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
from bpy.types import NodeTree, Node, NodeSocket
# Currently only for reference - the virutal socket type worked just fine here 
class LabelSocket(NodeSocket):
    '''Socket type for lables where the socket itself is invisible'''
    bl_idname: 'LabelSocket'
    bl_label = "Label Socket"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.15, 0.15, 0.15, 0.0)

def register():
    from bpy.utils import register_class
    register_class(LabelSocket)
def unregister():
    from bpy.utils import unregister_class
    unregister_class(LabelSocket)
if __name__ == "__main__":
    register()