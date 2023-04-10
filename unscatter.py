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
import pprint
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)
from pprint import pprint
from . import defaults
from .utilities import get_scatter_sources, get_groups

def extract_images(self, selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    scatter_nodes = [x for x in selected_nodes if get_scatter_sources([x])]
    for scatter_node in scatter_nodes:
        inner_textures = []
        new_textures = []
        scatter_sources = get_scatter_sources([scatter_node])
        for scatter_source in scatter_sources:
            for node in scatter_source.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node not in inner_textures: inner_textures.append(node)
        columns = 0
        for image_idx, image in enumerate(inner_textures):
            new_image = nodes.new("ShaderNodeTexImage")
            new_textures.append(new_image)
            new_image.image = image.image
            new_image.image.colorspace_settings.name = image.image.colorspace_settings.name
            new_image.location = [scatter_node.location[0] + (250 * columns), scatter_node.location[1] - (285 * (image_idx % 4))]
            new_image.projection = self.projection
            new_image.interpolation = self.interpolation
            new_image.extension = self.extension
            if (image_idx + 1) % 4 == 0: columns += 1
        return new_textures
            
def remove_scatter_nodes(selected_nodes):
    nodes = selected_nodes[0].id_data.nodes
    trees_to_delete = []
    groups = get_groups(selected_nodes)
    trees_to_delete.extend(groups)

    for node in selected_nodes:
        if get_scatter_sources([node]):
            nodes.remove(node)

    for tree in [x.name for x in trees_to_delete]:
        if tree in [x.name for x in bpy.data.node_groups]:
            bpy.data.node_groups.remove(bpy.data.node_groups[tree])


class NODE_OT_unscatter(Operator):
    bl_label = "Un-Scatter"
    bl_idname = "node.unscatter"
    bl_description = "Reverses Voronoi Scatter"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

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

    @classmethod
    def poll(cls, context):
        if context.selected_nodes:
            return get_scatter_sources(context.selected_nodes)
        else:
            return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        extract_images(self, selected_nodes)
        remove_scatter_nodes(selected_nodes)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NODE_OT_unscatter)

def unregister():
    bpy.utils.unregister_class(NODE_OT_unscatter)
