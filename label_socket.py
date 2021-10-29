import bpy
from bpy.types import NodeTree, Node, NodeSocket
# Currently only for reference - the virutal socket type worked just fine here 
class LabelSocket(NodeSocket):
    '''Socket type for lables where the socket itself is invisible'''
    bl_idname: 'LabelSocket'
    bl_label = "Label Socket"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.15, 0.15, 0.15, 0.0)

def register():
    from bpy.utils import register_class
    register_class(LabelSocket)
def unregister():
    from bpy.utils import unregister_class
    unregister_class(LabelSocket)
if __name__ == "__main__":
    register()