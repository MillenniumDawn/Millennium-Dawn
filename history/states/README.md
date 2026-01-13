# Read This If You Plan On Modding States In Any Capacity

## Creating a New State

If you create a new state, remember these key things:

- Transfer resources, factories, population etc accordingly (ex. if you split a state in two)
- Set the correct `state_category` according to the population (see the list at the bottom)
- Victory points be put in the correct state file
- Make sure provinces don't overlap in two different states
- Buildings are corrected in nudge, that goes for unit stacks as well if provinces are altered
- If the game crashes on start up ask for help (it's most likely air bases in wrong prov)
- Read the error log for any mentions of the former or new state added

## Modding an Existing State

If you mod in an existing state make sure that:

- Everything said above is correct
- Be more hesitant if your changes gives the country controlling the state more longterm advantages, as balance can be rubbed in favour to one country for something like adding an extra naval factory

## State Category Population Ledger

Approximate `state_category` per number of population a state should have:

| State Category | Population Range |
|---|---|
| `state_military_base` | For leased military bases |
| `state_inhospitable` | For impassable states |
| `state_00` | <300,000 inhabitants |
| `state_01` | 300,000 - 800,000 inhabitants |
| `state_02` | 800,000 - 1,500,000 inhabitants |
| `state_03` | 1,500,000 - 2,500,000 inhabitants |
| `state_04` | 2,500,000 - 3,800,000 inhabitants |
| `state_05` | 3,800,000 - 5,200,000 inhabitants |
| `state_06` | 5,200,000 - 6,800,000 inhabitants |
| `state_07` | 6,800,000 - 8,500,000 inhabitants |
| `state_08` | 8,500,000 - 10,500,000 inhabitants |
| `state_09` | 10,500,000 - 13,000,000 inhabitants |
| `state_10` | 13,000,000 - 16,000,000 inhabitants |
| `state_11` | 16,000,000 - 19,000,000 inhabitants |
| `state_12` | 19,000,000 - 23,000,000 inhabitants |
| `state_13` | 23,000,000 - 27,000,000 inhabitants |
| `state_14` | 27,000,000 - 34,000,000 inhabitants |
| `state_15` | 34,000,000 - 42,000,000 inhabitants |
| `state_16` | 42,000,000 - 52,000,000 inhabitants |
| `state_17` | 52,000,000 - 65,000,000 inhabitants |
| `state_18` | >65,000,000 inhabitants |

## Additional Resources

A more detailed guide on Hydroelectric and other variables that are set in the state files is available in the [Millennium Dawn: Code Resource](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/code-resource)
