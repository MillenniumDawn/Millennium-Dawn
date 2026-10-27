# Intelligence Agency Upgrades

`intelligence_agency_upgrades.txt` defines the agency upgrades shown in the normal Intelligence Agency window. `_documentation.info` describes the engine syntax.

Each upgrade needs:

- a unique `upgrade_*` ID
- a `picture = GFX_*` sprite defined in `interface/*.gfx`
- its native `available` prerequisites, if any
- every intended `level`, including the full `modifier` and `complete_effect`
- an `ai_will_do` block

References from `create_intelligence_agency` must use a defined agency logo sprite. References from `upgrade_intelligence_agency` must name an upgrade defined in this directory.

Run the focused validator with:

```bash
python3 tools/validation/validate_agency_upgrades.py --path .
```

It checks duplicate upgrade IDs, required upgrade pictures and their sprites, agency creation icons, and upgrade effect references.
