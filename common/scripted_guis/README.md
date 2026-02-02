# Scripted GUIs

This directory contains Millennium Dawn's scripted GUI definitions.

## Developer Guidelines

### Performance Optimization

- **Use dirty variables**: Implement dirty variables to prevent unnecessary GUI updates. Only recalculate values when the underlying data has actually changed, not on every frame.
- **Minimize update frequency**: Follow best practices to reduce performance impact, as scripted GUIs can be resource-intensive on lower-end systems.

### AI Compatibility

- Ensure AI can interact with your GUI mechanics when necessary.
- If direct GUI interaction isn't feasible for AI, provide alternative pathways via on_actions or other automated mechanics.

### Vanilla Main Screens

For main screens such as the political tab, diplomacy screen, or otherwise there is no real discernible way for us to use dirty there without it displaying code language.

Known impacted parent_window_tokens for the dirty variable:

- selected_country_view_diplomacy
- trade_tab
- politics_tab
- decision_tab
- technology_tab
- construction_tab
- production_tab
- deployment_tab
- logistics_tab
- diplomacy_tab

For more syntax and other help you can review the [wiki](https://hoi4.paradoxwikis.com/Scripted_GUI_modding).
