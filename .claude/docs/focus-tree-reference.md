# Focus Tree Reference

## Authoring rules

- Ids use `TAG_focus_name`. Use `relative_position_id` beyond the root.
- Include logging, `ai_will_do = { base = N }`, and the two-layer search filters
  from [Search Filters](search-filters.md). The log belongs in a `completion_reward`
  or `select_effect` that runs something. A block holding only a log is dead. Omit it.
- Omit defaults: `cost = 10`, `cancel_if_invalid = yes`, `continue_if_invalid = no`,
  and `available_if_capitulated = no`.
- No empty `mutually_exclusive` or `available` blocks, or commented-out slot markers.
- Limit permanent effects to five. Use timed ideas for additional bonuses.
- Match `available` to a reachable bypass condition. Never pair a bypass with
  `available = { always = no }`.
- A focus whose reward spends treasury needs the bankruptcy guard in `ai_will_do`. See
  [Search Filters](search-filters.md#bankruptcy-guard). Focus duration is not money cost.
- Check `country_exists` before targeting another country with a wargoal.
- When a focus fires an event to another country, add the `TT_IF_THEY_ACCEPT` tooltip
  pattern from `event-reference.md`.
- Focus titles carry no `§` color codes, and descriptions use only `§Y`, `§G`, and `§R`.
  See [Color Codes](localisation-rules.md#color-codes).

## Files and container

| Prefix   | Usage                                |
| -------- | ------------------------------------ |
| `00_`    | System requirements such as titlebar |
| `01-04_` | Shared and joint trees               |
| `05_`    | Country trees                        |

The prefix forces load order, so shared trees load first.

```
focus_tree = {
 id = greece_focus

 country = {
  factor = 0
  modifier = {
   tag = GRE
   add = 100
  }
 }

 shared_focus = USoE001

 continuous_focus_position = { x = 2350 y = 1200 }
}
```

## Property order

```
1.  id
2.  icon
3.  x, y
4.  relative_position_id
5.  cost
6.  allow_branch
7.  prerequisite / mutually_exclusive
8.  search_filters
9.  available / bypass / cancel
10. completion_reward / select_effect / bypass_effect
11. ai_will_do                  (always last)
```

```
focus = {
 id = SER_free_market_capitalism
 icon = blr_market_economy

 x = 5
 y = 3
 relative_position_id = SER_free_elections

 cost = 5

 prerequisite = { focus = SER_western_approach }
 search_filters = { FOCUS_FILTER_POLITICAL }

 available = {
  western_liberals_are_in_power = yes
 }

 completion_reward = {
  log = "[GetDateText]: [Root.GetName]: Focus SER_free_market_capitalism"
  add_ideas = SER_free_market_idea
 }

 ai_will_do = {
  base = 1
 }
}
```

## Shared and joint focuses

A shared focus lives in one file and appears in several trees through
`shared_focus = X`. A joint focus (`joint_focus = { ... }`) also shares completion: when
one joint country completes it, it is complete for every country in its joint set.

`joint_trigger` defines the joint set. It is not a selection gate. Who can pick the
focus is still governed by `available`, `visible`, `prerequisite`, and `allow_branch`.

| Reward block                         | Fires on                              |
| ------------------------------------ | ------------------------------------- |
| `completion_reward`                  | Every joint country                   |
| `completion_reward_joint_originator` | Only the country that completed it    |
| `completion_reward_joint_member`     | Every joint country but the completer |

- All-members focus: omit `joint_trigger` and gate `available` with the membership
  trigger. The default joint set is every country that has the tree.
- Country-specific focus: gate `available` to that country and restrict the set with
  `joint_trigger = { original_tag = TAG }`. Without it, other members still receive
  shared completion and rewards.
- Joint focuses pick a `text_icon` titlebar style matching the joint set, defined in
  `common/national_focus/00_titlebar_styles.txt`.

## Building effects

Buildings in effects must cost money. Use the scripted effects in
`common/scripted_effects/00_scripted_effects.txt`, not raw `add_building_construction`.
Each charges treasury itself. The price includes a building slot.

```
117 = { one_state_industrial_complex = yes }   # a given state
one_random_industrial_complex = yes            # any owned state
two_random_industrial_complex = yes
```

| Building               | Random effect                       | State-scope effect                 |
| ---------------------- | ----------------------------------- | ---------------------------------- |
| Civilian factory       | `one_random_industrial_complex`     | `one_state_industrial_complex`     |
| Military factory       | `one_random_arms_factory`           | `one_state_arms_factory`           |
| Dockyard               | `one_random_dockyard`               | `one_state_dockyard`               |
| Offices                | `one_office_construction`           | `one_state_office_construction`    |
| Infrastructure         | `one_random_infrastructure`         | `one_state_infrastructure`         |
| Air base               | `one_air_base`                      | `one_state_air_base`               |
| Network infrastructure | `one_random_network_infrastructure` | `one_state_network_infrastructure` |
| Anti-air               | `one_anti_air`                      | `one_state_anti_air`               |
| Radar                  | `one_radar_station`                 | `one_state_radar_station`          |
| Nuclear reactor        | `one_random_nuclear_reactor`        | `one_state_nuclear_reactor`        |
| Agriculture district   | `one_random_agriculture_district`   | `one_state_agriculture_district`   |

Full library: `docs/src/content/resources/scripted-effects-reference.md`.
