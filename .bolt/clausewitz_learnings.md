## 2024-05-24 - [AI Limiter Calculations]
**Learning:** `ai_limiter_calculations` runs in `on_daily` for all AI nations. This involves multiple heavy arithmetic variable modifiers and bounds checking to determine unit limiters (divisions, planes, ships) based on factory count and threat. These inputs (factories, threat) change slowly. Running them daily for ~200 tags causes unnecessary CPU overhead.
**Action:** Move `ai_limiter_calculations` to the `on_weekly` pulse for all AI nations, reducing the tick cost by a factor of 7 without changing behavioral output.
