---
title: Error & Debug Codes
description: Millennium Dawn's Error & Debug Codes
---

This guide helps developers read game.log to debug the mod.

**How to Use**: Open game.log, search for `DEBUG: CODE_NUM`, and look up the code below.

---

# Debug Codes

## Influence System (1000-1099)

| Code | Description                            | Source                              |
| ---- | -------------------------------------- | ----------------------------------- |
| 1000 | Influencer has fallen below 0.01%      | `00_influence_scripted_effects.txt` |
| 1001 | Double Influencer Present              | `00_influence_scripted_effects.txt` |
| 1002 | Non-Existent Nation in Influencer List | `00_influence_scripted_effects.txt` |
| 1003 | Influence Change (detailed log)        | `00_influence_scripted_effects.txt` |

## Money System (1049-1099)

### Tax Changes

| Code | Description                     | Source                                |
| ---- | ------------------------------- | ------------------------------------- |
| 1049 | Player/AI Triggered Tax Refresh | `00_MD_economyview_scripted_guis.txt` |
| 1050 | AI Population Tax +1            | `00_MD_economyview_scripted_guis.txt` |
| 1051 | AI Population Tax +5            | `00_MD_economyview_scripted_guis.txt` |
| 1052 | AI Population Tax -1            | `00_MD_economyview_scripted_guis.txt` |
| 1053 | AI Population Tax -5            | `00_MD_economyview_scripted_guis.txt` |
| 1054 | AI Corporate Tax +1             | `00_MD_economyview_scripted_guis.txt` |
| 1055 | AI Corporate Tax +5             | `00_MD_economyview_scripted_guis.txt` |
| 1056 | AI Corporate Tax -1             | `00_MD_economyview_scripted_guis.txt` |
| 1057 | AI Corporate Tax -5             | `00_MD_economyview_scripted_guis.txt` |

### Debt Management (1070-1079)

| Code | Description                          | Source                                |
| ---- | ------------------------------------ | ------------------------------------- |
| 1070 | 1 Billion Debt Taken                 | `00_MD_economyview_scripted_guis.txt` |
| 1071 | 10 Billion Debt Taken                | `00_MD_economyview_scripted_guis.txt` |
| 1072 | 100 Billion Debt Taken               | `00_MD_economyview_scripted_guis.txt` |
| 1073 | 1 Billion Debt Paid                  | `00_MD_economyview_scripted_guis.txt` |
| 1074 | 10 Billion Debt Paid                 | `00_MD_economyview_scripted_guis.txt` |
| 1075 | 100 Billion Debt Paid                | `00_MD_economyview_scripted_guis.txt` |
| 1076 | Maximum Debt Paid (All Debt Cleared) | `00_MD_economyview_scripted_guis.txt` |

### Money Printing (1080-1089)

| Code | Description   | Source                                |
| ---- | ------------- | ------------------------------------- |
| 1084 | Money Printed | `00_MD_economyview_scripted_guis.txt` |

## Energy System (2000-2099)

| Code | Description    | Source              |
| ---- | -------------- | ------------------- |
| 1049 | Energy Refresh | `01_energy_gui.txt` |

---

# How to Enable Debug Logging

To see debug messages in game.log, use console commands during gameplay:

- `debug logcat on` - Enable debug logging
- `debug logcat off` - Disable debug logging

---

# Source Files

Debug codes are defined in these common files:

- `common/scripted_guis/00_MD_economyview_scripted_guis.txt` - Money system debug
- `common/scripted_guis/01_energy_gui.txt` - Energy system debug
- `common/scripted_effects/00_influence_scripted_effects.txt` - Influence system debug

---

# Related Resources

- [Code Resources](/dev-resources/code-resource/) - Modifiers and effects
- [Code Stylization](/dev-resources/code-stylization-guide/) - Best practices
