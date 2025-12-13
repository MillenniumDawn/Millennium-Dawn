---
layout: default
title: "Troubleshooting Guide"
description: "Guide for troubleshooting common issues in Millennium Dawn"
---

# Troubleshooting Guide

## Basic Troubleshooting Steps

1. Remove the ugc_2777392649.mod file from the mod folder in ``Documents / Paradox Interactive / Hearts Of Iron IV``
2. Unsubscribe from Millennium Dawn
3. Remove the all mod files in location\steamapps\workshop\content\394360\2777392649
4. Resubscribe to Millennium Dawn
5. After this, validate the HOI4 files.
6. After finishing the validation, exit steam and then reopen steam
7. Start Millennium Dawn without any submods to ensure it boots into game as expected
  - Note: Submods can and will cause issues. Please refrain from using them where possible if you are experiencing issues.

## Save Game Corruption

Save games in Millennium Dawn are much larger than other mods. It is important to ensure you are using local game saves over cloud saves for the most stability. Typically this becomes more problematic in the late game around the 2020+ mark when save files start to exceed 100MB or more. You can easily bypass this issue by not saving anything on the cloud for *Millennium Dawn*.

## General Performance Improvement Tips

Some computers may have performance issues with Millennium Dawn and as such we recommend taking a couple precautionary steps if you have an older GPU/Laptop or any form of computer that offers. Every update we strive to continue to make the mod more performant, but are ultimately beholden to Paradox for most major performance improvements.

- Clear the User Directory in your launcher
- Switch it to DX9 from DX11
- Do NOT use submods, most are poorly optimized and make the experience that much worse.
- Background processes
- Overloading of the CPU
- Try to run the mod on a SSD if possible. It runs much better and has a more smooth experience on more modern hardware

**If none of the above relates to your current issues, please reach out on the Discord.**

# Linux Users

The Millennium Dawn team tries our best to provide a compatible experience with Linux users, but as the team is predominantly Windows we struggle to be as effective with Linux.

## Help! My game crashes shortly after game start!

This is a known issue with Linux as of the v1.17.* of Hearts of Iron IV. We have reached out to Paradox Interactive for support on this but until that time we are flying blind.

You can easily fix this by switching to a different runtime in your compatibility tab. The team recommends Proton of some form for now as that has been tested and works with the OpenGL renderer.
