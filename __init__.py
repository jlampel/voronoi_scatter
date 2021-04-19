bl_info = {
    "name": "Voronoi Texture Scattering",
    "author": "Jonathan Lampel",
    "version": (1, 0),
    "blender": (2, 92, 0),
    "location": "Shader Editor > Node",
    "description": "Scatters image and procedural textures in one click",
    "warning": "",
    "wiki_url": "",
    "category": "Node",
}

from . import voronoi_scattering, unscatter

def register():
    voronoi_scattering.register()
    unscatter.register()

def unregister():
    voronoi_scattering.unregister()
    unscatter.unregister()

if __name__ == "__main__":
    register()