# These are the file extensions that get stripped out of the name when checking for a PBR texture
file_types = ['.png', '.jpg', '.exr', '.bmp', '.tff', '.tif', '.tga']

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
    'normal': ['normal', 'nrm', 'n', 'nrlm'],
    'bump': ['bmp', 'bump', 'height', 'h', 'dp', 'displacement']
}

# Defaults for the operators 
scatter = {
    'projection_method': 'uv',
    'texture_interpolation': 'Closest',
    'layering': 'simple',
    'use_edge_blur': True,
    'use_edge_warp': True,
    'use_texture_warp': False,
    'use_random_col': True,
    'use_pbr': False,
}
unscatter = {
    'interpolation': 'Linear',
    'projection': 'FLAT',
    'extension': 'REPEAT',
}
noise_blend = {
    'mix_by': 'common_name',
}

# Default values for the scatter node inputs on creation
layering = {
    'common': {
        'Tri-Planar Blending': 0.15,
        'Random Hue': 0.1,
        'Random Saturation': 0.1,
        'Random Value': 0.1,
        'Random Rotation': 1,
        'Random Scale': 0.25,
        'Edge Warp': 0.5,
        'Edge Warp Scale': 1,
        'Edge Warp Detail': 3,
        'Texture Warp': 0.5,
        'Edge Blur': 0.25
    },
    'coordinates': {
        'Cell Scale': 2,
        'Random Cell Shape': 1,
        'Random Location': 1,
    },
    'simple': {
        'Cell Scale': 2,
        'Random Cell Shape': 1,
        'Random Location': 1,
    },
    'blended': {
        'Blending Scale': 1,
        'Blending Detail': 6,
        'Blending Roughness': 0.75,
        'Blending Blur': 0.25,
        'Cell Scale': 2,
        'Random Cell Shape': 1,
        'Random Location': 1,
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
        'Random Location': 0.5
    },
}