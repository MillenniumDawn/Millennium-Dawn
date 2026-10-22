# Music System Reference

A track must appear in both a definition file, which declares its audio file, and a
playlist, which declares when it plays. Sound effects and voicelines are in
`sound-system.md`.

## Definitions (`music/*.asset`)

```
music = { name = "My Song Title" file = "My_Song_Title.ogg" volume = 1.0 }
```

- `.asset` files are not Paradox script.
- Song names are case-sensitive and at most 63 characters.
- The `.ogg` path is relative to the directory holding the `.asset`.
- `volume` 1.0 is neutral.

## Playlists (`music/*.txt`)

```
music_station = "Station Name"

music = {
    song = "My Song Title"         # must match a name in an .asset file
    chance = {
        base = 15
        modifier = { has_war = yes add = -15 }
        modifier = { threat > 0.4 add = -10 }
    }
}
```

- The weight is `base` plus every matching `add`, then multiplied by every matching
  `factor`. Zero or less means the track is skipped. Playlists are re-evaluated as game
  state changes.
- Common triggers: `has_war`, `threat`, `original_tag`, `surrender_progress`,
  `has_government`, `has_war_with`.
- Separator entries such as `"--ASIAN PLAYLIST--"` have zero weight and never play. They
  still need a matching `.asset` entry.

War track:

```
music = {
    song = "My War Track"
    chance = {
        base = 0
        modifier = { has_war = yes add = 35 }
        modifier = { surrender_progress > 0.5 add = 20 }
    }
}
```

Regional track:

```
music = {
    song = "My Regional Track"
    chance = {
        base = 0
        modifier = { OR = { original_tag = JAP original_tag = CHI original_tag = KOR } add = 60 }
        modifier = { has_war = yes add = -60 }
    }
}
```

## Stations

| Station              | Playlist                               | Content                              |
| -------------------- | -------------------------------------- | ------------------------------------ |
| `MD_Soundtrack`      | `MD_songs.txt`                         | General tension, war, and peace      |
| `MD_main_music`      | Inline in `Main Music/` asset          | European calm, tension, and war      |
| `MD_regional_music`  | `MD_regional_music.txt`                | Asian and Middle Eastern, by tag     |
| `MD_ukrwar_music`    | `UKR-RUS war/MD_ukraine_war_music.txt` | Ukraine and Russia war tracks        |
| `MD_synthwave_music` | `Synthwave/MD_synthwave.txt`           | Always on, every track at `base = 1` |
| `base_music`         | `_songs.txt`                           | Vanilla and integrated-DLC tracks    |

Add artist attribution for original or licensed music to the `Credits.txt` beside the
`.asset`.

## Paid DLC playlists

Do not copy paid-DLC playlist or asset files into MD under their vanilla filenames. Mod
files load regardless of DLC ownership, so an override references assets and station
GUI components that non-owners lack. The engine resolves those references before
evaluating `chance`, so a `has_dlc` modifier does not prevent the errors. Integrated-DLC
playlists are safe to adapt.

If a paid-DLC playlist references vanilla scripted triggers or focus ids that an MD
`replace_path` removed, keep those identifiers in an MD compatibility file. Scripted
triggers keep their vanilla conditions. Focus ids are registered as unattached shared
focuses so they cannot alter a playable tree.

## Troubleshooting

1. The playlist song name must match the `.asset` name exactly.
2. The file must exist and be valid OGG. Bad files are skipped silently.
3. Check the weight. Test with `base = 15` and no modifiers.
4. Check that the station is active for the country.

## Radio station GUI

A station with an in-game faceplate needs:

1. A `.gui` file in `interface/` with `<station>_faceplate` and
   `<station>_stations_entry` containers.
2. A two-frame sprite for the album art under `gfx/interface/topbar/musicplayer/`.
3. A localisation entry for the station name.
