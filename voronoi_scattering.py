import bpy
import os
import re
from pprint import pprint
from bpy.types import (Object, Operator)
from bpy.props import (BoolProperty, EnumProperty)

from . import noise_blending
noise_blend = noise_blending.noise_blend

def append_node(nodes, node_tree_name):
    path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'scatter_nodes.blend\\NodeTree\\')
    node_group = nodes.new("ShaderNodeGroup")
    initial_nodetrees = set(bpy.data.node_groups)
    bpy.ops.wm.append(filename=node_tree_name, directory=path)
    appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
    appended_node = [x for x in appended_nodetrees if node_tree_name in x.name][0]
    node_group.node_tree = bpy.data.node_groups[appended_node.name].copy()
    node_group.node_tree.name = node_tree_name
    return node_group

def create_friendly_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']
    albedo_names = ['albedo', 'base color', 'base_color', 'basecolor', 'base_col', 'color', 'diffuse', 'diff', 'col', 'd']
    ao_names = ['ao', 'ambient_occlusion', 'ambient occlusion', 'occlusion']
    metal_names = ['metal', 'metallic', 'metalness', 'm', 'met', 'mt']
    rough_names = ['roughness', 'rough', 'r', 'rgh']
    gloss_names = ['gloss', 'glossiness', 'gls']
    spec_names = ['spec', 'specular', 's', 'refl', 'reflection']
    emit_names = ['emit', 'emission', 'emissive', 'glow', 'glw', 'e']
    alpha_names = ['alpha', 'transparent', 'transparency', 'opacity']
    normal_names = ['normal', 'nrm', 'n', 'nrlm']
    bump_names = ['bmp', 'bump', 'height', 'h', 'dp', 'displacement']
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    for word in re.split('[^a-z]', name.lower()):
        if word in albedo_names: 
            name = 'Albedo'
            break
        if word in ao_names: 
            name = 'AO'
            break
        elif word in metal_names: 
            name = 'Metallic'
            break
        elif word in rough_names:
            name = 'Roughness'
            break
        elif word in gloss_names:
            name = 'Glossiness'
            break
        elif word in spec_names:
            name = 'Specular'
            break
        elif word in emit_names:
            name = 'Emission'
            break
        elif word in alpha_names:
            name = 'Alpha'
            break
        elif word in normal_names:
            name = 'Normal'
            break
        elif word in bump_names:
            name = 'Bump'
            break
    return name 

def create_sortable_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']
    for t in file_types:
        if t in name:
            name = name.replace(t, '')
    all_words = re.split('[^\d\w]*[\(\)\_\-\s]', name.lower())
    without_spaces = []
    for word in all_words:
        if word == '':
            pass
        else: 
            without_spaces.append(word)
    name = without_spaces
    return name
   
class NODE_OT_scatter(Operator):
    bl_label = "Voronoi Scatter"
    bl_idname = "node.scatter"
    bl_description = "Scatters image and procedural textures in one click"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    projection_method: bpy.props.EnumProperty(
        name = "Mapping",
        description = "How the texture is projected onto the model. The performance difference is negligible",
        items = [
            ("uv", "UV", "Scatter based on UV coordinates"),
            ("tri-planar", "Tri-Planar", "Scatter based on generated object coordinates")
        ],
        default = "uv"
    )
    texture_interpolation: bpy.props.EnumProperty(
        name = "Pixel Interpolation",
        description = "The pixel interpolation for each image",
        items = [
            ("Closest", "Closest", "Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee"),
            ("Cubic", "Cubic", "Pixels are smoothed but may cause artifacts between voronoi cells in Eevee. Only recommended for Cycles")
        ],
        default = "Closest", 
    )
    layering: bpy.props.EnumProperty(
        name = "Scatter Method",
        description = "How the texture interacts with the background and the other scattered textures around it",
        items = [
            ("coordinates", "Just Coordinates", "Creates a scatter node that only outputs the scattered vectors for greater flexibility"),
            ("simple", "Interspersed", "A random texture is chosen per cell and each texture is set to repeat to prevent gaps and all transparency settings are removed to improve performance"),
            ("blended", "Noise Blended", "Each texture is scattered on its own and then they are all blended together using a noise texture"),
            ("stacked", "Stacked", "Scatters each image using the same controls and creates an output for each. Useful for PBR setups without transparency"),
            ("blended_stacked", "Noise Blended Stacked", "Stacks similarly named textures together and blends each texture set together using a noise texture. Great for scattering several sets of PBR textures. Supported naming conventions can be found in the documentation"),
            ("simple_alpha", "Interspersed Alpha", "A random texture is chosen per cell and adds ability to change the background, alpha clip threshold, and scatter density"),
            ("stacked_alpha", "Stacked Alpha", "Scatters each texture using the same controls and creates an output and a background input for each. Useful for PBR decals"),
            ("layered", "Layered Alpha", "Creates Interspersed Alpha scatter nodes for each texture and chains them all together, which allows for very a basic overlap that is faster than using Overlapping"),
            ("overlapping", "Overlapping Alpha", "All the options of Simple Alpha with the additional benefit of enabling neighboring cells to overlap each other. This increases shader compilation time since 9 cells are calculated rather than 1")
        ],
        default = "simple",
    )
    use_edge_blur: bpy.props.BoolProperty(
        name = "Enable Edge Blur",
        description = "Adds ability to blend the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures",
        default = True,
    )
    use_edge_warp: bpy.props.BoolProperty(
        name = "Enable Edge Warp",
        description = "Adds ability to distort the edges of each voronoi cell without distorting the texture. This helps seams between cells appear less obvious, especially for tileable textures",
        default = True,
    )
    use_texture_warp: bpy.props.BoolProperty(
        name = "Enable Texture Warp",
        description = "Adds ability to distort the shape of the resulting texture",
        default = False,
    )
    use_random_col: bpy.props.BoolProperty(
        name = "Enable Random Color",
        description = "Adds easy controls for varying the color of each instance",
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "projection_method", expand=True)
        layout.prop(self, "layering")
        layout.prop(self, "texture_interpolation")
        layout.prop(self, "use_edge_blur")
        layout.prop(self, "use_edge_warp")
        layout.prop(self, "use_texture_warp")
        random_col_row = layout.row()
        random_col_row.enabled = (self.layering != "coordinates")
        random_col_row.prop(self, "use_random_col")

    @classmethod
    def poll(cls, context):
        if context.selected_nodes:
            nodes = context.selected_nodes[0].id_data.nodes
            return [x for x in nodes if (x.select and x.type == 'TEX_IMAGE' and x.image)]
        else:
            return False
            
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_nodes = context.selected_nodes
        nodes = selected_nodes[0].id_data.nodes
        links = selected_nodes[0].id_data.links

        def create_scatter_node(textures):
            transparency = False
            if (
                self.layering == 'simple_alpha' or 
                self.layering == 'stacked_alpha' or 
                self.layering == 'layered' or 
                self.layering == 'overlapping'
            ):
                transparency = True
            # Import corresponding group node
            if self.layering == 'overlapping':
                scatter_node = append_node(nodes, 'SS - Scatter Overlapping')
                scatter_node.label = "Scatter Overlapping"
            elif self.layering != 'overlapping': 
                scatter_node = append_node(nodes, 'SS - Scatter Fast')
                scatter_node.label = "Scatter Fast"
            scatter_node.width = 250
            scatter_node.location = [
                sum([x.location[0] for x in textures]) / len(textures),
                sum([x.location[1] for x in textures]) / len(textures) + 150
            ]
            scatter_links = scatter_node.node_tree.links
            scatter_nodes = scatter_node.node_tree.nodes
            # replace voronoi coordinates in group node
            scatter_coordinates_groups = [x for x in scatter_nodes if x.label == "Scatter Coordinates"]
            new_scatter_coordinates = scatter_coordinates_groups[0].node_tree.copy()
            for x in scatter_coordinates_groups:
                x.node_tree = new_scatter_coordinates
            # create scatter sources 
            scatter_sources = []
            col_mix_nodes = []
            alpha_mix_nodes = []

            if self.layering == 'stacked' or self.layering == 'stacked_alpha' or self.layering == 'blended_stacked':
                scatter_node.node_tree.name = 'SS - Image Scatter Stacked'
                # For some reason, using 'unsorted_textures = textures' on the line below clears out 'textures' and 'selected_nodes'
                unsorted_textures = [x for x in textures]
                map_types = ['Albedo', 'AO', 'Metallic', 'Specular', 'Roughness', 'Glossiness', 'Emission', 'Alpha', 'Bump', 'Normal']
                sorted_textures = []
                for map in map_types:
                    for texture in unsorted_textures:
                        if create_friendly_name(texture.image.name) == map:
                            sorted_textures.append(texture)
                for texture in sorted_textures:
                    unsorted_textures.remove(texture)
                for texture in unsorted_textures:
                    sorted_textures.append(texture)

                scatter_node.node_tree.outputs.remove(scatter_node.node_tree.outputs['Image'])
                scatter_node.node_tree.outputs.remove(scatter_node.node_tree.outputs['Random Color'])
                for texture in sorted_textures:
                    scatter_sources.append(scatter_nodes.new("ShaderNodeGroup"))
                for scatter_source_idx in range(len(scatter_sources)):
                    scatter_source = scatter_sources[scatter_source_idx]
                    scatter_source.node_tree = bpy.data.node_groups['SS - Scatter Source Empty'].copy()
                    scatter_source.node_tree.name = "SS - Scatter Source"
                    scatter_source.label = "Scatter Source"
                    scatter_source.location = [-650, 200 + (-250 * scatter_source_idx)]
                    scatter_source_nodes = scatter_source.node_tree.nodes

                    image = scatter_source_nodes.new("ShaderNodeTexImage")
                    image.image = sorted_textures[scatter_source_idx].image
                    image.image.colorspace_settings.name = sorted_textures[scatter_source_idx].image.colorspace_settings.name
                    image.interpolation = self.texture_interpolation
                    image.projection = 'FLAT'
                    if transparency:
                        image.extension = 'CLIP'
                    else:
                        image.extension = 'REPEAT'
                    image.location = [scatter_source_idx * 250, -scatter_source_idx * 250]
                    scatter_source.label = create_friendly_name(image.image.name)

                    scatter_source_links = scatter_source.node_tree.links
                    scatter_source_links.new(scatter_source_nodes["Group Input"].outputs[0], image.inputs[0])
                    scatter_source_links.new(image.outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                    scatter_source_links.new(image.outputs[1], scatter_source_nodes["Alpha Result"].inputs[0])

                    scatter_coordiates = scatter_coordinates_groups[0]
                    scatter_links.new(scatter_coordiates.outputs["Vector"], scatter_source.inputs["Vector"])
                    scatter_links.new(scatter_coordiates.outputs["Color"], scatter_source.inputs["Random Color"])
                    scatter_links.new(scatter_nodes["Density Input"].outputs[0], scatter_source.inputs["Density"])
                    scatter_links.new(scatter_nodes["Group Input"].outputs["Alpha Clip"], scatter_source.inputs["Alpha Clip"])

                    randomization = 'none'
                    texture_type = create_friendly_name(image.image.name)
                    if self.use_random_col:
                        if (
                            texture_type == 'Roughness' 
                            or texture_type == 'Specular' 
                            or texture_type == 'Glossiness' 
                            or texture_type == 'Alpha'
                        ):
                            randomization = 'value'
                            randomize_value = append_node(scatter_nodes, 'SS - Randomize Value')
                            randomize_value.name = 'Randomize ' + texture_type
                            randomize_value.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
                            scatter_links.new(scatter_source.outputs[0], randomize_value.inputs[0])
                            scatter_links.new(scatter_coordiates.outputs[1], randomize_value.inputs[1])
                            group_input = scatter_node.node_tree.inputs.new('NodeSocketFloatFactor', "Random " + texture_type)
                            group_input.min_value = 0
                            group_input.max_value = 1
                            scatter_links.new(scatter_nodes['Group Input'].outputs[-2], randomize_value.inputs[2])
                            randomize_value.inputs['Random Seed'].default_value = 1 + scatter_source_idx
                            moving_from = -1
                            for input in scatter_node.node_tree.inputs:
                                moving_from += 1
                            moving_to = 13
                            scatter_node.node_tree.inputs.move(moving_from, moving_to)
                            scatter_links.new(randomize_value.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[scatter_source_idx].name = texture_type
                        elif (
                            texture_type == 'Normal'
                            or texture_type == 'Bump'
                            or texture_type == 'Metallic' 
                        ):
                            scatter_links.new(scatter_source.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[scatter_source_idx].name = texture_type
                        else: 
                            randomization = 'hsv'
                            randomize_hsv = scatter_nodes.new("ShaderNodeGroup")
                            randomize_hsv.name = 'Randomize ' + texture_type
                            randomize_hsv.node_tree = bpy.data.node_groups['SS - Randomize HSV']
                            randomize_hsv.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
                            scatter_links.new(scatter_source.outputs[0], randomize_hsv.inputs[0])
                            scatter_links.new(scatter_source.outputs[1], randomize_hsv.inputs[1])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Hue'], randomize_hsv.inputs['Random Hue'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Saturation'], randomize_hsv.inputs['Random Saturation'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Value'], randomize_hsv.inputs['Random Value'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Seed'], randomize_hsv.inputs['Random Seed'])
                            scatter_links.new(randomize_hsv.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[scatter_source_idx].name = texture_type
                    else:
                        scatter_links.new(scatter_source.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                        scatter_node.node_tree.outputs[scatter_source_idx].name = texture_type

                    if self.layering == 'stacked_alpha':
                        mix_bg_nodes = [x for x in scatter_nodes if (x.parent and "Mix Background" in x.parent.name) or "Mix Background" in x.name]
                        for node in mix_bg_nodes:
                            scatter_nodes.remove(node)
                        get_alpha = scatter_nodes.new('ShaderNodeMath')
                        get_alpha.operation = 'GREATER_THAN'
                        get_alpha.inputs[1].default_value = 0
                        get_alpha.location = [scatter_source.location[0] + 400, scatter_source.location[1]]
                        scatter_links.new(scatter_source.outputs[1], get_alpha.inputs[0])
                        alpha_over = scatter_nodes.new('ShaderNodeMixRGB')
                        alpha_over.blend_type = 'MIX'
                        alpha_over.location = [scatter_source.location[0] + 600, scatter_source.location[1]]
                        scatter_links.new(get_alpha.outputs[0], alpha_over.inputs[0])
                        # Create and connect inputs
                        scatter_links.new(scatter_nodes['Group Input'].outputs[-1], alpha_over.inputs[1])
                        scatter_node.node_tree.inputs[-1].name = texture_type + " Background"
                        if texture_type == 'Normal':
                            scatter_node.inputs[-1].default_value = [0.5, 0.5, 1, 1]
                        elif texture_type == 'Bump' or texture_type == 'Roughness':
                            scatter_node.inputs[-1].default_value = [0.5, 0.5, 0.5, 1]
                        else:
                            scatter_node.inputs[-1].default_value = [0, 0, 0, 1]
                        # Connect outputs 
                        if randomization == 'value':
                            scatter_links.new(randomize_value.outputs[0], alpha_over.inputs[2])
                        elif randomization == 'hsv':
                            scatter_links.new(randomize_hsv.outputs[0], alpha_over.inputs[2])
                        else: 
                            scatter_links.new(scatter_source.outputs[0], alpha_over.inputs[2])
                        scatter_links.new(alpha_over.outputs[0], scatter_nodes['Group Output'].inputs[scatter_source_idx])
                        scatter_node.width = 300

                scatter_nodes.remove(scatter_nodes["Scatter Source"])
                scatter_links.new(scatter_sources[0].outputs[1], scatter_nodes['Group Output'].inputs[-1])
                if self.use_random_col == True:
                    scatter_nodes.remove(scatter_nodes['SS - Randomize HSV'])
                    scatter_nodes.remove(scatter_nodes['Color Result'])
                    scatter_nodes.remove(scatter_nodes['Color Output'])
                    scatter_nodes.remove(scatter_nodes['Group Input Random Col'])
                if transparency == True:
                    scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs['Background'])

            else:
                # create scatter source
                scatter_source = nodes.new("ShaderNodeGroup")
                scatter_sources.append(scatter_source)
                scatter_source.node_tree = bpy.data.node_groups['SS - Scatter Source Empty'].copy()
                scatter_source.node_tree.name = "SS - Scatter Source"
                scatter_source.name = "Scatter Source"
                scatter_source.label = "Scatter Source"
                # populate images      
                scatter_source_nodes = scatter_source.node_tree.nodes
                scatter_source_links = scatter_source.node_tree.links
                images = [scatter_source_nodes.new("ShaderNodeTexImage") for x in textures]
                multiply_nodes = []
                greater_nodes = []
                for x in range(len(images)):
                    images[x].image = textures[x].image
                    images[x].image.colorspace_settings.name = textures[x].image.colorspace_settings.name
                    images[x].interpolation = self.texture_interpolation
                    images[x].projection = 'FLAT'
                    if transparency:
                        images[x].extension = 'CLIP'
                    else:
                        images[x].extension = 'REPEAT'
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
                for x in range(len(images)):
                    scatter_source_nodes["Number of Images"].outputs[0].default_value = x + 1
                    scatter_source_links.new(scatter_source_nodes["Group Input"].outputs[0], images[x].inputs[0])
                    if x > 0:
                        scatter_source_links.new(scatter_source_nodes["Fraction"].outputs[0], multiply_nodes[x - 1].inputs[0])
                        multiply_nodes[x - 1].inputs[1].default_value = x
                        scatter_source_links.new(scatter_source_nodes["Group Input"].outputs[1], greater_nodes[x - 1].inputs[0])
                        scatter_source_links.new(multiply_nodes[x - 1].outputs[0], greater_nodes[x - 1].inputs[1])
                        scatter_source_links.new(greater_nodes[x - 1].outputs[0], col_mix_nodes[x - 1].inputs[0])
                        scatter_source_links.new(greater_nodes[x - 1].outputs[0], alpha_mix_nodes[x - 1].inputs[0])
                        if x == 1:
                            scatter_source_links.new(images[x - 1].outputs[0], col_mix_nodes[x - 1].inputs[1])
                            scatter_source_links.new(images[x - 1].outputs[1], alpha_mix_nodes[x - 1].inputs[1])
                        else: 
                            scatter_source_links.new(images[x - 1].outputs[0], col_mix_nodes[x - 2].inputs[2])
                            scatter_source_links.new(images[x - 1].outputs[1], alpha_mix_nodes[x - 2].inputs[2])
                            scatter_source_links.new(col_mix_nodes[x - 2].outputs[0], col_mix_nodes[x - 1].inputs[1])
                            scatter_source_links.new(alpha_mix_nodes[x - 2].outputs[0], alpha_mix_nodes[x - 1].inputs[1])
                        scatter_source_links.new(images[-1].outputs[0], col_mix_nodes[-1].inputs[2])
                        scatter_source_links.new(images[-1].outputs[1], alpha_mix_nodes[-1].inputs[2])
                        scatter_source_links.new(col_mix_nodes[-1].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                        scatter_source_links.new(alpha_mix_nodes[-1].outputs[0], scatter_source_nodes["Alpha Result"].inputs[0])
                    else:
                        scatter_source_links.new(images[0].outputs[0], scatter_source_nodes["Color Result"].inputs[0])
                        scatter_source_links.new(images[0].outputs[1], scatter_source_nodes["Alpha Result"].inputs[0])
                
                scatter_source_groups = [x for x in scatter_nodes if x.label == "Scatter Source"]
                for x in scatter_source_groups:
                    x.node_tree = scatter_source.node_tree
                nodes.remove(scatter_source)
            
            # remove optional components 
            if self.use_random_col == False:
                random_col_nodes = [x for x in scatter_nodes if (x.parent and "Randomize HSV" in x.parent.name) or "Randomize HSV" in x.name]
                for node in random_col_nodes:
                    scatter_nodes.remove(node)
                scatter_nodes.remove(scatter_nodes['Group Input Random Col'])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Hue"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Saturation"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Random Value"])
                if self.layering != 'stacked' and self.layering != 'stacked_alpha':
                    scatter_node.node_tree.links.new(scatter_nodes["Color Result"].outputs[0], scatter_nodes["Color Output"].inputs[0])
            if self.use_texture_warp == False:
                warp_nodes = [x for x in scatter_nodes if (x.parent == scatter_nodes["Texture Warp"] or x.name == "Texture Warp")]
                for node in warp_nodes:
                    scatter_nodes.remove(node)
                scatter_node.node_tree.links.new(scatter_nodes["Scaled Coordinates"].outputs[0], scatter_nodes["Warped Coordinates"].inputs[0])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Texture Warp"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Texture Warp Scale"])
            if self.use_edge_warp == False:
                scatter_nodes.remove(scatter_nodes["Noise Texture"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Warp"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Warp Scale"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Warp Detail"])
                new_scatter_coordinates.inputs.remove(new_scatter_coordinates.inputs["Edge Warp"])
                new_scatter_coordinates.inputs.remove(new_scatter_coordinates.inputs["Edge Warp Noise"])
                new_scatter_coordinates.nodes.remove(new_scatter_coordinates.nodes["Edge Warp"])
                new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Edge Blur"].outputs[0], new_scatter_coordinates.nodes["Voronoi Texture"].inputs[0])
            if self.use_edge_blur == False:
                scatter_nodes.remove(scatter_nodes["White Noise Texture"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Edge Blur"])
                new_scatter_coordinates.inputs.remove(new_scatter_coordinates.inputs["Edge Blur"])
                new_scatter_coordinates.inputs.remove(new_scatter_coordinates.inputs["Edge Blur Noise"])
                new_scatter_coordinates.nodes.remove(new_scatter_coordinates.nodes["Edge Blur"])
                new_scatter_coordinates.nodes.remove(new_scatter_coordinates.nodes["Blur Range"])
                if self.use_edge_warp:
                    new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Shift Cells"].outputs[0], new_scatter_coordinates.nodes["Edge Warp"].inputs[1])
                else: 
                    new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Shift Cells"].outputs[0], new_scatter_coordinates.nodes["Voronoi Texture"].inputs[0])
            if self.layering != 'overlapping':
                new_scatter_coordinates.inputs.remove(new_scatter_coordinates.inputs["Shift"])
                new_scatter_coordinates.nodes.remove(new_scatter_coordinates.nodes["Shift Cells"])
                new_scatter_coordinates.nodes["Location Origin"].inputs[1].default_value = [0.5, 0.5, 0.5]
                new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Group Input"].outputs[0], new_scatter_coordinates.nodes["Subtract"].inputs[1])
                if self.use_edge_blur:
                    new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Group Input"].outputs[0], new_scatter_coordinates.nodes["Edge Blur"].inputs[1])
                elif self.use_edge_warp:
                    new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Group Input"].outputs[0], new_scatter_coordinates.nodes["Edge Warp"].inputs[1])
                else:
                    new_scatter_coordinates.links.new(new_scatter_coordinates.nodes["Group Input"].outputs[0], new_scatter_coordinates.nodes["Voronoi Texture"].inputs[0])
            if transparency == False:
                for node in scatter_source_nodes:
                    if node.parent and node.parent.name == "Transparency Options":
                        alpha_mix_nodes.append(node)
                for node in alpha_mix_nodes:
                    scatter_source_nodes.remove(node)
                scatter_source_nodes.remove(scatter_source_nodes["Transparency Options"])
                scatter_source_links.new(scatter_source_nodes["Group Input"].outputs["Random Color"], scatter_source_nodes["Group Output"].inputs["Random Color"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Density"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Alpha Clip"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Background"])
                mix_bg_nodes = [x for x in scatter_nodes if (x.parent and "Mix Background" in x.parent.name) or "Mix Background" in x.name]
                for node in mix_bg_nodes:
                    scatter_nodes.remove(node)
                if self.layering == 'simple' or self.layering == 'blended':
                    scatter_links.new(scatter_nodes["Color Output"].outputs[0], scatter_nodes["Group Output"].inputs[0])
            if self.projection_method == 'uv':
                scatter_nodes.remove(scatter_nodes["Tri-Planar Mapping"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Tri-Planar Blending"])
                scatter_node.node_tree.links.new(scatter_nodes["Centered UVs"].outputs[0], scatter_nodes["Pattern Scale"].inputs[0])
            return scatter_node
        
        def create_layered_transparency_node(textures):
            master_node = create_scatter_node([textures[0]])
            master_node.node_tree.name = 'SS - Image Scatter Layered'
            master_nodes =  master_node.node_tree.nodes
            master_inputs = [x for x in master_node.node_tree.inputs.items()]
            for n in [x for x in  master_nodes if x.name != "Group Input" and x.name != "Group Output"]:
                 master_nodes.remove(n)
            inner_nodes = []
            mix_nodes = []
            for n in range(len(textures)):
                outer_node = create_scatter_node([textures[n]])
                inner_node = master_nodes.new("ShaderNodeGroup")
                inner_nodes.append(inner_node)
                inner_node.node_tree = outer_node.node_tree
                nodes.remove(outer_node)
                inner_node.location = [-2300 + (n*500), 0]
                for i in range(len(master_inputs)):
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs[i], inner_node.inputs[i])
                if n > 0:
                    master_node.node_tree.links.new(inner_nodes[n - 1].outputs[0], inner_node.inputs['Background'])
                    seed = master_nodes.new("ShaderNodeMath")
                    seed.location = [inner_node.location[0] - 300, inner_node.location[1] - 500]
                    seed.operation = 'MULTIPLY'
                    seed.inputs[1].default_value = 1 / (n + 1)
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs['Random Seed'], seed.inputs[0])
                    master_node.node_tree.links.new(seed.outputs[0], inner_node.inputs['Random Seed'])
                    greater = master_nodes.new("ShaderNodeMath")
                    greater.operation = 'GREATER_THAN'
                    greater.inputs[1].default_value = 0.15
                    greater.location = [inner_node.location[0] + 250, inner_node.location[1] + 250]
                    master_node.node_tree.links.new(inner_node.outputs["Random Color"], greater.inputs[0])
                    mix = master_nodes.new("ShaderNodeMixRGB")
                    mix_nodes.append(mix)
                    mix.location = [inner_node.location[0] + 450, inner_node.location[1] + 250]
                    master_node.node_tree.links.new(greater.outputs[0], mix.inputs[0])
                    master_node.node_tree.links.new(inner_nodes[n].outputs["Random Color"], mix.inputs[2])
                    if n == 1:
                        master_node.node_tree.links.new(inner_nodes[n-1].outputs["Random Color"], mix.inputs[1])
                    else:
                        master_node.node_tree.links.new(mix_nodes[n-2].outputs[0], mix.inputs[1])
            master_node.node_tree.links.new(inner_nodes[-1].outputs[0], master_nodes["Group Output"].inputs[0])
            if mix_nodes:
                master_node.node_tree.links.new(mix_nodes[-1].outputs[0], master_nodes["Group Output"].inputs[1])
            else:
                master_node.node_tree.links.new(inner_nodes[-1].outputs[0], master_nodes["Group Output"].inputs[1])
            return master_node

        def create_coordinates_node(textures):
            scatter_node = append_node(nodes, 'SS - Scatter Mapping')
            scatter_node.label = "Scatter Mapping"
            scatter_node.width = 250
            scatter_node.location = [
                min([tex.location[0] for tex in textures]) - 350, 
                sum([x.location[1] for x in textures]) / len(textures) + 100
            ]
            for texture in textures:
                links.new(scatter_node.outputs[0], texture.inputs['Vector'])
                texture.interpolation = self.texture_interpolation
            texture_coordinates = nodes.new("ShaderNodeTexCoord")
            if self.projection_method == 'uv':
                texture_coordinates.location = [scatter_node.location[0] - 250, scatter_node.location[1] - 235]
                links.new(texture_coordinates.outputs['UV'], scatter_node.inputs['Vector'])
            else:
                tri_planar = append_node(nodes, 'SS - Tri-Planar Mapping')
                tri_planar.label = "Tri-Planar Mapping"
                tri_planar.width = 150
                tri_planar.location = [scatter_node.location[0] - 200, scatter_node.location[1] - 345]
                texture_coordinates.location = [scatter_node.location[0] - 400, scatter_node.location[1] - 235]
                links.new(texture_coordinates.outputs['Object'], tri_planar.inputs['Vector'])
                links.new(tri_planar.outputs['Vector'], scatter_node.inputs['Vector'])

        def group_similar_textures(selected_nodes):
            if self.layering == 'blended':
                sorted_textures = []
                for i in range(len(selected_nodes)):
                    sorted_textures.append([selected_nodes[i]])
                return sorted_textures
            elif self.layering == 'blended_stacked':
                unsorted_textures = selected_nodes
                sorted_textures = []
                for unsorted_texture_counter in range(len(unsorted_textures)):
                    if unsorted_texture_counter == 0:
                        sorted_textures.append( [unsorted_textures[unsorted_texture_counter]] )
                    else:
                        name1 = create_sortable_name(unsorted_textures[unsorted_texture_counter].image.name)              
                        has_match = False
                        for sorted_texture_counter in range(len(sorted_textures)):
                            name2 = create_sortable_name(sorted_textures[sorted_texture_counter][0].image.name)
                            similar_words = 0
                            for word_counter in range(len(name2)):
                                if len(name1) > word_counter:
                                    if name1[word_counter].isdigit():
                                        if float(name1[word_counter]) != float(name2[word_counter]):
                                            similar_words -= 1
                                    if name2[word_counter] == name1[word_counter]:
                                        similar_words += 1
                            if similar_words >= max([len(name2), len(name1)]) - 1:
                                sorted_textures[sorted_texture_counter].append(unsorted_textures[unsorted_texture_counter])
                                has_match = True
                                break
                        if has_match == False:
                            sorted_textures.append( [unsorted_textures[unsorted_texture_counter]] )
                return sorted_textures
        
        def create_blended_node(scattered_textures):
            scatter_nodes = scattered_textures
            master_node = scatter_nodes[0]
            master_node_links = master_node.node_tree.links
            master_node_nodes = master_node.node_tree.nodes
            scatter_coordinates = master_node_nodes['Scatter Coordinates']
            nodes_to_mix = []
            sockets_to_mix = {}
            for scatter_node_idx, scatter_node in enumerate(scatter_nodes):
                scatter_sources = [x for x in scatter_node.node_tree.nodes if x.type == 'GROUP' and 'SS - Scatter Source' in x.node_tree.name]
                for source_idx, source in enumerate(scatter_sources):
                    if not sockets_to_mix.get(source.label):
                        sockets_to_mix[source.label] = []
                    if scatter_node != master_node:
                        new_source = master_node.node_tree.nodes.new('ShaderNodeGroup')
                        nodes_to_mix.append(new_source)
                        new_source.node_tree = source.node_tree
                        new_source.label = source.label
                        new_source.node_tree.outputs['Color'].name = source.label
                        new_source.location = [-650, 85 - (500 * scatter_node_idx) - (250 * source_idx) - (100 * len(scatter_sources))]
                        master_node_links.new(scatter_coordinates.outputs["Vector"], new_source.inputs["Vector"])
                        master_node_links.new(scatter_coordinates.outputs["Color"], new_source.inputs["Random Color"])
                        if self.use_random_col:
                            # TODO This really shouldn't be written twice, so create a new function for use in both places
                            image = new_source.node_tree.nodes['Image Texture']
                            texture_type = create_friendly_name(image.image.name)
                            if (
                                texture_type == 'Roughness' 
                                or texture_type == 'Specular' 
                                or texture_type == 'Glossiness' 
                                or texture_type == 'Alpha'
                            ): 
                                randomize_node = append_node(master_node_nodes, 'SS - Randomize Value')
                                randomize_node.location = [new_source.location[0] + 250, new_source.location[1]]
                                randomize_node.inputs['Random Seed'].default_value = scatter_node_idx + 1
                                master_node_links.new(new_source.outputs[0], randomize_node.inputs[0])
                                master_node_links.new(scatter_coordinates.outputs["Color"], randomize_node.inputs["Random Color"])
                                master_node_links.new(master_node_nodes['Group Input'].outputs['Random ' + texture_type], randomize_node.inputs['Random Value'])
                                sockets_to_mix[new_source.label].append(randomize_node.outputs[0])
                            elif (
                                texture_type == 'Normal'
                                or texture_type == 'Bump'
                                or texture_type == 'Metallic' 
                            ):
                                sockets_to_mix[new_source.label].append(new_source.outputs[0])
                            else: 
                                randomize_node = master_node_nodes.new("ShaderNodeGroup")
                                randomize_node.node_tree = bpy.data.node_groups['SS - Randomize HSV']
                                randomize_node.location = [new_source.location[0] + 250, new_source.location[1]]
                                randomize_node.inputs['Random Seed'].default_value = scatter_node_idx + 1
                                master_node_links.new(new_source.outputs[0], randomize_node.inputs[0])
                                master_node_links.new(new_source.outputs[1], randomize_node.inputs[1])
                                master_node_links.new(master_node_nodes['Group Input'].outputs['Random Hue'], randomize_node.inputs['Random Hue'])
                                master_node_links.new(master_node_nodes['Group Input'].outputs['Random Saturation'], randomize_node.inputs['Random Saturation'])
                                master_node_links.new(master_node_nodes['Group Input'].outputs['Random Value'], randomize_node.inputs['Random Value'])
                                sockets_to_mix[new_source.label].append(randomize_node.outputs[0])
                        else:
                            sockets_to_mix[new_source.label].append(new_source.outputs[0])
                    else:
                        new_source = source
                        nodes_to_mix.append(source)
                        image = new_source.node_tree.nodes['Image Texture']
                        texture_type = create_friendly_name(image.image.name)
                        if (self.use_random_col and (
                            texture_type == 'Roughness' 
                            or texture_type == 'Specular' 
                            or texture_type == 'Glossiness' 
                            or texture_type == 'Alpha'
                            or texture_type == 'Albedo'
                            or texture_type == 'AO'
                            or texture_type == 'Emission'
                        )):
                            randomize_node = master_node_nodes['Randomize ' + texture_type]
                            sockets_to_mix[new_source.label].append(randomize_node.outputs[0])
                        else:
                            sockets_to_mix[new_source.label].append(new_source.outputs[0])

            blending_node = noise_blend(self, context, nodes_to_mix, sockets_to_mix, 'custom')
            blending_node.location[0] = 250
            output_names = [x.name for x in master_node_nodes['Group Output'].inputs]
            for channel_name in sockets_to_mix.keys():
                if channel_name not in output_names:
                    master_node.node_tree.outputs.new("NodeSocketColor", channel_name)
            for output in blending_node.outputs:
                master_node_links.new(output, master_node_nodes['Group Output'].inputs[output.name])
            input_names = ['Noise Scale', 'Noise Detail', 'Noise Roughness', 'Noise Blur']
            input_count = len(master_node.inputs)
            for input_name in input_names:
                master_node_links.new(master_node_nodes['Group Input'].outputs[-1], blending_node.inputs[input_name])
                master_node.node_tree.inputs[input_name].name = input_name.replace('Noise', 'Blending')
            for input_idx in range(len(input_names)):
                master_node.node_tree.inputs.move(input_count + input_idx, 1 + input_idx)
            master_node_links.new(master_node_nodes['Warped Coordinates'].outputs[0], blending_node.inputs['Vector'])

            for node in scatter_nodes:
                if node != master_node:
                    nodes.remove(node)
            return master_node
  
        if self.layering == 'coordinates':
            create_coordinates_node(selected_nodes)
        else:
            if (
                self.layering == 'simple'  or
                self.layering == 'stacked' or
                self.layering == 'stacked_alpha' or
                self.layering == 'overlapping'
            ):
                scatter_node = create_scatter_node(selected_nodes)
            elif (
                self.layering == 'blended' or
                self.layering == 'blended_stacked'
            ):
                node_sets = group_similar_textures(selected_nodes)
                scatter_nodes = [create_scatter_node(x) for x in node_sets]
                scatter_node = create_blended_node(scatter_nodes)
                if scatter_node:
                    scatter_node.node_tree.name = 'SS - Scatter Blended'
                else:
                    return {'CANCELLED'}
            elif self.layering == 'simple_alpha':
                scatter_node = create_scatter_node(selected_nodes)
                scatter_node.inputs["Texture Scale"].default_value = 2
                scatter_node.inputs["Random Cell Shape"].default_value = 1
                scatter_node.inputs["Random Rotation"].default_value = 1
            elif self.layering == 'layered': 
                scatter_node = create_layered_transparency_node(selected_nodes)
                scatter_node.inputs["Texture Scale"].default_value = 2
                scatter_node.inputs["Random Cell Shape"].default_value = 1
                scatter_node.inputs["Random Rotation"].default_value = 1
            else:
                self.report({"ERROR"}, "Cancelling Operation - Scatter method not recognized")
                return {'CANCELLED'}
            for texture in selected_nodes: nodes.remove(texture)

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
    
