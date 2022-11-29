---
excerpt: Documentation for baking Scattershot's procedural results to image textures.
nav_order: 5
nav_exclude: false
search_exclude: false
---

# Baking

Scattershot includes an operator called Bake Scatter that allows you to bake your procedurally scattered results back to image textures so that you can export the final textures to a game engine or any other app. To bake, simply select one or more Scattershot nodes and choose Bake Scatter from the Scattershot menu.

## Objects

You can choose between baking just the selected object or all objects that share the same material (texture set).

## Channels

You can optionally bake any channel* that Scattershot outputs. Only displacement is enabled by default. If only displacement is chosen, you'll still have access to all of the procedural controls and can simply re-bake whenever you need to update the final displacement map. If more channels are chosen, the scatter node will collapse to just the baked results.

*Baking normal maps is not currently supported because Scattershot outputs object space normals whereas most apps require tangent space normals. I will work on converting them in a future update.

## UV Unwrapping

If your objects already have UV's, go ahead and turn the UV Unwrap option off. If enabled, it will unwrap and pack the objects for you before baking. There are a variety of projection options available, but Smart UV Project is usually suitable. A good amount of margin is automatically applied.

## Render Options

The Samples option determines how many Cycles samples are used for the bake. If you are not using any edge or tri-planar blending, you can get away with as little as 1 sample since there will be no noise to clear in the first place. Higher samples will result in a more crisp, clean result for the blending, but it's generally not necissary to use above 6 if you are using denoising.

Cycles does support denoising baked results, but the implementation is currently quite broken and according to the developers it requires major changes to be fixed. So, Scattershot denoises the baked result using the OpenImageDenoise compositing node. It works great and resolves the artifacts, but it is a bit slower. If you are not baking displacement, it may not be necissary.

## Output Preferences

The file type, name, and path for baked textures can be set in the add-on's preferences.

Use two forward slashes '//' at the beginning of the output folder's file path in order to make it relative the the current .blend file. If your file is not saved, the textures will end up in your TEMP directory.

The supported variables for the file name are listed below. Make sure to include the channel name somewhere, or the textures from different channels will overwrite each other.
- C = channel
- G = node group name
- L = node label
- M = material name
- N = node name

It's quite common (and suggested!) to use a higher quality format for displacement, bump, and normal maps than for regular textures like albedo and roughness maps. In the Scattershot preferences, you'll find options for the Color Format and the Data Format. The Color Format will be used for all regular textures and the Data Format will be used for all of the surface detail textures.
