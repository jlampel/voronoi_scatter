# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Scattershot - Voronoi Image Texture Scattering",
    "author": "Jonathan Lampel",
    "version": (1, 0),
    "blender": (2, 92, 0),
    "location": "Shader Editor > Node",
    "description": "Quickly distributes image textures around your model with several controls for randomization",
    "warning": "",
    "wiki_url": "",
    "category": "Node",
}

from . import voronoi_scattering, unscatter, noise_blending

def register():
    voronoi_scattering.register()
    unscatter.register()
    noise_blending.register()

def unregister():
    voronoi_scattering.unregister()
    unscatter.unregister()
    noise_blending.unregister()

if __name__ == "__main__":
    register()