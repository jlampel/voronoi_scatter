---
excerpt: Documentation for the Noise Mix function of the Scattershot add-on for Blender.
nav_order: 2
nav_exclude: false
search_exclude: false
---

# Noise Mix

The Noise Blend operator, also found in the Node menu and RMB context menu, allows you to instantly mix together any number of nodes with a noise pattern. The only option, Mix Outputs By, determines which outputs of the selected nodes get mixed together.

**Order** will blend all sockets together based on their socket number on the node. If one node has more sockets than the other, empty inputs will be created for those channels.

**Name** will mix outputs together based on their name and create a blank input if a node doesn't have an output of that name.

**Only Common Names** will mix only the outputs that all selected nodes have in common, such as Color or Fac. Nothing will happen and a warning will appear if the nodes have no outputs in common.

**Only First** will simply mix the first outputs of each node.