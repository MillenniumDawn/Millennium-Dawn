# Sound System Reference

Sound effects, combat sounds, and country voicelines. Music is in `music-system.md`.

## Files

| File                                        | Holds                                          |
| ------------------------------------------- | ---------------------------------------------- |
| `sound/MD4_sound.asset`                     | `sound` definitions: WAV to logical name       |
| `sound/MD4_soundeffects.asset`              | `soundeffect` groupings                        |
| `sound/MD4_category.asset`                  | Categories with compressor settings            |
| `sound/combat_sounds/MD4_combat_sounds.txt` | Unit types to combat sounds                    |
| `sound/vo.asset`                            | Voice category and every country voiceline     |
| `sound/*_vo.asset`                          | Blanked DLC voice packs, replaced by MD's      |
| `sound/<tag>/`                              | Per-country voiceline WAVs (HEZ shares `leb/`) |

`.asset` files are not Paradox script. WAVs for weapons and vehicles are in
`sound/animations/`, UI sounds in `sound/menu/`.

## Formats

```
sound = { name = <name> file = <path under sound/> always_load = <bool> volume = <float> }

falloff = { name = <name> min_distance = <float> max_distance = <float> height_scale = <float> }

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
    max_audible = <int>                  # maximum concurrent instances
    max_audible_behaviour = fail         # reject extras over the cap
    volume = <float>
    fade_in = <float>
    fade_out = <float>
    delay_random_offset = { <float> <float> }
    volume_random_offset = { <float> <float> }
    playbackrate_random_offset = { <float> <float> }
    prevent_random_repetition = <bool>
}

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

- MD falloffs: `falloff_50`, `falloff_100`, `falloff_distance`, `falloff_airplane_light`,
  `falloff_airplane_heavy`.
- MD categories: `Millennium Dawn` (combat sounds), `MD animations` (engine loops and
  weapon fire), `MD ambient battle`, `MD EH static effect`. A category compressor
  overrides the global `master_compressor`.

Combat sounds map unit types to an effect:

```
infantry_sound = {
    sound_effect = "infantry_rifle_layers"
    units = { infantry paratrooper mountaineers marine motorized }
    divisions_range = { 5 -1 }    # min and max divisions, -1 is no max
}
```

## Country voicelines

Each country has five soundeffects in `vo.asset`:

| Soundeffect                    | Plays when                           |
| ------------------------------ | ------------------------------------ |
| `TAG_infantry_idle`            | Unit selected while idle             |
| `TAG_infantry_neutral_combat`  | Selected in neutral or losing combat |
| `TAG_infantry_positive_combat` | Selected in winning combat           |
| `TAG_infantry_move_out`        | Unit given a move order              |
| `TAG_infantry_retreat`         | Unit retreating                      |

WAVs are named `sound/<tag>/<prefix>_<type>_<NNN>.wav`. The prefix is lowercase and not
always the tag (`us` for USA, `pe` for PER, `gr` for GRE).

To add a country:

1. Put the WAVs in `sound/<tag_lowercase>/`.
2. Add a `sound` definition per file to `vo.asset`:
   `sound = { name = "xx_idle_001" file = "tag/xx_idle_001.wav" }`
3. Add the five soundeffects:

```
soundeffect = {
    name = "TAG_infantry_idle"
    sounds = { sound = xx_idle_001 sound = xx_idle_002 }
    max_audible = 1
    max_audible_behaviour = fail
    volume = 0.65
    volume_random_offset = { -0.15 0.15 }
    playbackrate_random_offset = { -0.15 0.15 }
    prevent_random_repetition = yes
}
```

4. Add the five names to the `Voices` category at the top of `vo.asset`.

## Audio requirements

| Property    | Sound effects and voicelines | Music        |
| ----------- | ---------------------------- | ------------ |
| Format      | WAV                          | OGG (Vorbis) |
| Channels    | Mono                         | Stereo       |
| Sample rate | 44100 Hz                     | 44100 Hz     |
| Bit depth   | 32-bit float                 | n/a          |
