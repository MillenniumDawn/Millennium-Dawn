# How to use gfx_entry_generator.py

## Prerequisites

- Python 3.9 or later installed
- This script must be located in the `tools/` directory of the mod

## Usage

1. Open a terminal (PowerShell, CMD, Terminal, or any shell)

2. Navigate to the `tools/` directory of the mod:
   ```
   cd path/to/Millennium-Dawn/tools
   ```

3. Run the script:
   ```
   python3 gfx_entry_generator.py
   ```

4. Select from the menu:
   - **1** - Generate `goals.gfx` and `goals_shine.gfx`
   - **2** - Generate `MD_eventpictures.gfx`
   - **3** - Generate `MD_ideas.gfx`
   - **4** - Generate `MD_parties_icons.gfx`
   - **5** - Generate `MD_intelligence_icons.gfx`
   - **6** - Generate `MD_decisions.gfx`

5. The generated `.gfx` files will be automatically moved to the `interface/` directory

## Notes

- The script automatically detects and warns about duplicate icon names
- Works on Linux, Mac, and Windows
- For goals (option 1), you will be asked whether to prepend `GFX_` to icon names. Typically enter `0` (no) for goals.

## Verification

After generating, check the changes:
```
git status
git diff
```
