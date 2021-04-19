import bpy
import os
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)

class NODE_OT_scatter(Operator):
    bl_label = "Voronoi Scatter"
    bl_idname = "node.scatter"
    bl_description = "Scatters image and procedural textures in one click"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    scatterMethod: bpy.props.EnumProperty(
        name = "Scatter Method",
        description = "Mapping type and scattering algorithm. Listed from fastest to slowest.",
        items = [
            ("uv_simple", "UV Simple", "Scatter based on UV coordinates without allowing overlap. Fastest Method"),
            ("uv_overlap", "UV Overlapping", "Scatter based on UV coordinates and allow cells to overlap neighbors"),
            ("tri-planar_simple", "Tri-Planar Simple", "Scatter based on generated object coordinates without allowing overlapping neigbors. No UVs needed but slower"),
            ("tri-planar_overlapping", "Tri-Planar Overlap", "Scatter based on generated object coordinates and allow overlapping neighbors. Extremely slow")
        ],
        default = "uv_simple", 
    )
    scatterGrouping: bpy.props.EnumProperty(
        name = "Grouping",
        description = "Scatter each texture individually, use the same settings for each, or randomly select one for each cell",
        items = [
            ("individual", "Individual", "Creates a unique scatter node for each image"),
            ("stacked", "Stacked", "Creates one scatter node that applies the same settings to each image. Useful for PBR setups"),
            ("interspersed", "Interspersed", "Creates one scatter node and randomly assigns images to each voronoi cell")
        ],
        default = "interspersed",  
    )
    textureInterpolation: bpy.props.EnumProperty(
        name = "Pixel Interpolation",
        description = "The pixel interpolation for each image",
        items = [
            ("Closest", "Closest", "Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee"),
            ("Cubic", "Cubic", "Pixels are smoothed but may cause artifacts between voronoi cells in Eevee")
        ],
        default = "Closest", 
    )
    useRandomCol: bpy.props.BoolProperty(
        name = "Random Color Options",
        description = "Adds easy controls for varying the color of each instance at a slight cost of render time",
        default = True,
    )
    useWarp: bpy.props.BoolProperty(
        name = "Warp Options",
        description = "Adds ability to distort the shape of each cell at a slight cost of render time",
        default = True,
    )

    @classmethod
    def poll(cls, context):
        nodes = bpy.context.active_object.data.materials[bpy.context.active_object.active_material_index].node_tree.nodes
        return [x for x in nodes if (x.select and x.type == 'TEX_IMAGE' and x.image)]

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = bpy.context.active_object
        slot = obj.active_material_index
        material = obj.data.materials[slot]
        nodes = material.node_tree.nodes
        selected_nodes = [x for x in nodes if (x.select and x.type == 'TEX_IMAGE')]

        def create_scatter_node(textures):
            scatter_node = nodes.new("ShaderNodeGroup")
            scatter_source = nodes.new("ShaderNodeGroup")
            # create friendly name 
            def sort_by_name(x):
                return x.image.name
            selected_nodes.sort(key=sort_by_name)
            file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tga']
            scatter_node_name = selected_nodes[0].image.name
            for t in file_types:
                if t in scatter_node_name:
                    scatter_node_name = scatter_node_name.replace(t, '') 
                
            path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'scatter_nodes.blend\\NodeTree\\')
            if self.scatterMethod == 'uv_overlap':
                bpy.ops.wm.append(filename='UV Scatter Overlapping', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['UV Scatter Overlapping'].copy()
                scatter_node.node_tree.name = scatter_node_name + " UV Scatter Overlapping"
                scatter_node.name = scatter_node_name + " UV Scatter Overlapping"
                scatter_node.label = scatter_node_name + " UV Scatter Overlapping"
            elif self.scatterMethod == 'uv_simple': 
                bpy.ops.wm.append(filename='UV Scatter Fast', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['UV Scatter Fast'].copy()
                scatter_node.node_tree.name = scatter_node_name + " UV Scatter Fast"
                scatter_node.name = scatter_node_name + " UV Scatter Fast"
                scatter_node.label = scatter_node_name + " UV Scatter Fast"
            elif self.scatterMethod == 'tri-planar_simple': 
                bpy.ops.wm.append(filename='Tri-Planar Scatter Fast', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['Tri-Planar Scatter Fast'].copy()
                scatter_node.node_tree.name = scatter_node_name + " Tri-Planar Scatter Fast"
                scatter_node.name = scatter_node_name + " Tri-Planar Scatter Fast"
                scatter_node.label = scatter_node_name + " Tri-Planar Scatter Fast"
            elif self.scatterMethod == 'tri-planar_overlap': 
                bpy.ops.wm.append(filename='Tri-Planar Scatter Overlapping', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['Tri-Planar Scatter Overlapping'].copy()
                scatter_node.node_tree.name = scatter_node_name + " Tri-Planar Scatter Overlapping"
                scatter_node.name = scatter_node_name + " Tri-Planar Scatter Overlapping"
                scatter_node.label = scatter_node_name + " Tri-Planar Scatter Overlapping"
            scatter_node.width = 250
            def average_loc():
                loc_x = sum([x.location[0] for x in textures]) / len(textures)
                loc_y = sum([x.location[1] for x in textures]) / len(textures) + 150
                return([loc_x, loc_y])
            scatter_node.location = average_loc()

            # remove optional components 
            if self.useRandomCol == False:
                random_col_node = scatter_node.node_tree.nodes["Randomize Colors"]
                scatter_node.node_tree.nodes.remove(random_col_node)
                scatter_node.node_tree.links.new(scatter_node.node_tree.nodes["Color Result"].outputs[0], scatter_node.node_tree.nodes["Color Output"].inputs[0])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Hue"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Saturation"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Value"])
            if self.useWarp == False:
                warp_node =  scatter_node.node_tree.nodes["Warp Coordinates"]
                scatter_node.node_tree.nodes.remove(warp_node)
                scatter_node.node_tree.links.new(scatter_node.node_tree.nodes["Scaled Coordinates"].outputs[0], scatter_node.node_tree.nodes["Warped Coordinates"].inputs[0])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Warp Amount"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Warp Scale"])

            # create scatter source 
            scatter_source.node_tree = bpy.data.node_groups['Scatter Source Empty'].copy()
            scatter_source.node_tree.name = "Scatter Source"
            scatter_source.name = "Scatter Source"
            scatter_source.label = "Scatter Source"

            # populate images      
            scatter_source_nodes = scatter_source.node_tree.nodes
            images = [scatter_source_nodes.new("ShaderNodeTexImage") for x in textures]
            multiply_nodes = []
            greater_nodes = []
            col_mix_nodes = []
            alpha_mix_nodes = []
            for x in range(len(images)):
                images[x].image = textures[x].image
                images[x].image.colorspace_settings.name = textures[x].image.colorspace_settings.name
                images[x].projection = 'FLAT'
                images[x].interpolation = self.textureInterpolation
                images[x].extension = 'CLIP'
                images[x].location = [x * 250, -x * 250]
                if x > 0:
                    multiply = scatter_source_nodes.new("ShaderNodeMath")
                    multiply.operation = 'MULTIPLY'
                    multiply.location = [(x * 250) + 350, (-x * 250) + 600]
                    multiply_nodes.append(multiply)
                    
                    greater = scatter_source_nodes.new("ShaderNodeMath")
                    greater.operation = 'GREATER_THAN'
                    greater.location = [(x * 250) + 350, (-x * 250) + 425]
                    greater_nodes.append(greater)
                    
                    col_mix = scatter_source_nodes.new("ShaderNodeMixRGB")
                    col_mix.location = [(x * 250) + 350, (-x * 250) + 250]
                    col_mix.hide = True
                    col_mix_nodes.append(col_mix)
                    
                    alpha_mix = scatter_source_nodes.new("ShaderNodeMixRGB")
                    alpha_mix.location = [(x * 250) + 350, (-x * 250) + 200]
                    alpha_mix.hide = True
                    alpha_mix_nodes.append(alpha_mix)
                    
            # connect the scatter source nodes
            scatter_links = scatter_source.node_tree.links
            for x in range(len(images)):
                scatter_source_nodes["Number of Images"].outputs[0].default_value = x + 1
                scatter_links.new(scatter_source_nodes["Group Input"].outputs[0], images[x].inputs[0])
                if x > 0:
                    scatter_links.new(scatter_source_nodes["Fraction"].outputs[0], multiply_nodes[x - 1].inputs[0])
                    multiply_nodes[x - 1].inputs[1].default_value = x
                    scatter_links.new(scatter_source_nodes["Group Input"].outputs[1], greater_nodes[x - 1].inputs[0])
                    scatter_links.new(multiply_nodes[x - 1].outputs[0], greater_nodes[x - 1].inputs[1])
                    scatter_links.new(greater_nodes[x - 1].outputs[0], col_mix_nodes[x - 1].inputs[0])
                    scatter_links.new(greater_nodes[x - 1].outputs[0], alpha_mix_nodes[x - 1].inputs[0])
                    if x == 1:
                        scatter_links.new(images[x - 1].outputs[0], col_mix_nodes[x - 1].inputs[1])
                        scatter_links.new(images[x - 1].outputs[1], alpha_mix_nodes[x - 1].inputs[1])
                    else: 
                        scatter_links.new(images[x - 1].outputs[0], col_mix_nodes[x - 2].inputs[2])
                        scatter_links.new(images[x - 1].outputs[1], alpha_mix_nodes[x - 2].inputs[2])
                        scatter_links.new(col_mix_nodes[x - 2].outputs[0], col_mix_nodes[x - 1].inputs[1])
                        scatter_links.new(alpha_mix_nodes[x - 2].outputs[0], alpha_mix_nodes[x - 1].inputs[1])
                    scatter_links.new(images[-1].outputs[0], col_mix_nodes[-1].inputs[2])
                    scatter_links.new(images[-1].outputs[1], alpha_mix_nodes[-1].inputs[2])
                    scatter_links.new(col_mix_nodes[-1].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                    scatter_links.new(alpha_mix_nodes[-1].outputs[0], scatter_source_nodes["Alpha Result"].inputs[0])
                elif x == 0:
                    scatter_links.new(images[0].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                    scatter_links.new(images[0].outputs[1], scatter_source_nodes["Alpha Result"].inputs[0])

            # replace scatter source in group node
            scatter_source_groups = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Source"]
            for x in scatter_source_groups:
                x.node_tree = scatter_source.node_tree
            nodes.remove(scatter_source)

        if self.scatterGrouping == 'interspersed':
            create_scatter_node(selected_nodes)
        elif self.scatterGrouping == 'individual':
            for n in selected_nodes:
                create_scatter_node([n])
        elif self.scatterGrouping == 'stacked':
            master_node = create_scatter_node([selected_nodes[0]])
            master_nodes =  master_node.node_tree.nodes
            removed_nodes = [x for x in  master_nodes if x.name != "Group Input" and x.name != "Group Output"]
            for n in removed_nodes:
                 master_nodes.remove(n)
            for x in master_node.node_tree.outputs:
                master_node.node_tree.outputs.remove(master_node.node_tree.outputs[x.name])
            for n in range(len(selected_nodes)):
                outer_node = create_scatter_node([selected_nodes[n]])
                inner_node = master_nodes.new("ShaderNodeGroup") 
                inner_node.node_tree = outer_node.node_tree
                inner_node.location = [-500, (n * 600)]
                nodes.remove(outer_node)
                for i in range(len(master_node.node_tree.inputs.items())):
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs[i], inner_node.inputs[i])
                master_node.node_tree.links.new(inner_node.outputs[0], master_nodes["Group Output"].inputs[-1])

        for texture in selected_nodes:
            nodes.remove(texture)

        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.separator()
    self.layout.operator(NODE_OT_scatter.bl_idname)
    
def register():
    bpy.utils.register_class(NODE_OT_scatter)
    bpy.types.NODE_MT_node.append(draw_menu)
    bpy.types.NODE_MT_context_menu.append(draw_menu)
    
def unregister():
    bpy.utils.unregister_class(NODE_OT_scatter)
    bpy.types.NODE_MT_node.remove(draw_menu)
    bpy.types.NODE_MT_context_menu.remove(draw_menu)
    
