---
excerpt: The changes made to Scattershot over time.
nav_order: 6
nav_exclude: false
search_exclude: false
---

# Changelog

## v1.9
- Fixed issue with noise blending due to API change in Blender 3.5
- Added ability to add textures while re-scattering
- Improved initial location of scatter node
- Automatically set transparent backgrounds based on selected Principled or Diffuse BSDF
- Fixed automatic connection to the material output node
- Fixed incorrect vectors when using Noise Blended scatter method
- Added HSV Noise as input rather than output when used on a shader
- Added purge for inner group nodes while unscattering to reduce clutter

## v1.8
- Fixed issues related to Blender new Mix Color node
- Bumped minimum supported version to Blender 3.4

## v1.7
- Improved PBR keyword detection
- Made the PBR keywords editable via the add-on's preferences
- Added operator for baking displacement maps
- Added operator to clear baked results
- Added support for AgX color management

## v1.6
- Updated documentation and switched to using GitHub Pages
- Fixed issue with socket colors reverting to yellow
- Moved operators to a sub-menu
- Added error message if missing node groups
- Added some node groups as assets for the asset browser

## v1.5
- Fixed compatibility issue with ACES color management

## v1.4
- Fixed normal map rotation limitations
- Added re-scattering of existing scatter nodes
- Introduced Noise HSV
- Grouped scatter node controls
- Fixed error when not in Object Mode