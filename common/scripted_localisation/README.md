# Scripted Localisation Guide

## Overview

Scripted localisation allows you to create dynamic localisation that changes based on game conditions. It functions similar to creating custom namespaces but with the current scope assumed by default, making scoping optional.

## File Location

Scripted localisation files are located in `/common/scripted_localisation/*.txt`

## Millennium Dawn File Naming Standards

- **Mechanical files**: Use `00_` or `01_` prefix (e.g., `00_generic_scripted_localisation.txt`)
- **Country-specific files**: Use `99_<TAG>_` prefix (e.g., `99_USA_scripted_localisation.txt`)

## Basic Structure

```
defined_text = {
    name = my_scripted_loc
    text = {
        trigger = {
            tag = FRA
        }
        localization_key = FRA_localization_key
    }
    text = {
        localization_key = fallback_localization_key
    }
}
```

### Components

- **`name`**: The identifier used to reference this scripted localisation in regular localisation files
- **`text`**: A possible choice for localisation. The game evaluates these top-to-bottom and uses the first one that meets its conditions
- **`trigger`**: Conditional block that determines if this text option should be used
- **`localization_key`**: The localisation key to display if this text block is selected

## Usage in Localisation Files

```yaml
l_english:
 some_localisation: "[my_scripted_loc]"
 FRA_localization_key: "France-exclusive localisation"
 fallback_localization_key: "Generic localisation"
```

## Advanced Features

### Random Selection

You can randomize which localisation key is chosen using `random_list`:

```
defined_text = {
    name = random_greeting
    text = {
        random_list = {
            60 = { localization_key = greeting_formal }
            40 = { localization_key = greeting_casual }
        }
    }
}
```

### Scoped References

Scripted localisation can be called with specific scopes:

- `[ROOT.my_scripted_loc]`
- `[FROM.my_scripted_loc]`
- `[THIS.my_scripted_loc]`
- `[PREV.my_scripted_loc]`
- `[USA.my_scripted_loc]` (country tag scopes)

### Variable Usage

Temporary variables set in trigger blocks remain available when displaying the localisation key, enabling mathematical operations and recursive scripted localisation calls.

## Best Practices

1. **Fallback Options**: Always include a fallback `text` block without triggers as the last option
2. **Performance**: Avoid overly complex trigger conditions
3. **Organization**: Group related scripted localisation in the same file
4. **Naming**: Use descriptive names that indicate the content type (e.g., `country_status_descriptor`, `war_outcome_text`)
5. **Documentation**: Comment complex logic within your scripted localisation files

## Example: Dynamic Country Status

```
defined_text = {
    name = country_power_status
    text = {
        trigger = {
            is_major = yes
            has_war = yes
        }
        localization_key = major_at_war
    }
    text = {
        trigger = {
            is_major = yes
        }
        localization_key = major_at_peace
    }
    text = {
        trigger = {
            has_war = yes
        }
        localization_key = minor_at_war
    }
    text = {
        localization_key = minor_at_peace
    }
}
```

## Reference

For detailed technical information, see the [HOI4 Paradox Wiki: Localisation](https://hoi4.paradoxwikis.com/Localisation#Scripted_localisation)