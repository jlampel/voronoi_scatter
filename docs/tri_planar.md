---
excerpt: Documentation for the Tri-Planar Mapping function of the Scattershot add-on for Blender.
nav_order: 4
nav_exclude: false
search_exclude: false
---

# Tri-Planar Mapping

Scattershot's Tri-Planar Mapping operator allows you to use box mapping with any node that has a Vector input. I would recommend using Blender's box mapping if it's just for a basic image texture, but Scattershot's Tri-Planar mapping is useful for procedural textures and textures that need to be rotated. 

The Blending control uses a white noise texture under the hood, so you may need to increase your sample count in order to get a smooth result. Unfortunately, that means it can't play nice with displacement and you may see jagged edges around the blended area. 