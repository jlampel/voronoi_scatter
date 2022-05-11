---
excerpt: Short description to include as an opening and SEO metatags.
nav_order: 1
nav_exclude: false
canonical_url: https://www.google.com
search_exclude: false
---

# Voronoi Scatter

Once you install the Scattershot addon, you'll find a new operator called Voronoi Scatter in the Node menu of the Shader Editor. To access it more quickly, right quick and add it to your quick favorites (Q) menu or use the right click context menu.

> [!NOTE]
> Note: the right click context menu does not show the addon's settings - it will use the default or last used settings.

You must have one or more image textures selected in order to use the Voronoi Scatter command. The tooltips for the settings are pretty descriptive, so hover your mouse over each button if you forget what it does. Click 'OK' and your textures will be converted into a scatter node.

If you would like to change your scatter node's settings after the fact, such as to switch from UV to tri-planar mapping, select just the scatter node and run the Voronoi Scatter operator again.

To reverse the process, you can always select the scatter node and use the Un-Scatter command that is in the Node menu or in the right click context menu.

## Mapping

The scattering can be done according to your object's UVs or it can be projected from all sides with tri-planar mapping. Tri-planar projection is the same thing as box mapping, but Scattershot uses a custom implementation instead of Blender's box mapping because it allows for important options like random rotation (you can't rotate a box mapped texture) and correcting the aspect ratio of non-square textures. The impact on performance between the UV and Tri-Planar options is negligible since the image is not duplicated to achieve the effect.

## Scatter Methods

This setting has the biggest impact on performance and changes several things about the setup, including transparency.

**Just Coordinates** does not move or replace the texture like the other methods and instead attaches a scattered vector coordinates node to it. This is useful for advanced users who want to customize their setups or scatter procedural textures. The Random Color and PBR options are disabled because no mixing is done after the image texture.

**Interspersed** picks a random texture or texture set for each voronoi cell. It does not have transparency and sets the image texture's extension to Repeat so that you will never have gaps in the result. This is useful for scattering one or two textures across a terrain or scattering a couple grunge masks together.

**Noise Blended** does not choose a random texture per cell and instead scatters each texture individually and then blends them all together at the end using the Noise Blend operator (more on that below). This produces a much more natural pattern than Interspersed if working with many images. This method is perfect for scattering several sets of PBR textures together (more on PBR below).

**Interspersed Alpha** picks a random texture or texture set per cell just like Interspersed but supports transparency. The image texture's extension will be set to clip and you will be given controls for the background color, the alpha clip threshold, and the density.

**Layered Alpha** is the fastest way to get textures to overlap. It simply creates an Interspersed Alpha scatter node for each texture or texture set and chains them all together inside one parent scatter node. This creates a layering effect where the first texture set gets overlapped by the second, which gets overlapped by the third, and so on.

**Overlapping** enables textures to actually overlap their immediate neighbors. This allows for great looking results and appears much more randomized than Layered Alpha because the same texture set will not always be on top and the distribution is much more controllable, but it comes at the cost of shader compilation time since each image setup is duplicated eight times in order for each surrounding cell to be checked. This method works best when leaving the Random Cell Shape at 0 and increasing the Random Location instead. Also, Cycles has a hard texture limit, so it is not recommended to use this option with more than four images. If you can, try using the Stacked option instead.

## Pixel Interpolation

This option sets how Cycles and Eevee blends between each pixel of the image.

**Closest** - Pixels are not interpolated, like in pixel art. This fixes artifacts between voronoi cell edges in Eevee.

**Cubic** - Pixels are smoothed but may cause artifacts between voronoi cells in Eevee. Only recommended for Cycles.

## Edge Blur

This option enables an option that mixes in white noise to the voronoi coordinates so that the boundaries between cells appears to blur without blurring the texture. This is incredibly helpful for hiding seams. The quality of this blur depends on the number of samples in both Eevee and Cycles.

## Edge Warp

Edge Warp is another way to disguise seams. It enables an option to distort the shape of each voronoi cell. Without straight lines, it's much harder for the viewer's eyes to pick out where the boundaries are.

## Texture Warp

This applies a noise to the resulting texture coordinates, so that each instance of the texture appears to have a slightly different shape.

## Random Color

This enables controls for randomizing the hue, saturation, and value of the texture in each cell. It will also allow randomization for some PBR channels such as roughness when using Detect PBR.