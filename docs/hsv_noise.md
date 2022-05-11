---
excerpt: Documentation for the HSV Noise function of the Scattershot add-on for Blender.
nav_order: 3
nav_exclude: false
search_exclude: false
---

# HSV Noise

The Scattershot HSV Noise operator takes the first output of any node and shifts its hue, saturation, and value based on a noise texture. It's useful for dirtying up or adding an extra layer of randomness to any surface. The saturation control takes the values from the noise texture directly for a linear change, but the hue control is dialed down to be more subtle and the value control is adjusted via a soft light operation to help preserve detail. 