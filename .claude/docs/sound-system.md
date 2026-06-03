# Sound System Reference

How MD defines sound effects, combat sounds, and country voicelines. Music: see `.claude/docs/music-system.md`.

## File types

| Type                   | Location                                    | Format                                              |
| ---------------------- | ------------------------------------------- | --------------------------------------------------- |
| Sound definitions      | `sound/*.asset`                             | `.asset` files (not Paradox script)                 |
| Sound effect groupings | `sound/*.asset`                             | `soundeffect` blocks in the same `.asset` files     |
| Sound categories       | `sound/MD4_category.asset`                  | Category blocks with compressor settings            |
| Combat sound mapping   | `sound/combat_sounds/MD4_combat_sounds.txt` | Maps unit types to sound effects                    |
| Country voicelines     | `sound/vo.asset`                            | Voice category + all country soundeffects           |
| DLC voiceover stubs    | `sound/*_vo.asset`                          | Blanked-out DLC voice packs (replaced by MD voices) |

## Directory layout

```
sound/
├── MD4_sound.asset          # Sound definitions (raw WAV → logical name)
├── MD4_soundeffects.asset   # Soundeffect definitions (logical names → grouped effects)
├── MD4_category.asset       # Sound categories with compressor settings
├── vo.asset                 # Country voiceline category + all voiceline soundeffects
├── dd_vo.asset              # DLC voice stubs (blanked)
├── botb_vo.asset            # DLC voice stubs (blanked)
├── goe_vo.asset             # DLC voice stubs (blanked)
├── lar_vo.asset             # DLC voice stubs (blanked)
├── toa_vo.asset             # DLC voice stubs (blanked)
├── animations/              # Weapon, vehicle, and aircraft WAV files (101 files)
├── combat_ambient/          # Ambient battle layer WAVs
├── combat_sounds/           # Combat sound mapping file
├── menu/                    # UI sound effects (alerts, clicks, airwing orders)
├── threshold/               # EH (Event Horizon) threshold sound effects
└── <TAG>/                   # Per-country voiceline WAV directories
    ├── arm/                 # Armenia (89 files)
    ├── ast/                 # Australia (36 files)
    ├── bra/                 # Brazil (36 files)
    ├── chi/                 # China (36 files)
    ├── eng/                 # UK (25 files)
    ├── fra/                 # France (32 files)
    ├── ger/                 # Germany (36 files)
    ├── gre/                 # Greece (36 files)
    ├── irq/                 # Iraq (36 files)
    ├── ita/                 # Italy (28 files)
    ├── kuw/                 # Kuwait (34 files)
    ├── leb/                 # Lebanon (43 files, includes HEZ)
    ├── mex/                 # Mexico (35 files)
    ├── per/                 # Iran (41 files)
    ├── por/                 # Portugal (36 files)
    ├── raj/                 # India (36 files)
    ├── sau/                 # Saudi Arabia (28 files)
    ├── sov/                 # Russia (32 files)
    ├── spr/                 # Spain (31 files)
    ├── tur/                 # Turkey (33 files)
    ├── ukr/                 # Ukraine (28 files)
    ├── usa/                 # USA (33 files)
    └── zom/                 # Zombie (5 files, special)
```

## Sound definition format

```
sound = { name = <name> file = <path> always_load = <bool> volume = <float> }
```

| Field         | Purpose                                          |
| ------------- | ------------------------------------------------ |
| `name`        | Identifier referenced by `soundeffect` entries   |
| `file`        | Path relative to the `sound/` folder             |
| `always_load` | Whether the sound is always loaded into memory   |
| `volume`      | Playback volume (1.0 = neutral, higher = louder) |

## Soundeffect format

Groups one or more `sound` definitions into a playable effect with randomization and spatial properties:

```
soundeffect = {
    name = <name>
    falloff = <name>
    sounds = {
        sound = <name>
        weighted_sound = { sound = <name> weight = int }
    }
    loop = <bool>
    is3d = <bool>
    random_sound_when_looping = <bool>
    max_audible = <int>
    max_audible_behaviour = fail
    volume = <float>
    fade_in = <float>
    fade_out = <float>
    delay_random_offset = { <float> <float> }
    volume_random_offset = { <float> <float> }
    playbackrate_random_offset = { <float> <float> }
    prevent_random_repetition = <bool>
}
```

| Field                        | Purpose                                                                     |
| ---------------------------- | --------------------------------------------------------------------------- |
| `name`                       | Identifier for the soundeffect                                              |
| `falloff`                    | Falloff entry used by this effect                                           |
| `sounds`                     | One or more sound entries; `weighted_sound` picks by weight                 |
| `loop`                       | Whether the effect repeats                                                  |
| `is3d`                       | Whether the effect uses 3D positioning                                      |
| `random_sound_when_looping`  | Picks a random sound on each loop iteration                                 |
| `max_audible`                | Maximum concurrent instances; `max_audible_behaviour = fail` rejects extras |
| `fade_in` / `fade_out`       | Transition durations in seconds                                             |
| `delay_random_offset`        | Min/max random delay between loops                                          |
| `volume_random_offset`       | Min/max random volume variation per play                                    |
| `playbackrate_random_offset` | Min/max random playback rate variation                                      |
| `prevent_random_repetition`  | Prevents the same sound playing twice in a row                              |

## Falloff format

Controls how 3D sounds attenuate with distance:

```
falloff = { name = <name> min_distance = <float> max_distance = <float> height_scale = <float> }
```

| Field          | Purpose                                            |
| -------------- | -------------------------------------------------- |
| `min_distance` | Distance at which volume starts decreasing         |
| `max_distance` | Distance beyond which the sound is inaudible       |
| `height_scale` | Vertical distance scalar between source and camera |

Common MD falloffs: `falloff_50`, `falloff_100`, `falloff_distance`, `falloff_airplane_light`, `falloff_airplane_heavy`.

## Sound categories

Categories apply a compressor to grouped soundeffects:

```
category = {
    name = <name>
    soundeffects = { <soundeffect_name> }
    compressor = {
        enabled = yes
        pregain = <float>
        postgain = <float>
        ratio = <float>
        threshold = <float>
        attacktime = <float>
        releasetime = <float>
    }
}
```

### MD categories (`MD4_category.asset`)

| Category              | Purpose                                       | Contents                                                                |
| --------------------- | --------------------------------------------- | ----------------------------------------------------------------------- |
| `Millennium Dawn`     | Primary MD combat sounds                      | Rifle attacks, jet sounds, vehicle sounds, Czech vehicles, PER marching |
| `MD animations`       | Vehicle/aircraft engine loops and weapon fire | Helicopter engines, tank engines, autocannons, CIWS, rifles             |
| `MD ambient battle`   | Ambient battle layer                          | Empty (compressor-only, applied to ambient sounds)                      |
| `MD EH static effect` | Event Horizon static noise                    | `EH_static`                                                             |

### Global compressors

- `master_compressor` — applied to all sound effects
- `music_compressor` — applied to all music

Per-category compressors override these for the sounds in that category.

## Combat sounds (`combat_sounds/MD4_combat_sounds.txt`)

Maps unit types to sound effects that play during battle animations:

```
infantry_sound = {
    sound_effect = "infantry_rifle_layers"
    units = { infantry paratrooper mountaineers marine motorized }
    divisions_range = { 5 -1 }
}
```

| Field             | Purpose                                                    |
| ----------------- | ---------------------------------------------------------- |
| `sound_effect`    | Name of the soundeffect to play                            |
| `units`           | Unit types that trigger this sound                         |
| `divisions_range` | Min/max divisions for the sound to trigger (`-1` = no max) |

## Country voicelines

MD replaces all vanilla DLC voiceover packs (`dd_vo.asset`, `lar_vo.asset`, etc. are blanked) with custom per-country voicelines in `vo.asset`.

### Voiceline types

Each country has 5 voiceline types that play when the player interacts with units:

| Soundeffect name               | Trigger                                    |
| ------------------------------ | ------------------------------------------ |
| `TAG_infantry_idle`            | Unit selected while idle                   |
| `TAG_infantry_neutral_combat`  | Unit selected during neutral/losing combat |
| `TAG_infantry_positive_combat` | Unit selected during winning combat        |
| `TAG_infantry_move_out`        | Unit given a move order                    |
| `TAG_infantry_retreat`         | Unit retreating                            |

### Countries with voicelines

23 countries currently have custom voicelines:

ARM, AST, BRA, CHI, ENG, FRA, GER, GRE, HEZ (Hezbollah, shares `leb/` directory),
IRQ, ITA, KUW, LEB, MEX, PER, POR, RAJ, SAU, SOV, SPR, TUR, UKR, USA

Plus ZOM (zombie, special/joke).

### Voiceline file naming

WAV files use a lowercase country abbreviation prefix:

```
sound/<tag>/<prefix>_<type>_<NNN>.wav
```

Examples: `us_idle_001.wav`, `us_move_003.wav`, `gr_positive_007.wav`

The prefix is **not always the tag** — it may be an abbreviation (e.g., `us` for USA, `pe` for PER, `gr` for GRE, `as` for AST).

### Voiceline structure in `vo.asset`

Three layers:

1. **Category block** — a `Voices` category listing all `TAG_infantry_*` soundeffect names
2. **Sound definitions** — `sound = { name = "xx_type_NNN" file = "tag/xx_type_NNN.wav" }` entries
3. **Soundeffect definitions** — `soundeffect = { name = TAG_infantry_type ... }` grouping the sounds

Example soundeffect:

```
soundeffect = {
    name = "USA_infantry_idle"
    sounds = { sound = us_idle_001 sound = us_idle_002 sound = us_idle_003 ... }
    max_audible = 1
    max_audible_behaviour = fail
    volume = 0.65
    volume_random_offset = { -0.15 0.15 }
    playbackrate_random_offset = { -0.15 0.15 }
    prevent_random_repetition = yes
}
```

### Adding voicelines for a new country

1. **Record/source WAV files** — see audio requirements below.
2. **Create directory** `sound/<tag_lowercase>/` and place WAV files there.
3. **Add sound definitions** to `vo.asset`:
   ```
   sound = { name = "xx_idle_001" file = "tag/xx_idle_001.wav" }
   ```
4. **Add soundeffect definitions** to `vo.asset` for each of the 5 types:
   ```
   soundeffect = {
       name = "TAG_infantry_idle"
       sounds = { sound = xx_idle_001 sound = xx_idle_002 ... }
       max_audible = 1
       max_audible_behaviour = fail
       volume = 0.65
       volume_random_offset = { -0.15 0.15 }
       playbackrate_random_offset = { -0.15 0.15 }
       prevent_random_repetition = yes
   }
   ```
5. **Add to the Voices category** in `vo.asset` (the category block at the top):
   ```
   TAG_infantry_idle
   TAG_infantry_neutral_combat
   TAG_infantry_positive_combat
   TAG_infantry_move_out
   TAG_infantry_retreat
   ```

## Technical requirements for audio files

| Property    | Sound effects | Voicelines   | Music                      |
| ----------- | ------------- | ------------ | -------------------------- |
| Format      | WAV           | WAV          | OGG (Vorbis)               |
| Channels    | Mono          | Mono         | Stereo                     |
| Sample rate | 44100 Hz      | 44100 Hz     | Any (44100 Hz recommended) |
| Bit depth   | 32-bit float  | 32-bit float | N/A (OGG handles this)     |
