# These are the file extensions that get stripped out of the name when checking for a PBR texture
file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']

section_labels = ["Transformation", "Cell Randomization", "Texture Randomization", "Transparency"]

# Including any of the following words between separaters [' ', '-', '_'] will add the texture to the corresponding PBR channel
texture_names = {
    'albedo': ['albedo', 'base color', 'base_color', 'basecolor', 'base_col', 'color', 'diffuse', 'diff', 'col', 'd'],
    'ao': ['ao', 'ambient_occlusion', 'ambient occlusion', 'occlusion'],
    'metal': ['metal', 'metallic', 'metalness', 'm', 'met', 'mt'],
    'rough': ['roughness', 'rough', 'r', 'rgh'],
    'gloss': ['gloss', 'glossiness', 'gls'],
    'spec': ['spec', 'specular', 'spc', 'refl', 'reflection'],
    'emit': ['emit', 'emission', 'emissive', 'glow', 'glw', 'e'],
    'alpha': ['alpha', 'transparent', 'transparency', 'opacity'],
    'bump': ['bmp', 'bump', 'height', 'h', 'dp', 'disp', 'displacement'],
    'normal': ['normal', 'nrm', 'n', 'nrlm']
}

# Include any texture types that should only have their value adjusted and not their hue or saturation
value_channels = ['AO', 'Metallic', 'Specular', 'Roughness', 'Glossiness', 'Alpha', 'Bump']

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
        'Random Texture Location': 1,
    },
    'simple': {
        'Cell Scale': 2,
        'Random Cell Shape': 1,
        'Random Texture Location': 1,
    },
    'blended': {
        'Mix Noise Scale': 1,
        'Mix Noise Detail': 6,
        'Mix Noise Roughness': 0.75,
        'Mix Noise Blending': 0.25,
        'Cell Scale': 2,
        'Random Cell Shape': 1,
        'Random Texture Location': 1,
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