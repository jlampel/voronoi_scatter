import bpy
import os
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)

def create_friendly_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tga']
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    return name 

class NODE_OT_scatter(Operator):
    bl_label = "Voronoi Scatter"
    bl_idname = "node.scatter"
    bl_description = "Scatters image and procedural textures in one click"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    scatter_method: bpy.props.EnumProperty(
        name = "Scatter Method",
        description = "Mapping type and scattering algorithm. Listed from fastest to slowest.",
        items = [
            ("uv_simple", "UV Simple", "Scatter based on UV coordinates without allowing overlap. Fastest Method"),
            ("box_simple", "Box Map Simple", "Scatter with the image set to box mapping. Much faster than tri-planar but without rotation or x scale control"),
            ("tri-planar_simple", "Tri-Planar Simple", "Scatter based on generated object coordinates without allowing overlapping neigbors. No UVs needed but slower"),
            ("uv_overlap", "UV Overlapping", "Scatter based on UV coordinates and allow cells to overlap neighbors. Much slower since it needs to calculate 9 cells rather than 1"),
            ("tri-planar_overlap", "Tri-Planar Overlap", "Scatter based on generated object coordinates and allow overlapping neighbors. Extremely slow since it needs to calcuate 9 cells x 3")
        ],
        default = "uv_simple", 
    )
    scatter_grouping: bpy.props.EnumProperty(
        name = "Grouping",
        description = "Scatter each texture individually or randomly select one for each cell",
        items = [
            ("individual", "Individual", "Creates a unique scatter node for each image"),
            # ("stacked", "Stacked", "Creates one scatter node that applies the same settings to each image. Useful for PBR setups"),
            ("interspersed", "Interspersed", "Creates one scatter node and randomly assigns images to each voronoi cell")
        ],
        default = "interspersed",  
    )
    texture_interpolation: bpy.props.EnumProperty(
        name = "Pixel Interpolation",
        description = "The pixel interpolation for each image",
        items = [
            ("Closest", "Closest", "Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee"),
            ("Cubic", "Cubic", "Pixels are smoothed but may cause artifacts between voronoi cells in Eevee")
        ],
        default = "Closest", 
    )
    texture_extrapolation: bpy.props.EnumProperty(
        name = "Image Extrapolation",
        description = "Sets whether or not the image repeats outside of its bounds",
        items = [
            ("CLIP", "Clip", "Does not repeat texture and sets outer pixels as transparent"),
            ("EXTEND", "Extend", "Repeats only the boundary pixels. Only useful is extremely specific circumstances"), 
            ("REPEAT", "Repeat", "Repeats the image indefinitely. Useful for scattering tiled textures over a terrain")
        ],
        default = "CLIP"
    )
    use_random_col: bpy.props.BoolProperty(
        name = "Random Color Options",
        description = "Adds easy controls for varying the color of each instance at a slight cost of render time",
        default = False,
    )
    use_edge_warp: bpy.props.BoolProperty(
        name = "Edge Warp Options",
        description = "Adds ability to distort the edges of each voronoi cell at a slight cost of render time",
        default = False,
    )
    use_texture_warp: bpy.props.BoolProperty(
        name = "Texture Warp Options",
        description = "Adds ability to distort the shape of the resulting texture at a slight cost of render time",
        default = False,
    )

    @classmethod
    def poll(cls, context):
        if context.selected_nodes:
            selected_nodes = context.selected_nodes
            nodes = selected_nodes[0].id_data.nodes
            return [x for x in nodes if (x.select and x.type == 'TEX_IMAGE' and x.image)]
        else:
            return False
            
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        nodes = selected_nodes[0].id_data.nodes

        def create_scatter_node(textures):
            path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'scatter_nodes.blend\\NodeTree\\')
            scatter_node = nodes.new("ShaderNodeGroup")
            scatter_source = nodes.new("ShaderNodeGroup")

            def sort_by_name(x):
                return x.image.name
            selected_nodes.sort(key=sort_by_name)
                
            if self.scatter_method == 'uv_overlap':
                bpy.ops.wm.append(filename='UV Scatter Overlapping', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['UV Scatter Overlapping'].copy()
                scatter_node.node_tree.name = "UV Image Scatter Overlapping"
                scatter_node.label = "UV Scatter Overlapping"
            elif self.scatter_method == 'uv_simple': 
                bpy.ops.wm.append(filename='UV Scatter Fast', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['UV Scatter Fast'].copy()
                scatter_node.node_tree.name = " UV Image Scatter Fast"
                scatter_node.label = "UV Scatter Fast"
            elif self.scatter_method == 'tri-planar_simple': 
                bpy.ops.wm.append(filename='Tri-Planar Scatter Fast', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['Tri-Planar Scatter Fast'].copy()
                scatter_node.node_tree.name = "Tri-Planar Image Scatter Fast"
                scatter_node.label = "Tri-Planar Scatter Fast"
            elif self.scatter_method == 'tri-planar_overlap': 
                bpy.ops.wm.append(filename='Tri-Planar Scatter Overlapping', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['Tri-Planar Scatter Overlapping'].copy()
                scatter_node.node_tree.name = "Tri-Planar Image Scatter Overlapping"
                scatter_node.label = "Tri-Planar Scatter Overlapping"
            elif self.scatter_method == 'box_simple': 
                bpy.ops.wm.append(filename='Box Mapping Scatter Fast', directory=path)
                scatter_node.node_tree = bpy.data.node_groups['Box Mapping Scatter Fast'].copy()
                scatter_node.node_tree.name = "Box Mapping Image Scatter Fast"
                scatter_node.label = "Box Mapping Scatter Fast"
            scatter_node.width = 250
            def average_loc():
                loc_x = sum([x.location[0] for x in textures]) / len(textures)
                loc_y = sum([x.location[1] for x in textures]) / len(textures) + 150
                return([loc_x, loc_y])
            scatter_node.location = average_loc()

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
                images[x].interpolation = self.texture_interpolation
                images[x].extension = self.texture_extrapolation
                images[x].location = [x * 250, -x * 250]
                if self.scatter_method == 'box_simple':
                    images[x].projection = 'BOX'
                    d = images[x].driver_add("projection_blend")
                    d.driver.expression = "var"
                    var = d.driver.variables.new()
                    var.targets[0].id_type = 'NODETREE'
                    var.targets[0].id = scatter_node.id_data
                    var.targets[0].data_path = 'nodes["' + scatter_node.name + '"]' + '.inputs["Box Map Blending"].default_value'
                else:
                    images[x].projection = 'FLAT'
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

            # replace scatter source and voronoi coordinates in group node
            scatter_source_groups = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Source"]
            for x in scatter_source_groups:
                x.node_tree = scatter_source.node_tree
            nodes.remove(scatter_source)
            scatter_coordinates_groups = [x for x in scatter_node.node_tree.nodes if x.label == "Scatter Coordinates"]
            new_scatter_coordinates = scatter_coordinates_groups[0].node_tree.copy()
            for x in scatter_coordinates_groups:
                x.node_tree = new_scatter_coordinates

            # remove optional components 
            if self.use_random_col == False:
                random_col_node = scatter_node.node_tree.nodes["Randomize Colors"]
                scatter_node.node_tree.nodes.remove(random_col_node)
                scatter_node.node_tree.links.new(scatter_node.node_tree.nodes["Color Result"].outputs[0], scatter_node.node_tree.nodes["Color Output"].inputs[0])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Hue"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Saturation"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Value"])
            if self.use_texture_warp == False:
                warp_node =  scatter_node.node_tree.nodes["Warp Coordinates"]
                scatter_node.node_tree.nodes.remove(warp_node)
                scatter_node.node_tree.links.new(scatter_node.node_tree.nodes["Scaled Coordinates"].outputs[0], scatter_node.node_tree.nodes["Warped Coordinates"].inputs[0])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Texture Warp"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Texture Warp Scale"])
            if self.use_edge_warp == False:
                scatter_node.node_tree.nodes.remove(scatter_node.node_tree.nodes["Noise Texture"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Warp"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Warp Scale"])
                coordinates_nodes = [x for x in scatter_node.node_tree.nodes if (x.type == 'GROUP' and x.label == "Scatter Coordinates")]
                coordinates_nodes[0].node_tree.inputs.remove(coordinates_nodes[0].node_tree.inputs["Edge Warp"])
                coordinates_nodes[0].node_tree.inputs.remove(coordinates_nodes[0].node_tree.inputs["Edge Warp Noise"])
                coordinates_nodes[0].node_tree.nodes.remove(coordinates_nodes[0].node_tree.nodes["Edge Warp"])
                coordinates_nodes[0].node_tree.links.new(coordinates_nodes[0].node_tree.nodes["Edge Blur"].outputs[0], coordinates_nodes[0].node_tree.nodes["Voronoi Texture"].inputs[0])
            if self.scatter_method == "uv_simple" or self.scatter_method == "tri-planar_simple":
                new_scatter_coordinates.nodes["Location Origin"].inputs[1].default_value = [0.5, 0.5, 0.5]
            return scatter_node
        
        def create_stacked_node(textures): 
            master_node = create_scatter_node([textures[0]])
            master_nodes =  master_node.node_tree.nodes
            for n in [x for x in  master_nodes if x.name != "Group Input" and x.name != "Group Output"]:
                 master_nodes.remove(n)
            for x in master_node.node_tree.outputs:
                master_node.node_tree.outputs.remove(master_node.node_tree.outputs[x.name])
            for n in range(len(textures)):
                outer_node = create_scatter_node([textures[n]])
                inner_node = master_nodes.new("ShaderNodeGroup") 
                inner_node.node_tree = outer_node.node_tree
                nodes.remove(outer_node)
                inner_node.location = [-500, (n * 600)]
                inner_node.node_tree.outputs[0].name = create_friendly_name(textures[n].image.name)

                non_bg_inputs = [x for x in master_node.node_tree.inputs.items() if "Background" not in x[0]]
                for i in range(len(non_bg_inputs)):
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs[i], inner_node.inputs[i])
                background_name = "Background " + create_friendly_name(textures[n].image.name)
                if n == 0:
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs["Background"], inner_node.inputs["Background"])
                    master_node.node_tree.inputs["Background"].name = background_name
                else:
                    inner_node.node_tree.inputs["Background"].name = background_name
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs[-1], inner_node.inputs[background_name])
                master_node.node_tree.links.new(inner_node.outputs[0], master_nodes["Group Output"].inputs[-1])

        if self.scatter_grouping == 'interspersed':
            create_scatter_node(selected_nodes)
        elif self.scatter_grouping == 'individual':
            for n in selected_nodes:
                create_scatter_node([n])
        elif self.scatter_grouping == 'stacked':
            create_stacked_node(selected_nodes)
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
    
