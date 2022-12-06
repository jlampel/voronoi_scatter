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


file_types = {
  'PNG': 'png',
  'JPEG': 'jpg',
  'OPEN_EXR': 'exr',
  'BMP': 'bmp',
  'TIFF': 'tif',
  'TARGA': 'tga'
}

section_labels = ["Transformation", "Cell Randomization", "Texture Randomization", "Transparency"]

# Including any of the following words between separaters [' ', '-', '_'] will add the texture to the corresponding PBR channel
texture_names = {
  'Albedo': ['albedo', 'base_color', 'basecolor', 'base_col', 'base', 'color', 'diffuse', 'diff', 'col', 'c', 'd'],
  'AO': ['ao', 'ambient_occlusion', 'ambient occlusion', 'occlusion', 'occ'],
  'Metalness': ['metal', 'metallic', 'metalness', 'm', 'met', 'mt', 'ml'],
  'Roughness': ['roughness', 'rough', 'r', 'rgh', 'rh'],
  'Glossiness': ['gloss', 'glossiness', 'gl', 'gls', 'g'],
  'Specular': ['spec', 'specular', 'sp', 'spc', 'refl', 'reflection', 'r', 's'],
  'Emission': ['emit', 'emission', 'emissive', 'glow', 'glw', 'em', 'e'],
  'Alpha': ['alpha', 'transparent', 'transparency', 'opacity', 'a'],
  'Bump': ['bmp', 'bump', 'b'],
  'Normal': ['normal', 'nrm', 'n', 'nrlm', 'nor'],
  'Displacement': ['d', 'dp', 'disp', 'displacement', 'height', 'h']
}

# Texture types that should only have their value adjusted and not their hue or saturation
data_channels = ['AO', 'Metallic', 'Specular', 'Roughness', 'Glossiness', 'Alpha', 'Bump', 'Displacement']
# Texture types that should be output at a higher bit depth
detail_channels = ['Bump', 'Displacement', 'Normal']

# Some custom builds of blender use other color spaces
data_color_spaces = ['Non-Color', 'Linear', 'Linear BT.709', 'Generic Data', 'Data']
default_view_transforms = ['Standard', 'Display Native']

# Defaults for the operators. Do not add or remove any of these.
scatter = {
  'projection_method': 'uv', # uv or tri-planar
  'texture_interpolation': 'Closest', # Closest or Cubic
  'layering': 'simple',   # coordinates, simple, blended, simple_alpha, layered, or overlapping
  'use_pbr': True,
  'use_edge_blur': True,
  'use_edge_warp': True,
  'use_texture_warp': False,
  'use_random_col': True,
  'use_noise_col': False,
  'use_manage_col': True
}
unscatter = {
  'interpolation': 'Linear', # Linear, Closest, Cubic, or Smart
  'projection': 'FLAT', # FLAT, BOX, SPHERE, or TUBE
  'extension': 'REPEAT',  # REPEAT, CLIP, or EXTEND
}
noise_blend = {
  'mix_by': 'common_name', # order, name, common_name, or first
}

# Default values for the scatter node inputs on creation.
# You can add or remove any settings that you find on a scatter node
layering = {
  'common': {
    'Tri-Planar Blending': 0.15,
    'Random Cell Hue': 0.1,
    'Random Cell Saturation': 0.1,
    'Random Cell Value': 0.1,
    'Random Texture Rotation': 1,
    'Random Texture Scale': 0.25,
    'Edge Warp': 0.5,
    'Edge Warp Scale': 1,
    'Edge Warp Detail': 3,
    'Texture Warp': 0.5,
    'Cell Blending': 0.25
  },
  'coordinates': {
    'Cell Scale': 2,
    'Random Cell Shape': 1,
    'Random Texture Location X': 1,
    'Random Texture Location Y': 1,
  },
  'simple': {
    'Cell Scale': 2,
    'Random Cell Shape': 1,
    'Random Texture Location X': 1,
    'Random Texture Location Y': 1,
  },
  'blended': {
    'Mix Noise Scale': 1,
    'Mix Noise Detail': 6,
    'Mix Noise Roughness': 0.75,
    'Mix Noise Blending': 0.25,
    'Cell Scale': 2,
    'Random Cell Shape': 1,
    'Random Texture Location X': 1,
    'Random Texture Location Y': 1,
  },
  'simple_alpha': {
    'Texture Scale': 2,
    'Random Cell Shape': 1,
  },
  'layered': {
    'Texture Scale': 2,
    'Random Cell Shape': 1,
    'Edge Warp': 0,
  },
  'overlapping': {
    'Texture Scale': 2,
    'Random Texture Location': 0.5
  },
}

# Node names
node_names = {
  "tri-planar": "Tri-Planar Mapping",
  "uv_normal_map": "UV Normal Map",
  "tri-planar_normal_map": "Tri-Planar Normal Map",
  "scatter_vectors": "Scatter Vectors",
  "vector_default": "Vector Default",
  "scatter": "Scattershot",
  "scatter_overlapping": "Scatter Overlapping",
  "randomize_cell_hsv": "Randomize Cell HSV",
  "randomize_noise_hsv": "Noise Randomize HSV",
  "randomize_cell_value": "Randomize Cell Value",
  "randomize_noise_value": "Noise Randomize Value",
  "scatter_coordinates": "Scatter Voronoi Coordinates",
  "scatter_source": "Scatter Source",
  "scatter_source_empty": "Scatter Source Empty",
  "scatter_layered": "Scatter Layered"
}