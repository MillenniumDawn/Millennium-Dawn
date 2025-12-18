# Singapore Dynamic Modifier Guide

**Author(s):** BirdyBoi & BlackSyX
**Mentor:** BirdyBoi & Luigi IV (aka MD's Fijian Nationalist)

---

This guide covers how to create Singapore dynamic modifiers. This is one of 3 files related to Singapore Dynamic Modifier (`05_SIN_dynamic_modifier.txt`, `SIN - Singapore.txt`, `MD_ideas.gfx`).

**© Millennium Dawn 2016-2026**

## How to Add New Ideas

Follow these steps to create a new idea for a country:

### Step 1: Create Your Dynamic Modifier
Edit the file: `common/dynamic_modifiers/05_SIN_dynamic_modifiers.txt`

**Modifier Database References:**
- `localisation/english/replace/replaced_from_focus_l_english.yml`
- `localisation/english/replace/replaced_from_vanilla_modifiers_l_english.yml`

### Step 2: Add Dynamic Modifier to Country
Edit the file: `history/countries/SIN - Singapore.txt`

Add the following line:
```
530 = { add_dynamic_modifier = { modifier = SIN_singapore_problem } }
```

### Step 3: Register Your GFX
Edit these files:
- `interface/MD_ideas.gfx`
- `interface/MD_dynamic_modifiers.gfx`

Add:
```
name = "GFX_idea_SIN_singapore_problem"
texturefile = "gfx/interface/state_modifiers/SIN_singapore_problem.dds"
```

### Step 4: Register State Modifier
Edit the appropriate state file in: `history/states/`

### Step 5: Create Idea Icon
Create icon in: `gfx/interface/state_modifiers/`

**Icon Creation Guidelines:**
1. Millennium Dawn has visual standards - discuss in Discord channel "graphics-sound"
2. Download template from Google Drive (pinned in Discord "graphics-sound" channel)
3. Create an icon that represents your idea
4. Submit for review in Discord channel "gfx_request" to ensure visual consistency

### Step 6: Add Localisation
Edit the file: `localisation/english/MD_focus_SIN_l_english.yml`

Add your dynamic modifier with name and description.

---

Happy Coding!