# Music System Reference

How Millennium Dawn organises music and how to add new tracks.

## File types

| Type                 | Location              | Purpose                                                                        |
| -------------------- | --------------------- | ------------------------------------------------------------------------------ |
| **Music definition** | `music/*.asset`       | Maps a logical `song` name to an actual `.ogg` audio file                      |
| **Playlist**         | `music/*.txt`         | Declares which songs belong to which `music_station` and when they should play |
| **Credits**          | `music/*/Credits.txt` | Attribution for artists whose music is used in each station                    |

## How it works

The game has multiple independent `music_station` channels. At any moment, one song
is chosen from the active station based on weighted chance. Playlists are evaluated
continuously — a song that was unavailable may become eligible as game state changes.

A track must appear in **both** a definition file (to declare its audio file) and a
playlist file (to declare when it plays). Neither alone is sufficient.

## Music definition (`.asset` files)

Each `music = { name = "Song Name" file = "filename.ogg" volume = X }` entry registers
the logical name and links it to the physical audio file. These files are NOT Paradox
script — they are parsed separately. Every unique `song` name referenced in any `.txt`
playlist must have a matching entry in one of the `.asset` files.

**Name limit:** song IDs cannot exceed 63 characters.

**Audio format:** `.ogg` (Vorbis). Place the file in the same directory as the `.asset`
that references it, or use a relative path from the `music/` root.

Key definition files for MD content:

| File                                              | Songs it contains                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `music/MD_music.asset`                            | Main MD soundtrack (main theme, modern warfare, tension, commercials)                       |
| `music/Main Music/MD_main_music.asset`            | Main Music station (EU calm/tension/war tracks by Karel Antonin, Voyager, Matt Ragan, etc.) |
| `music/Asian/MD_asian_music.asset`                | Asian regional music (calm/tension/war for East Asian countries)                            |
| `music/Middle East/MD_middle_eastern_music.asset` | Middle Eastern regional music (calm/tension/war + jihad nasheeds)                           |
| `music/UKR-RUS war/UKR_RUS_war_music.asset`       | Ukraine-Russia war station (UKR and SOV/separatist tracks)                                  |
| `music/Synthwave/MD_synthwave.asset`              | Synthwave station tracks                                                                    |
| `music/music.asset`                               | Vanilla HOI4 soundtrack definitions                                                         |

## Playlist (`.txt` files)

```
music_station = "Station Name"

music = {
    song = "Logical Song Name"     # must match a name= in an .asset file
    chance = {
        base = N                   # base weight (can be 0)
        modifier = { add = N ... } # trigger-based adjustments
        modifier = { factor = N ... } # multiplier adjustments
    }
}
```

### How chance weights work

The game sums all `base` + `modifier { add = N }` values from every matching modifier.
`factor` multiplies the final sum. Higher total weight = more likely to be selected.
If a track's total weight is 0 or negative it is skipped.

### Common trigger patterns

| Trigger                    | Effect                                                |
| -------------------------- | ----------------------------------------------------- |
| `has_war = yes`            | Increases weight during wartime                       |
| `threat > 0.4`             | Increases weight when global threat is high           |
| `original_tag = TAG`       | Increases weight for a specific country               |
| `surrender_progress > 0.5` | Increases weight when a country is losing badly       |
| `has_government = fascism` | Increases weight for specific ideology                |
| `factor = 0`               | Disables the track entirely (0 weight overrides base) |

### Sentinel / separator songs

Some playlists use fake `song` entries with descriptive names (e.g., `"--ASIAN PLAYLIST--"`,
`"--UKRAINE PLAYLIST--"`, `"--RUSSIAN PLAYLIST--"`) and `base = 0` or negative weight as
visual separators. These never play — they are comments-in-disguise. They require a matching
`name=` in an `.asset` file to avoid parse errors, but the `.asset` entry can point to any
valid `.ogg`.

## Music stations in MD

| Station              | Playlist file                                        | Asset file                                                                | Purpose                                                                                |
| -------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `MD_Soundtrack`      | `MD_songs.txt`                                       | `MD_music.asset`                                                          | Main MD soundtrack — general tension, war, peace, USA-specific tracks, commercials     |
| `MD_main_music`      | (inline in asset)                                    | `Main Music/MD_main_music.asset`                                          | European-style calm/tension/war tracks                                                 |
| `MD_regional_music`  | `MD_regional_music.txt`                              | `Asian/MD_asian_music.asset`, `Middle East/MD_middle_eastern_music.asset` | Asian and Middle Eastern regional tracks, triggered by `original_tag`                  |
| `MD_ukrwar_music`    | `UKR-RUS war/MD_ukraine_war_music.txt`               | `UKR-RUS war/UKR_RUS_war_music.asset`                                     | Ukraine and Russia/separatist war tracks, triggered by `original_tag` + `has_war_with` |
| `MD_synthwave_music` | `Synthwave/MD_synthwave.txt`                         | `Synthwave/MD_synthwave.asset`                                            | Always-on synthwave ambient music (equal weight)                                       |
| `MD_fm_habibi`       | `MD_fm_habibi.txt`                                   | —                                                                         | Israeli music (currently commented out / disabled)                                     |
| `base_music`         | `_songs.txt`, `dod_songs.txt`, `got_songs.txt`, etc. | `music.asset`, `music_bba.asset`                                          | Vanilla HOI4 soundtrack (DLC-gated)                                                    |

All stations play simultaneously — the game mixes or crossfades between them.
Regional stations use `original_tag = TAG` triggers to target specific countries.

## Adding a new track

Two steps are required:

### Step 1 — Register in a music definition file

Add to the appropriate `.asset` file:

```
music = {
    name = "My Song Title"
    file = "My_Song_Title.ogg"
    volume = 1.0
}
```

`volume` controls playback loudness relative to other tracks. 1.0 is neutral; values
above 1.0 amplify the track, below 1.0 quiet it.

Place the `.ogg` file in the same directory as the `.asset` file.

### Step 2 — Add to a playlist with appropriate triggers

Add to the relevant `.txt` playlist file. Choose the station and triggers based on
the track's mood and intended scope:

- **General soundtrack** (`MD_songs.txt` / `MD_Soundtrack`) — for tracks that fit any nation
- **Main music** (`Main Music/`) — for European-style calm/tension/war tracks
- **Regional** (`MD_regional_music.txt`) — for country-specific regional music (Asian, Middle Eastern)
- **UKR-RUS war** (`UKR-RUS war/MD_ukraine_war_music.txt`) — for Ukraine/Russia conflict tracks
- **Synthwave** (`Synthwave/MD_synthwave.txt`) — for always-on ambient synthwave
- **Vanilla base** (`_songs.txt` / `base_music`) — for vanilla tracks that MD reuses

Example — adding a general peace track:

```
music = {
    song = "My Song Title"
    chance = {
        base = 15
        modifier = {
            has_war = yes
            add = -15
        }
        modifier = {
            threat > 0.4
            add = -10
        }
    }
}
```

Example — adding a war track:

```
music = {
    song = "My War Track"
    chance = {
        base = 0
        modifier = {
            has_war = yes
            add = 35
        }
        modifier = {
            surrender_progress > 0.5
            add = 20
        }
    }
}
```

Example — adding a country-specific regional track:

```
music = {
    song = "My Regional Track"
    chance = {
        base = 0
        modifier = {
            OR = {
                original_tag = JAP
                original_tag = CHI
                original_tag = KOR
            }
            add = 60
        }
        modifier = {
            has_war = yes
            add = -60
        }
    }
}
```

Example — adding a UKR-RUS war track (boosted during active conflict):

```
music = {
    song = "My War Song"
    chance = {
        base = 0
        modifier = {
            original_tag = UKR
            add = 1
        }
        modifier = {
            OR = {
                has_war_with = SOV
                has_war_with = DPR
                has_war_with = LPR
            }
            original_tag = UKR
            add = 45
        }
    }
}
```

### Step 3 — Update credits (if applicable)

If the track is original or licensed music, add the artist attribution to the
`Credits.txt` file in the same directory as the `.asset` file:

```
# Track Title - Artist Name
```

## Synthwave station

`music/Synthwave/` holds the `MD_synthwave_music` station. It plays all tracks at equal
base weight (1) regardless of game state — always-on ambient music. Tracks are defined
in `MD_synthwave.asset` and listed in `MD_synthwave.txt`.

To add a new synthwave track, add both an `.asset` entry and a playlist entry with
`base = 1` and no modifiers.

## Troubleshooting missing music

If a song does not play:

1. **Verify the song name in the playlist exactly matches the `name=` in the `.asset`
   file** — the lookup is case-sensitive.
2. **Verify the audio file exists and is a valid OGG** — invalid or missing files are
   silently skipped.
3. **Check the chance weight** — if all modifiers evaluate to 0 or negative, the track
   is never selected. Try setting `base = 15` and removing restrictive modifiers to
   test.
4. **Check the music station** — if the station is not active (e.g., regional trigger
   not matched), no tracks from it will play.
5. **Check the file path** — `.asset` file paths are relative to the directory containing
   the `.asset` file, not the `music/` root.

## Radio station GUI

A music station can have an in-game radio faceplate UI. This requires:

1. A `.gui` file in `interface/` defining `containerWindowType` elements for the
   faceplate (`<station>_faceplate`) and station entry (`<station>_stations_entry`).
2. A sprite definition for the station button's album art in `interface/*.gfx`:
   ```
   spriteType = {
       name = "<SPRITE>"
       texturefile = "gfx/interface/topbar/musicplayer/<FILE NAME>.dds"
       noOfFrames = 2
   }
   ```
3. A localisation entry mapping the station name to display text:
   `<STATION>:0 "Station Name"`

Sound effects and voicelines are documented in `.claude/docs/sound-system.md`.
