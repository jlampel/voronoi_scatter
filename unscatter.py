import bpy
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)

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
        default = "Linear",
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
        default="FLAT"
    )
    extension: bpy.props.EnumProperty(
        name="Extension",
        description="How the image is extrapolated beyond its origional bounds",
        items=[
            ("REPEAT", "Repeat", "Repeats texture horizontally and vertically"),
            ("CLIP", "Clip", "Sets pixels outside of texture as transparent"),
            ("EXTEND", "Extend", "Repeats only the boundary pixels of the texture")
        ],
        default="REPEAT"
    )

    @classmethod
    def poll(cls, context):
        nodes = bpy.context.active_object.data.materials[bpy.context.active_object.active_material_index].node_tree.nodes
        def checkImages():
            pass
        return [x for x in nodes if (x.select and x.type == 'GROUP' and x.node_tree.nodes["Color Result"])]

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = bpy.context.active_object
        slot = obj.active_material_index
        material = obj.data.materials[slot]
        nodes = material.node_tree.nodes
        selected_nodes = [x for x in nodes if (x.select and x.type == 'GROUP' and x.node_tree.nodes["Color Result"])]

        for scatter_node in selected_nodes:
            scatter_sources = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Source"]
            scatter_source = scatter_sources[0]
            images = [x for x in scatter_source.node_tree.nodes if x.type == "TEX_IMAGE"]
            for i in range(len(images)):
                image = nodes.new("ShaderNodeTexImage")
                image.image = images[i].image
                image.image.colorspace_settings.name = images[i].image.colorspace_settings.name
                image.projection = self.projection
                image.interpolation = self.interpolation
                image.extension = self.extension
                image.location = [scatter_node.location[0], scatter_node.location[1] - (255 * i)] 
            nodes.remove(scatter_node)
        
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(NODE_OT_unscatter.bl_idname)
    
def register():
    bpy.utils.register_class(NODE_OT_unscatter)
    bpy.types.NODE_MT_node.append(draw_menu)
    bpy.types.NODE_MT_context_menu.append(draw_menu)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_unscatter)
    bpy.types.NODE_MT_node.remove(draw_menu)
    bpy.types.NODE_MT_context_menu.remove(draw_menu)
