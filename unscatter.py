import bpy
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)

def get_scatter_nodes(selected_nodes):
    if selected_nodes:
        group_nodes = [x for x in selected_nodes[0].id_data.nodes if x.select and x.type == 'GROUP']
        def has_scatter_sources(node):
            scatter_sources = [x for x in node.node_tree.nodes if x.type == 'GROUP' and 'SS - Scatter Source' in x.node_tree.name]
            return scatter_sources
        return [x for x in group_nodes if has_scatter_sources(x)]
    else:
        return False

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
        return get_scatter_nodes(context.selected_nodes)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        nodes = selected_nodes[0].id_data.nodes
        selected_nodes = get_scatter_nodes(context.selected_nodes)

        for scatterNode in selected_nodes:
            scatter_sources = [x for x in scatterNode.node_tree.nodes if x.type == 'GROUP' and 'SS - Scatter Source' in x.node_tree.name]
            images_list = []
            image_count = 0
            columns = 0
            for x in range(len(scatter_sources)):
                scatter_source = scatter_sources[x]
                images = [x for x in scatter_source.node_tree.nodes if x.type == "TEX_IMAGE"]
                for i in range(len(images)):
                    image_count += 1
                    image = nodes.new("ShaderNodeTexImage")
                    images_list.append(image)
                    image.image = images[i].image
                    image.image.colorspace_settings.name = images[i].image.colorspace_settings.name
                    image.projection = self.projection
                    image.interpolation = self.interpolation
                    image.extension = self.extension
                    image.location = [scatterNode.location[0] + (250 * columns), scatterNode.location[1] - (255 * (image_count % 4))] 
                    if image_count % 4 == 0: columns += 1
            nodes.remove(scatterNode)
        
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
