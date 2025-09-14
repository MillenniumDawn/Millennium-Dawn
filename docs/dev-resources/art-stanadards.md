## File Management

All graphics need to be placed in the right location to ensure they aren’t lost and implemented into the game. Here are the resources you need and the places you need to be looking when you finish your icons.

## Saving Textures

First, download the Nvidia Texture Tools Exporter as a standalone app or a plugin for Photoshop to save icons as DDS files. You can find it here.

https://developer.nvidia.com/nvidia-texture-tools-exporter

The app will be brought up when saving a copy of a file when using it as a plugin for Photoshop. Select the correct format (usually RGB or RGBA, depending on the transparency) when exporting with the highest compression quality before you save.


### File Formats
- Leader Portraits - DXT1 (BC1) - No Mipmaps
- Leader Portraits Small - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Event Pictures - DXT5 (BC3) - No Mipmaps

- Tech Icons/Variant Icons - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Ideas - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Goals/Focus - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- GUI icons - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps

- Loading Screens/Main Menu - PNG

Some textures, such as flags, require the TGA format instead. Be mindful of what you’re working on.

## Placing Files

Ensure that you are in the gfx-input branch on the GitLab repository before dropping anything into the mod. This is where all graphics go regardless of what they are being made for.

You can usually find the location where your graphics need to go relatively easily just by looking at the names of the folders. Compare them to what you’re working on. Folder layouts might vary; some are deeper in the files than others. Here are just some examples.

- Event Pictures: gfx → event_pictures
- Flags: gfx → flags, medium, small
- Leaders: gfx → leaders → TAG
- National Focuses: gfx → interface → goals

Remember that some of these folders have subfolders for each country or region. Place your graphics for Germany in the German folder if you see one.

## Naming Files

Try to follow what everything else in the folder is named, and don’t put “gfx” in front of everything. Try to follow the example below.

DO: GER_Icon_Name
DO NOT: GFX_Germany_Icon_Name

## Implementation

We have a Python script that can do that automatically now. Either Bird or I will run it every time we’ve got lots of new stuff on the branch.

The script works as long as everything should be in the files. Please contact whoever requested the graphics you’re working on if the auto implementation isn’t working.
