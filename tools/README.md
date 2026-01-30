# Millennium Dawn Tools

The directory here contains various tools and scripts that the Millennium Dawn development team uses for mod development, quality assurance, and asset management.

## Requirements

Some scripts rely on non-native packages for Python. You can install these by executing the following command:

```bash
pip install -r requirements.txt
```

### Package List

- requests
- pillow

## Directory of Scripts

### Quality Assurance & Code Standards

1. **check_basic_style.py** - Basic style checking for mod files (.txt files)
2. **check_basic_style_2.py** - Advanced style checking for mod files
3. **check_braces.py** - Validates matching braces in mod script files
4. **coding_standards.py** - Enforces Millennium Dawn coding standards
5. **validate_localization_encoding.py** - Validates and fixes UTF-8 BOM encoding for localization files
6. **validate_mod_encoding.py** - Checks UTF-8 encoding for .mod files

### Asset & Graphics Tools

7. **batchDDS.py** - Batch processing for DDS texture files
8. **duplicate_icon.py** - Detects duplicate icon files
9. **find_duplicate_textures.py** - Finds duplicate texture files in the mod
10. **flag-reference-checker.py** - Validates flag references in the mod
11. **gfx_entry_generator.py** - Generates GFX entries for goals and other interface elements
12. **gfx_entry_generator_gui.py** - GUI version of the GFX entry generator
13. **state_gfx.py** - Manages state graphics entries

### Focus Tree & Content Tools

14. **count_of_focuses.py** - Counts focuses in focus tree files
15. **standardize_focus_tree.py** - Standardizes focus tree formatting
16. **text_to_focus_and_focus_to_loc.py** - Converts between focus definitions and localization
17. **to_focus_name.py** - Converts text to valid focus names
18. **generate_tribute_ideas.py** - Generates tribute idea definitions
19. **search_add_ideas.py** - Searches and adds ideas to the mod

### Formatting & Cleanup Tools

20. **convert to utf8.py** - Converts files to UTF-8 encoding
21. **fix_indentation_and_spacing.py** - Fixes indentation and spacing issues
22. **fix_line_endings.py** - Standardizes line endings
23. **fix_styling.py** - Automatic styling fixes for mod files

### Utility Scripts

24. **calculate_days.py** - Calculates days from January 1st for HOI4 date system
25. **create_modifiers.py** - Creates modifier definitions
26. **loc.py** - Localization utilities
27. **logging_tool.py** - Logging utility for development
28. **path_utils.py** - Path manipulation utilities

## Documentation

- **gfxEntryGenerator.md** - Detailed guide on using the GFX entry generator script
- **README.md** - This file

## Old Folder

The directory named `old` contains unused or outdated tools that are no longer actively maintained. They are kept for historical purposes but are not expected to be used in current development.
