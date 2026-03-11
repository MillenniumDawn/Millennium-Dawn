---
title: Troubleshooting Guide
description: Guide for troubleshooting common issues in Millennium Dawn
---

# Troubleshooting Guide

## General Performance Improvement Tips

Some computers may have performance issues with Millennium Dawn and as such we recommend taking a couple precautionary steps if you have an older GPU/Laptop or any form of computer that offers. Every update we strive to continue to make the mod more performant, but are ultimately beholden to Paradox for most major performance improvements.

Hearts of Iron IV runs multi-core on most processes but AI remains it's main bottleneck and is what causes most of the lag you see in game. Having a strong CPU with single-core performance will yield you

- Clear the User Directory in your launcher
- Use DirectX 9 instead of DirectX 11 on older hardware
  - Modern machines should have no noticeable difference on this but it's worth noting if you have any issues at all
- Do NOT use submods, most are poorly optimized and make the experience that much worse.
- Close CPU intensive background tasks where possible
- Overloading of the CPU
  - Linux users we recommend to setting your CPU Frequency to "Performance" rather then powersave for maximum performance
- Try to run the mod on a SSD if possible. It runs much better and has a more smooth experience on more modern hardware

## Basic Troubleshooting Steps

1. Remove the ugc_2777392649.mod file from the mod folder in `Documents / Paradox Interactive / Hearts Of Iron IV`
2. Unsubscribe from Millennium Dawn
3. Remove the all mod files in `location\steamapps\workshop\content\394360\2777392649`
4. Resubscribe to Millennium Dawn
5. After this, validate the HOI4 files.
6. After finishing the validation, exit steam and then reopen steam
7. Start Millennium Dawn without any submods to ensure it boots into game as expected

- Note: Submods can and will cause issues. Please refrain from using them where possible if you are experiencing issues.

## Help! My Game Boots to Vanilla

Typically, this comes from the steam servers from not properly installing/downloading everything for the mod.
Steam doesn't seem to play very nicely with large installs so just repeat steps 2, 3, and 4.

1. Remove all files in `location\steamapps\workshop\content\394360\2777392649`
2. Unsubscribe from Millennium Dawn
3. Resubscribe to Millennium Dawn
4. Allow Steam to fully complete the download
5. Restart your steam client and then try to boot the mod.

## Stale or Duplicate .mod Files

When switching between mod versions, changing game versions, or reinstalling mods from the Workshop, Steam can leave behind stale `.mod` files in your HOI4 mod directory (`Documents / Paradox Interactive / Hearts Of Iron IV / mod`). These leftover files can point to outdated or removed mod folders, causing the game to load the wrong version of a mod, boot into vanilla, or a mix of incompatible versions.

To resolve this:

1. Navigate to `Documents / Paradox Interactive / Hearts Of Iron IV / mod`
2. Delete any `.mod` files and matching folders related to the affected mod (e.g., `ugc_2777392649.mod`)
3. Also clear the Workshop content folder at `steamapps\workshop\content\394360\2777392649`
4. Validate your HOI4 game files through Steam
5. Resubscribe to the mod and let Steam fully download it
6. Restart Steam before launching the game

**Important:** Each of these steps (validating files, unsubscribing/resubscribing) can regenerate duplicate `.mod` files if old ones were not fully removed first. Always delete the stale files _before_ triggering any Steam download or validation. If you frequently switch between game versions or mod versions, check this directory regularly to ensure no extra/loose `.mod` files remain.

## Save Game Corruption

Save games in Millennium Dawn are much larger than other mods. It is important to ensure you are using local game saves over cloud saves for the most stability. Typically this becomes more problematic in the late game around the 2020+ mark when save files start to exceed 100MB or more. You can easily bypass this issue by not saving anything on the cloud for _Millennium Dawn_.

## Low Virtual Memory / Paging File

If you receive a "your paging file is low" warning or experience crashes on systems with limited RAM (common on laptops), you may need to increase your Windows virtual memory (page file) =.

Error in the Log:

```md
[19:01:16][no_game_date][virtualfilesystem_physfs.cpp:1257]: Error setting buffer for file: common/countries/Lesotho.txt. File may not read/write correctly.
```

****Windows Instructions****

To increase your page file size:

1. Right-click **This PC** on your desktop or in File Explorer and select **Properties**
2. Click **Advanced system settings** on the left
3. Under the **Advanced** tab, click **Settings** in the Performance section
4. Go to the **Advanced** tab and click **Change** under Virtual memory
5. Uncheck **Automatically manage paging file size for all drives**
6. Select your drive, choose **Custom size**, and set the initial and maximum size (a recommended minimum is 8192 MB for initial and 16384 MB for maximum)
7. Click **Set**, then **OK**, and restart your computer

This gives Windows more disk-backed memory to work with when physical RAM runs low, which helps prevent crashes during long sessions or late-game saves.

**If none of the above relates to your current issues, please reach out on the Discord.**

# Linux Users

The Millennium Dawn team tries our best to provide a compatible experience with Linux users, but as the team is predominantly Windows we struggle to be as effective with Linux.

## Help! My game crashes shortly after game start!

This is a known issue with Linux as of the v1.17.\* of Hearts of Iron IV. We have reached out to Paradox Interactive for support on this but until that time we are flying blind.

You can easily fix this by switching to a different runtime in your compatibility tab. The team recommends Proton of some form for now as that has been tested and works with the OpenGL renderer.

**NOTE**: This is fixed in the upcoming version and Linux/Mac users can use the BETA in the meantime without switching between renderers.
