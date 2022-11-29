from copy import copy
import bpy, mathutils

def unwrap(self, context, objects):
  context.area.type = "VIEW_3D"
  context.area.ui_type = "VIEW_3D"

  margin_percent = 0.025

  # Unwraps each object individually
  for obj in objects:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')

    uvs = obj.data.uv_layers
    if 'ScattershotUVs' in [x.name for x in obj.data.uv_layers]:
      uvs.active = obj.data.uv_layers["ScattershotUVs"]
    else:
      uvs.active = uvs.new(name="ScattershotUVs", do_init=True)

    if self.unwrap_method == 'smart':
      bpy.ops.uv.smart_project(angle_limit = self.smart_project_angle, island_margin = margin_percent)
    elif self.unwrap_method =='cube':
      bpy.ops.uv.cube_project()
    elif self.unwrap_method =='cylinder':
      bpy.ops.uv.cylinder_project(direction = 'ALIGN_TO_OBJECT')
    elif self.unwrap_method =='sphere':
      bpy.ops.uv.sphere_project(direction = 'ALIGN_TO_OBJECT')
    else:
      initial_rotation_mode = copy(obj.rotation_mode)
      initial_euler = copy(obj.rotation_euler)
      initial_quaternion = copy(obj.rotation_quaternion)
      obj.rotation_mode = 'XYZ'

      top_view = mathutils.Quaternion((1, 0, 0, 0))
      front_view = mathutils.Quaternion((0.707107, 0.707107, 0, 0))
      side_view = mathutils.Quaternion((0.707107, 0, 0.707107, 0))

      if self.unwrap_method =='top':
        obj.rotation_euler = [0, 0, 0]
        context.area.spaces[0].region_3d.view_rotation = top_view
      elif self.unwrap_method =='front':
        obj.rotation_euler = [-1.5708, 0, 0]
        context.area.spaces[0].region_3d.view_rotation = top_view
      elif self.unwrap_method =='side':
        obj.rotation_euler = [0, -1.5708, 0]
        context.area.spaces[0].region_3d.view_rotation = top_view
      elif self.unwrap_method =='x':
        context.area.spaces[0].region_3d.view_rotation = side_view
      elif self.unwrap_method =='y':
        context.area.spaces[0].region_3d.view_rotation = front_view
      else:
        context.area.spaces[0].region_3d.view_rotation = top_view
      context.area.spaces[0].region_3d.update()

      # This operator needs to run in the 'WINDOW' region, wich is usually regions[5] but not always. No idea why.
      with context.temp_override(region = context.area.regions[len(context.area.regions) - 1]):
        bpy.ops.uv.project_from_view(orthographic=True)

      obj.rotation_euler = initial_euler
      obj.rotation_quaternion = initial_quaternion
      obj.rotation_mode = initial_rotation_mode

    bpy.ops.object.editmode_toggle()

  # Packs all objects together
  for obj in objects:
    obj.select_set(True)
  if self.apply_scale:
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

  bpy.ops.object.editmode_toggle()
  bpy.ops.mesh.select_all(action='SELECT')
  context.area.type = "IMAGE_EDITOR"
  context.area.ui_type = "UV"
  bpy.ops.uv.select_all(action='SELECT')
  bpy.ops.uv.average_islands_scale()
  bpy.ops.uv.pack_islands(margin=margin_percent)

  # Returns to Shader Editor and Object mode
  context.area.ui_type = "ShaderNodeTree"
  bpy.ops.object.editmode_toggle()
