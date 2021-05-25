import bpy
import os
import re
from bpy.types import (Operator)
from bpy.props import (BoolProperty, EnumProperty)

def create_friendly_name(x):
    name = x
    file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tga']
    albedo_names = ['albedo', 'base color', 'base_color', 'basecolor', 'base_col', 'color', 'diffuse', 'diff', 'col', 'd']
    metal_names = ['metal', 'metallic', 'metalness', 'm', 'met', 'mt']
    rough_names = ['roughness', 'rough', 'r', 'rgh']
    gloss_names = ['gloss', 'glossiness', 'gls']
    spec_names = ['spec', 'specular', 's']
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
        name = "Layering",
        description = "How the texture interacts with the background and the other scattered textures around it",
        items = [
            ("coordinates", "Just Coordinates", "Creates a scatter node that only outputs the scattered vectors for greater flexibility"),
            ("none", "None", "The texture is set to repeat to prevent gaps and all transparency settings are removed to improve performance"),
            ("blended", "Blended", "Creates a scatter node without transparency for each image and blends them together using a noise texture"),
            ("stacked", "Stacked", "Scatters each image using the same controls and creates an output for each. Useful for PBR setups without transparency"),
            ("simple", "Simple Alpha", "Adds ability to change the background, alpha clip threshold, and scatter density"),
            ("stacked_alpha", "Stacked Alpha", "Scatters each texture using the same controls and creates an output and a background input for each. Useful for PBR decals"),
            ("layered", "Layered Alpha", "Creates Simple scatter nodes for each texture and chains them all together, which is faster than using Overlapping"),
            ("overlapping", "Overlapping Alpha", "All the options of Simple Alpha with the additional benefit of enabling neighboring cells to overlap each other. This increases shader compilation time since 9 cells are calculated rather than 1")
        ],
        default = "none",
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
        layout.prop(self, "use_random_col")

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

            transparency = True
            if self.layering == 'none' or self.layering == 'blended' or self.layering == 'stacked':
                transparency = False
            
            if self.layering == 'overlapping':
                initial_nodetrees = set(bpy.data.node_groups)
                bpy.ops.wm.append(filename='SS - Scatter Overlapping', directory=path)
                appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
                appended_node = [x for x in appended_nodetrees if 'SS - Scatter Overlapping' in x.name][0]
                scatter_node.node_tree = bpy.data.node_groups[appended_node.name].copy()
                scatter_node.node_tree.name = "SS - Image Scatter Overlapping"
                scatter_node.label = "Scatter Overlapping"
            elif self.layering != 'overlapping': 
                initial_nodetrees = set(bpy.data.node_groups)
                bpy.ops.wm.append(filename='SS - Scatter Fast', directory=path)
                appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
                appended_node = [x for x in appended_nodetrees if 'SS - Scatter Fast' in x.name][0]
                scatter_node.node_tree = bpy.data.node_groups[appended_node.name].copy()
                scatter_node.node_tree.name = "SS - Image Scatter Fast"
                scatter_node.label = "Scatter Fast"

            scatter_node.width = 250
            def average_loc():
                loc_x = sum([x.location[0] for x in textures]) / len(textures)
                loc_y = sum([x.location[1] for x in textures]) / len(textures) + 150
                return([loc_x, loc_y])
            scatter_node.location = average_loc()
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

            if self.layering == 'stacked' or self.layering == 'stacked_alpha':
                scatter_node.node_tree.name = 'SS - Image Scatter Stacked'
                unsorted_textures = textures
                map_types = ['Albedo', 'Metallic', 'Roughness', 'Glossiness', 'Specular', 'Emission', 'Alpha', 'Bump', 'Normal']
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
                for x in range(len(scatter_sources)):
                    scatter_source = scatter_sources[x]
                    scatter_source.node_tree = bpy.data.node_groups['SS - Scatter Source Empty'].copy()
                    scatter_source.node_tree.name = "SS - Scatter Source"
                    scatter_source.label = "Scatter Source"
                    scatter_source.location = [-650, 200 + (-250 * x)]
                    scatter_source_nodes = scatter_source.node_tree.nodes

                    image = scatter_source_nodes.new("ShaderNodeTexImage")
                    image.image = sorted_textures[x].image
                    image.image.colorspace_settings.name = sorted_textures[x].image.colorspace_settings.name
                    image.interpolation = self.texture_interpolation
                    image.projection = 'FLAT'
                    if transparency:
                        image.extension = 'CLIP'
                    else:
                        image.extension = 'REPEAT'
                    image.location = [x * 250, -x * 250]
                    scatter_source.label = create_friendly_name(image.image.name)
                    nodes.remove(sorted_textures[x])

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
                            texture_type == 'Metallic' 
                            or texture_type == 'Roughness' 
                            or texture_type == 'Specular' 
                            or texture_type == 'Glossiness' 
                            or texture_type == 'Alpha'
                        ):
                            randomization = 'value'
                            randomize_value = scatter_nodes.new("ShaderNodeGroup")
                            randomize_value.node_tree = bpy.data.node_groups['SS - Randomize Value']
                            randomize_value.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
                            scatter_links.new(scatter_source.outputs[0], randomize_value.inputs[0])
                            scatter_links.new(scatter_coordiates.outputs[1], randomize_value.inputs[1])
                            group_input = scatter_node.node_tree.inputs.new('NodeSocketFloatFactor', "Random " + create_friendly_name(image.image.name))
                            group_input.min_value = 0
                            group_input.max_value = 1
                            scatter_links.new(scatter_nodes['Group Input'].outputs[-2], randomize_value.inputs[2])
                            randomize_value.inputs['Random Seed'].default_value = 1 + x
                            moving_from = -1
                            for input in scatter_node.node_tree.inputs:
                                moving_from += 1
                            moving_to = 13
                            scatter_node.node_tree.inputs.move(moving_from, moving_to)
                            scatter_links.new(randomize_value.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[x].name = texture_type
                        elif (
                            texture_type == 'Normal'
                            or texture_type == 'Bump'
                        ):
                            scatter_links.new(scatter_source.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[x].name = texture_type
                        else: 
                            randomization = 'hsv'
                            randomize_hsv = scatter_nodes.new("ShaderNodeGroup")
                            randomize_hsv.node_tree = bpy.data.node_groups['SS - Randomize HSV']
                            randomize_hsv.location = [scatter_source.location[0] + 250, scatter_source.location[1]]
                            scatter_links.new(scatter_source.outputs[0], randomize_hsv.inputs[0])
                            scatter_links.new(scatter_source.outputs[1], randomize_hsv.inputs[1])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Hue'], randomize_hsv.inputs['Random Hue'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Saturation'], randomize_hsv.inputs['Random Saturation'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Value'], randomize_hsv.inputs['Random Value'])
                            scatter_links.new(scatter_nodes['Group Input'].outputs['Random Seed'], randomize_hsv.inputs['Random Seed'])
                            scatter_links.new(randomize_hsv.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                            scatter_node.node_tree.outputs[x].name = texture_type
                    else:
                        scatter_links.new(scatter_source.outputs[0], scatter_nodes['Group Output'].inputs[-1])
                        scatter_node.node_tree.outputs[x].name = texture_type

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
                        elif texture_type == 'Bump':
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
                        scatter_links.new(alpha_over.outputs[0], scatter_nodes['Group Output'].inputs[x])
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
                scatter_source_links = scatter_source.node_tree.links
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
                    elif x == 0:
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
                if self.layering != 'stacked' and self.layering != 'stacked_alpha':
                    scatter_links.new(scatter_nodes["Color Output"].outputs[0], scatter_nodes["Group Output"].inputs[0])
            if self.projection_method == 'uv':
                scatter_nodes.remove(scatter_nodes["Tri-Planar Mapping"])
                scatter_node.node_tree.inputs.remove(scatter_node.node_tree.inputs["Tri-Planar Blending"])
                scatter_node.node_tree.links.new(scatter_nodes["Centered UVs"].outputs[0], scatter_nodes["Pattern Scale"].inputs[0])

            return scatter_node
        
        def create_stacked_scatter_node(textures): 
            master_node = create_scatter_node([textures[0]])
            master_nodes =  master_node.node_tree.nodes
            master_node.node_tree.name = "SS - Image Scatter Stacked"
            for n in [x for x in  master_nodes if x.name != "Group Input" and x.name != "Group Output"]:
                 master_nodes.remove(n)
            for x in master_node.node_tree.outputs:
                master_node.node_tree.outputs.remove(master_node.node_tree.outputs[x.name])

            unsorted_textures = textures
            map_types = ['Albedo', 'Metallic', 'Roughness', 'Glossiness', 'Emission', 'Bump', 'Normal']
            sorted_textures = []
            for map in map_types:
                for texture in unsorted_textures:
                    if create_friendly_name(texture.image.name) == map:
                        sorted_textures.append(texture)
            for texture in sorted_textures:
                unsorted_textures.remove(texture)
            for texture in unsorted_textures:
                sorted_textures.append(texture)

            inner_nodes = []
            for n in range(len(sorted_textures)):
                outer_node = create_scatter_node([sorted_textures[n]])
                inner_node = master_nodes.new("ShaderNodeGroup") 
                inner_nodes.append(inner_node)
                inner_node.node_tree = outer_node.node_tree
                nodes.remove(outer_node)
                inner_node.location = [-500, (n * 600)]
                inner_node.node_tree.outputs[0].name = create_friendly_name(sorted_textures[n].image.name)
                non_bg_inputs = [x for x in master_node.node_tree.inputs.items() if "Background" not in x[0]]
                for i in range(len(non_bg_inputs)):
                    master_node.node_tree.links.new(master_nodes["Group Input"].outputs[i], inner_node.inputs[i])
                if self.layering == 'stacked_alpha':
                    background_name = "Background " + create_friendly_name(sorted_textures[n].image.name)
                    if n == 0:
                        master_node.node_tree.links.new(master_nodes["Group Input"].outputs["Background"], inner_node.inputs["Background"])
                        master_node.node_tree.inputs["Background"].name = background_name
                    else:
                        inner_node.node_tree.inputs["Background"].name = background_name
                        master_node.node_tree.links.new(master_nodes["Group Input"].outputs[-1], inner_node.inputs[background_name])
                master_node.node_tree.links.new(inner_node.outputs[0], master_nodes["Group Output"].inputs[-1])
            master_node.node_tree.links.new(inner_nodes[-1].outputs["Random Color"], master_nodes["Group Output"].inputs[-1])
            for texture in sorted_textures:
                if texture:
                    print('Removing ' + texture.image.name)
                    nodes.remove(texture)

            return master_node

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

        if self.layering == 'coordinates':
            print("Still working on this feature")
        if self.layering == 'none':
            scatter_node = create_scatter_node(selected_nodes)
        elif self.layering == 'blended':
            scatter_node = create_scatter_node(selected_nodes)
        elif self.layering == 'stacked':
            scatter_node = create_scatter_node(selected_nodes)
        elif self.layering == 'simple':
            scatter_node = create_scatter_node(selected_nodes)
            scatter_node.inputs["Texture Scale"].default_value = 2
            scatter_node.inputs["Random Cell Shape"].default_value = 1
            scatter_node.inputs["Random Rotation"].default_value = 1
        elif self.layering == 'stacked_alpha':
            scatter_node = create_scatter_node(selected_nodes)
        elif self.layering == 'layered': 
            scatter_node = create_layered_transparency_node(selected_nodes)
            scatter_node.inputs["Texture Scale"].default_value = 2
            scatter_node.inputs["Random Cell Shape"].default_value = 1
            scatter_node.inputs["Random Rotation"].default_value = 1
        elif self.layering == 'overlapping':
            scatter_node = create_scatter_node(selected_nodes)
        
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
    
