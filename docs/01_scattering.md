---
excerpt: Documentation for the Voronoi Scatter function of the Scattershot add-on for Blender.
nav_order: 1
nav_exclude: false
search_exclude: false
---

# Scatter Images

Once you install the Scattershot addon, you'll find a new operator called Scatter Images in the Node menu of the Shader Editor. To access it more quickly, right quick and add it to your quick favorites (Q) menu or use the right click context menu.

You must have one or more image textures selected in order to use the Scatter Images command. The tooltips for the settings are pretty descriptive, so hover your mouse over each button if you forget what it does. Click 'OK' and your textures will be converted into a scatter node.

You can include a Principled BSDF in your selection while scattering if you would like the resulting scatter node to be automatically hooked up.

## Re-scatter

If you would like to change your scatter node's settings after the fact, such as to switch from UV to tri-planar mapping, select just the scatter node and run the Scatter Images operator again.

## Un-scatter

To reverse the process, you can always select the scatter node and use the Un-Scatter command that is in the Node menu or in the right click context menu.

## Mapping

The scattering can be done according to your object's UVs or it can be projected from all sides with tri-planar mapping. Tri-planar projection is the same thing as box mapping, but Scattershot uses a custom implementation instead of Blender's box mapping because it allows for important options like random rotation (you can't rotate a box mapped texture) and correcting the aspect ratio of non-square textures.

The impact on performance between the UV and Tri-Planar options is negligible since the image is not duplicated to achieve the effect. The Tri-Planar's Blending control uses a white noise texture under the hood, so you may need to increase your sample count in order to get a smooth result. Unfortunately, that means it can't play nice with displacement and you may see jagged edges around the blended area.

## Scatter Methods

This setting has the biggest impact on performance and changes several things about the setup, including transparency.

**Just Coordinates** does not move or replace the texture like the other methods and instead attaches a scattered vector coordinates node to it. This is useful for advanced users who want to customize their setups or scatter procedural textures. The Random Color and PBR options are disabled because no mixing is done after the image texture.

**Interspersed** picks a random texture or texture set for each voronoi cell. It does not have transparency and sets the image texture's extension to Repeat so that you will never have gaps in the result. This is useful for scattering one or two textures across a terrain or scattering a couple grunge masks together.

**Noise Mixed** does not choose a random texture per cell and instead scatters each texture individually and then blends them all together at the end using the Noise Blend operator (more on that below). This produces a much more natural pattern than Interspersed if working with many images. This method is perfect for scattering several sets of PBR textures together (more on PBR below).

**Interspersed Alpha** picks a random texture or texture set per cell just like Interspersed but supports transparency. The image texture's extension will be set to clip and you will be given controls for the background color, the alpha clip threshold, and the density.

**Layered Alpha** is the fastest way to get textures to overlap. It simply creates an Interspersed Alpha scatter node for each texture or texture set and chains them all together inside one parent scatter node. This creates a layering effect where the first texture set gets overlapped by the second, which gets overlapped by the third, and so on.

**Overlapping Alpha** enables textures to actually overlap their immediate neighbors. This allows for great looking results and appears much more randomized than Layered Alpha because the same texture set will not always be on top and the distribution is much more controllable, but it comes at the cost of shader compilation time since each image setup is duplicated eight times in order for each surrounding cell to be checked. This method works best when leaving the Random Cell Shape at 0 and increasing the Random Location instead. Also, Cycles has a hard texture limit, so it is not recommended to use this option with more than four images. If you can, try using the Layered Alpha option instead.

## Pixel Interpolation

This option sets how Cycles and Eevee blends between each pixel of the image.

**Closest** - Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee.

**Cubic** - Pixels are smoothed but may cause artifacts between voronoi cells in Eevee. Only recommended for Cycles.

## Detect PBR Channels

Check this on when working with PBR texture sets and Scattershot will automatically group the textures together and create an output for each channel. To be recognized as a PBR texture, the name of the image must have a word that indicates which channel it should be a part of, surrounded by a separator like a space, dash, or underline. File extensions and numbers will be stripped out and capitalization does not matter.

Examples:
- red-rock_color.exr
- window-rough.png
- dirt_NRM.exr

The full list of accepted terms can be found (and changed!) in the file defaults.py.

The PBR output sockets are correctly colored according to their data type. 

If you scatter a normal map, the Normal output will be a purple vector socket and not a yellow color socket, indicating that it can be plugged directly into a shader and should not be run through a normal map node. 

## Cell Blending

This option enables an option that mixes in white noise to the voronoi coordinates so that the boundaries between cells appears to blur without blurring the texture. This is incredibly helpful for hiding seams. The quality of this blending depends on the number of samples in both Eevee and Cycles. Because it uses white noise, it will cause displacement textures to appear jagged. The solution, if you need to use both edge blur and displacement textures, is to bake the displacement map before your final render, which will smooth everything out.

## Cell Warping

Cell Warping is another way to disguise seams. It enables an option to distort the shape of each voronoi cell. Without straight lines, it's much harder for the viewer's eyes to pick out where the boundaries are.

## Texture Warping

This applies a noise to the resulting texture coordinates, so that each instance of the texture appears to have a slightly different shape.

## Cell HSV

This enables controls for randomizing the hue, saturation, and value of the texture in each cell. It will also allow randomization for some PBR channels such as roughness when using Detect PBR.

## Noise HSV

This also randomizes the HSV of the texture, but it's based on a noise texture that's overlayed on top of the final result.

## Modifying the Defaults

If you would like to change any of the scatter node's defaults to fit your particular workflow, just edit the defaults.py file inside the addon.