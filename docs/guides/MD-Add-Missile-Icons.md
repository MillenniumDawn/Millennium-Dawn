## How to Add Missile Icons

1. Add the dds files for your missile icons in ``gfx/interface/scripted_gui/missiles/models/TAG``
2. Create the sprite entries in ``interface/MD_countrymissilesview.gfx``
   - This following convention is the standard and the file is structure as missile types -> countries:

```
spriteType = {
   name = "GFX_missile_PER_ID_26_icon"
   texturefile = "gfx//interface//scripted_gui//missiles//models//PER//MD_IRBM_icon.dds"
   noOfFrames = 1
}
```

3. Create the sprite entries in ``interface/mdult_missiles.gfx``
   - The following convention is the standard and the file is structured as countries -> missile types

```
### PAK ###

SpriteType = {
	name = "GFX_PAK_ICBM1_medium"
	texturefile = "gfx//interface//scripted_gui//missiles//models//PAK//Ghauri-5.dds"
}
```
