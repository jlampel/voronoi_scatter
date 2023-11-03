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
from copy import copy
from .utilities.utilities import save_image

def denoise_image(context, image, format_settings):
  # Get current state
  prev_scene_name = copy(context.window.scene.name)
  prev_editor = {'area_type': context.area.type, 'ui_type': context.area.ui_type}

  # Create a new scene for compositing
  comp_scene = bpy.data.scenes.new('Temp Denoising Scene')
  context.window.scene = comp_scene
  context.area.ui_type = 'CompositorNodeTree'
  comp_scene.use_nodes = True
  comp_scene.render.resolution_x = image.size[0]
  comp_scene.render.resolution_y = image.size[1]
  camera_data = bpy.data.cameras.new('ScattershotTempCamera')
  camera = bpy.data.objects.new('ScattershotTempCamera', camera_data)
  context.scene.camera = camera

  # Composite image
  nodes = comp_scene.node_tree.nodes
  links = comp_scene.node_tree.links

  texture = nodes.new('CompositorNodeImage')
  texture.image = image
  denoise = nodes.new('CompositorNodeDenoise')
  links.new(texture.outputs[0], denoise.inputs[0])
  links.new(denoise.outputs[0], nodes['Composite'].inputs[0])

  # Save image
  bpy.ops.render.render()
  render = bpy.data.images['Render Result']
  render.filepath_raw = image.filepath_raw
  save_image(context, render, format_settings)
  image.source = 'FILE'
  image.reload()

  # Revert to previous state
  bpy.data.objects.remove(camera)
  bpy.data.cameras.remove(camera_data)
  bpy.data.scenes.remove(comp_scene)
  context.window.scene = bpy.data.scenes[prev_scene_name]
  context.area.type = prev_editor['area_type']
  context.area.ui_type = prev_editor['ui_type']

class IMAGE_OT_denoise_image(bpy.types.Operator):
  bl_label = "Denoise"
  bl_idname = "image.denoise"
  bl_description = "Denoises the image with the Intel OpenImageDenoise compositing node"
  bl_space_type = "IMAGE_EDITOR"
  bl_region_type = "UI"
  bl_options = {'REGISTER', 'UNDO'}

  overwrite: bpy.props.BoolProperty(
    name = 'Overwrite',
    description = 'Denoise the current image or save the result as a copy',
    default = False
  )

  def execute(self, context):
    format_settings = {}
    denoise_image(context, context.space_data.image, format_settings)
    return {'FINISHED'}

def register():
  bpy.utils.register_class(IMAGE_OT_denoise_image)

def unregister():
  bpy.utils.unregister_class(IMAGE_OT_denoise_image)