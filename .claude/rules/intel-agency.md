---
paths:
  - "common/intelligence_agency_upgrades/**"
---

# Intelligence Agency Upgrades

New upgrades require wiring across six files: definition, on_actions registry (four arrays + `resize_array` bump), loc triple (`id`/`_name`/`_gfx`), scripted_gui prerequisites, the `can_select` trigger + dispatch branch in `common/scripted_triggers/00_MD_auto_agency_scripted_triggers.txt`, and a sprite in `interface/*.gfx`. Read `common/intelligence_agency_upgrades/README.md` first.
