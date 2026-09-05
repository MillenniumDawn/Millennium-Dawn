---
paths:
  - "common/intelligence_agency_upgrades/**"
---

# Intelligence Agency Upgrades

New upgrades require wiring across seven files: definition, on_actions registry (four arrays + `resize_array` bump), loc triple (`id`/`_name`/`_gfx`), scripted_gui prerequisites, the `can_select` + `slot_available` triggers and their dispatch branches in `common/scripted_triggers/00_MD_auto_agency_scripted_triggers.txt`, the seed branch in `MD_auto_agency_seed_completed_cache` in `common/scripted_effects/00_MD_auto_agency_scripted_effects.txt`, and a sprite in `interface/*.gfx`. The system is statically dispatched on purpose — never reintroduce `meta_trigger` here. Read `common/intelligence_agency_upgrades/README.md` first.
