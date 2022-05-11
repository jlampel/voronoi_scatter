# About Scattershot

Scattershot is an addon for Blender’s shader editor that distributes and randomizes textures, similar to texture bombing or splattering operations in other 3d software, except with more control and less setup.

Tiled textures can look great up close, but even the best seamless texture looks obviously repeated and fake at a distance. Scattershot instantly fixes that issue with the **Voronoi Scatter** function, which turns your image textures into a new node that has controls for randomizing every aspect of each repetition of the texture as well as controls for obscuring the seams between each cell. 

**[Watch the Scattershot video tutorial](https://www.youtube.com/watch?v=_3DFBnYtC8E)**

Scattershot gives you full control over how you want to distribute and randomize your textures with finely tuned, easy to use sliders. Some options require a procedural texture to be added inside the node, so you can always leave those options off during creation so that your shader will be as quick to render as possible. 

And, speaking of render times, this setup is surprisingly fast. Texture bombing works by manipulating the texture’s vectors, which means that it is not increasing memory usage or render time to any noticeable degree.

**[Learn the principles behind the add-on](https://www.youtube.com/watch?v=xKnSgH8zVuA)**

In order for all of these effects to work together and be customized for each situation, a lot of manual tweaking would need to be done to your scattering setup each and every time you want to use it. I, of course, do not want to spend time doing that. This addon was born of pure laziness so that I can get exactly the results I need in just a few clicks.

You can download Scattershot by [purchasing it on the Blender Market](https://blendermarket.com/products/scattershot---procedural-image-texture-scattering--tiling-with-voronoi) or by [subscribing to CG Cookie](https://cgcookie.com/). The code for Scattershot is freely avaliable to view on GitHub but the node groups that it depends on are not included.