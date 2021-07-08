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
    },
    'layered': {
        'Texture Scale': 2,
    },
    'overlapping': {
        'Texture Scale': 2,
    },
}