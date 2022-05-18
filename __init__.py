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
    "version": (1, 6),
    "blender": (3, 1, 0),
    "location": "Shader Editor > Node",
    "description": "Quickly distributes image textures around your model with several controls for randomization",
    "warning": "",
    "wiki_url": "https://jlampel.github.io/voronoi_scatter/",
    "category": "Node",
}

import bpy, sys
from . import interface

def cleanse_modules():
    # Based on https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    for module_name in sorted(sys.modules.keys()):
        if module_name.startswith(__name__):
            del sys.modules[module_name]

def register():
    interface.register()

def unregister():
    interface.unregister()
    cleanse_modules()

if __name__ == "__main__":
    register()