# Console Commands

Console commands are split into two categories: actual commands and tweakable
variables.

Tweakable variables differ from console command in that they are more
specialized and usualy modify a single variable in the game. They are often
used to toggle on or off some behavior.

Console command are more general purpose and can affect a wider variety of
stuff, such as reloading some file, toggling off some gfx effects, starting
a civil war, ...

## Table of Content

* [All Console Commands](#all-console-commands)
* [All Tweakable Variables](#all-tweakable-variables)

## All Console Commands

### 3dstats

Toggles 3D Stats

### Agency.Instant

Activates Operation.Instant, IntelNetwork.Instant, Agency.InstantSlotUnlock and Agency.Autocomplete

### CrashReporter.DeleteCrashData

Delete local crash dumps older than X days.

### CrashReporter.SimulateCrash

Simulates a crash (resulting in the game exiting).

### CrashReporter.UploadCrash

Upload the latest crash dump.

### IP

Shows your IP

### PostEffectVolumes.Default
* Arguments: posteffect_values name
* Not available in release build

Toggles default posteffect values

### PrintSynchStuff

Prints random count and seed

### SetRandomCount

Sets the randomcount to 0 or arg

### acclimatization
* Aliases: acc
* Arguments: \<climate_name\>, \<value 0-100\>

Sets the acclimatization on a division(s).

### add_autonomy
### add_core
* Arguments: \<Province ID\>

Add core

### add_critical_hit
* Arguments: \<critical_hit_name\>

add critical hit to selected ships

### add_diplo

Adds diplomatic entroute

### add_equipment
* Aliases: ae
* Arguments: equipment amount, equipment name

Gives player amount of equipment that has the specified name

### add_exile_manpower
* Arguments: \<TAG\>, \<value\>

Adds legitimacy to specified tag. add_legitimacy TAG amount

### add_fake_armies

Creates fake intel armies for the player

### add_fleet_arrow
* Arguments: color
* Not available in release build

Add an arrow around a strategic region

### add_ideas

Adds ideas (ministers or national spirits) with \<ID\> to the country. Use 'all' to add them all

### add_intel

Set the values of a static intel pool against a specific country. E.g. `add_intel GER POL army=10`

### add_interest
* Arguments: \<Country tag\>

Add specified country tag to your interest

### add_latest_equipment
* Aliases: ale
* Arguments: equipment amount

Gives player amount of latest equipment variants

### add_legitimacy
* Arguments: \<TAG\>, \<value\>

Adds legitimacy to specified tag. add_legitimacy TAG amount

### add_mines
* Aliases: mines
* Arguments: \<Amount of naval mines\>

Add naval mines to selected region(s)

### add_opinion
* Arguments: \<Country tag\>

Add opinion to/from tag

### add_party_popularity
* Arguments: \<party\>, \<amount\>

Adds party popularity for specified party to the current country

### add_stability
* Aliases: st
* Arguments: unity amount

Gives/removes stability from player

### add_temporary_buff
* Arguments: \<buff_index\>

adds temporary buff to selected units

### add_war_support
* Aliases: ws
* Arguments: unity amount

Gives/removes war support from player

### ai

Toggles the AI on or off

### ai_accept
* Aliases: yesman

Toggles AI always accept diplomacy

### ai_dump
* Aliases: aidump
* Not available in release build

Dump AI data to log file

### ai_force_equipment

Force the AI to only spend army XP on equipment design

### ai_force_template

Force the AI to only spend army XP on template design

### ai_front_dump
* Aliases: aifrontdump
* Not available in release build

Dump AI front data to log file, needs to have a unit selected

### ai_front_id

Get the address of selected group's front debug id

### ai_idea_desire_log

Prints AI desire for ideas to log. For Current country only.

### ai_invasion

Toggles AI AI naval invasions

### ai_pp_log

Prints AI use of PP to log

### ai_research_log
* Not available in release build

Toggles ai research logging

### ai_trace
* Not available in release build

Toggles the AI Trace window

### aircombat
* Aliases: airc
* Arguments: \<scenario name\>, \<result name\>, \<province id\>, \<state id with airbase\>, \<state id with airbase\>, \<equipment type\>, \<equipment type\>, [equipment creator country], [equipment creator country]
* Not available in release build

Spawns an air combat in desired location.

### airealism

Enable realistic AI

### aiview

Enable AI debug info

### allowdiplo
* Aliases: adiplo, nocb

Allows to use all diplomatic actions for no matter the rules.

### allowideas

Allows to learn all ideas.

### allowoperations

Allows to execute all operations.

### allowtraits

Allows to learn all traits.

### analyzetheatres
* Aliases: anth

Analyze theatres for errors.

### annex
* Arguments: \<Target Country Tag\>

Begin annex/annexes the specified tag

### bloom
* Not available in release build

Toggles bloom

### browser
* Arguments: url
* Not available in release build

Show browser window

### build_war_blobs

Prints a list of all your wars

### building_health
* Aliases: bhealth
* Arguments: \<building type\>, \<state or prov id\>, \<building level\>, \<health to add\>

Changes specified building health

### bypass_invasion_superiority_check
* Aliases: bisc

Ignore superiority in the strategic areas crossed by a naval invasion order

### cameraclamp
* Not available in release build

Toggles the camera clamping

### cityreload

Reloads the cities

### civilwar
* Arguments: \<ideology\>, [target country tag]

Spawns a civil war

### clear_critical_hits

clear all critical hits

### clear_intel_pools

Reset the specified intel pool

### collaboration

Adds collaborations against selected country. Right click to select a country and use "collaboration 0.3"

### collision
* Aliases: debug_collision

Toggles debug display of normals/bounding boxes/collision

### combat_analyzer
* Arguments: \<TAG1\>, \<TAG2\>, \<OOB1\>, \<OOB2\>, \<num runs\> OPTIONAL, \<num days\> OPTIONAL

Runs a combat between the 2 OOBs owned by the two TAGs either until done or for the specified number of days. 
Using \<num runs\> the combat will be run multiple times and the averages are printed

### combatsound

How often does the combat view give a random sound? 0-50

### combattest
* Not available in release build

combat simulation process

### compare_to_last_checksum

Compare current checksum with the most recent dump

### compliance
* Arguments: amount

increases decreases compliance in a state

### cp
* Arguments: CP amount

Gives command power to player

### createarmygroup

Create field marshal group from selected groups

### createlean
* Not available in release build

Create LEAN textures

### ct

Puts timer info in clipboard

### damage_units
* Arguments: \<org\>, \<str\>, \<num\>

Damage or heal selected units or units under pointer if there is none selected. Enter 1 argument to apply damage for both types, two for individual both types

### dbg_enable_scripted_gui
* Arguments: \<scope\>
* Not available in release build

Enables scripted GUIs

### dbg_prov
* Arguments: \<int\>
* Not available in release build

Sets type of debugging information on provinces.

### dbg_task_force_role_insignia_assignment
* Aliases: tfria

print the role that would be deduced for the selected task force

### dbg_tf_fulfillment

Show the managed fulfillment of a taskforce (exepected number of ships after all ships have been merged in)

### debug

Toggle debug mode on/off.

### debug_achievements
* Not available in release build

Enables popups for achievements to debug them

### debug_achievements_clear
* Not available in release build

Clear all achievements and user stats

### debug_air_vs_land
* Aliases: dbg_cas
* Not available in release build

Toggle debug mode for air vs land combat.

### debug_army_entity
* Aliases: dae

Shows debug entity for all armies

### debug_assert
* Not available in release build

Toggles asserts on/off

### debug_bloom

Toggles Bloom on/off

### debug_borders

Toggles Borders on/off

### debug_cities

Toggles Cities painting mode on/off

### debug_commands
* Not available in release build

Printing commandcount to message.log

### debug_crash
* Aliases: crash
* Not available in release build

Crash!

### debug_diploactions
* Not available in release build

Start Counting diplomatic actions

### debug_dumpdiploactions
* Not available in release build

Dump diplomatic action data to game log

### debug_dumpevents

Dump Event data to game log

### debug_entities
* Not available in release build

Toggles Debug entities

### debug_events

Start Counting events

### debug_force_capitulate
* Aliases: dfc
* Arguments: \<tag\>

forces capitulation of a country on next daily tick

### debug_front_sections
* Aliases: dbg_fs
* Arguments: \<Theatre index\>, \<Front index\>, \<Section index\>

Visual debug of theatres, fronts and sections.

### debug_fronts
* Not available in release build

Toggles interpolated fronts debug

### debug_info
* Not available in release build

Toggles Debug info

### debug_lines
* Not available in release build

Toggles Debuglines

### debug_lockcamera
* Not available in release build

Toggles Camera locked on/off

### debug_nogui

Toggles GUI on/off

### debug_nomouse
* Not available in release build

Toggles mouse scrollwheel on/off

### debug_norender

Toggle rendering of map

### debug_nuking

Allows to nuke every province without checking any conditions.

### debug_off_front_snap
* Aliases: dbg_fsnap
* Not available in release build

Toggles offensive fronts snapping debug

### debug_orders_tree
* Aliases: dot
* Not available in release build

Print out debug about orders chain.

### debug_particle
* Not available in release build

Toggles Particles Debug info

### debug_postfx

Toggles PostFX on/off

### debug_rivers

Toggles Rivers on/off

### debug_show_event_ID

Shows event ID

### debug_sky

Toggles Sky on/off

### debug_smooth

Toggle framesmoothing

### debug_tactics

Toggle visibility of debug tooltip for tactics

### debug_terrain

Toggles Terrain on/off

### debug_texture
* Not available in release build

draws textures like bloom

### debug_textures
* Not available in release build

Writes Texture info to application debug log

### debug_tooltip
* Not available in release build

Toggles Tooltips on/off

### debug_trees

Toggles Trees on/off

### debug_types
* Not available in release build

Will print the data type for all dynamic reference objects. Can only be used if using RTTI.

### debug_unit_controller_weights
* Aliases: dbg_ucw
* Arguments: \<weight token\>

Visual debug of unit controller weights. Enable track_unit_controller_weights first!

### debug_unit_entity
* Aliases: dbg_ue

Print out the entity hierarchy.

### debug_volume
* Arguments: \<Volume Delta\>
* Not available in release build

Modifies music volume

### debug_water

Toggles Water on/off

### debug_wireframe
* Not available in release build

Toggles forced wireframe on/off

### debug_zoom
* Not available in release build

Zooms in the game

### deironman
* Not available in release build

Removes Ironman status from current game.

### deleteallunits
* Aliases: delall

Delete all armies and fleets of the specified countries.

### deleteallunitsbut
* Aliases: delallbut

Delete all armies and fleets of ALL countries, except specified one.

### deltat
* Arguments: \<speed factor\>

control animation speeds

### drop_cosmetic_tag
* Arguments: \<country tag\>

Drops 'cosmetic tag' for a specified country

### dump_cached_random_logs

dumps cached random logs

### dump_checksum

Compute and store the checksum in a file

### dump_synchronized_members

Dump the synchronized game state (the one that has checksum ID 2)

### effect
* Aliases: e
* Arguments: \<tag\> scripted_effect_name

Runs a scripted effect on selected scope

### empty_fuel_tanks
* Arguments: Fuel amount

Clear fuel tanks of all armies

### emulate_ai_operative_assignment

Log ai operative assignment if it were to run this tick. Takes as first argument the tag of the country to test, default to the player's.

### error

Show errors in log

### eval_effect

Runs the inlined effect on a selected scope

### event
* Arguments: event id, \<Target Country Tag\>

Executes an event

### flagsoutput
* Arguments: \<path\>

Creates texture atlas files from memory.

### force_operative_detection
* Aliases: snitch

Print intel network related information

### fow
* Aliases: debug_fow
* Arguments: \<Province ID\> OPTIONAL

Turns off fog of war in a province or in general

### fronts

Toggle visibility of the foreign fronts

### fuel
* Aliases: army_juice
* Arguments: Fuel amount

Adds/removes fuel to the player

### fuel_gain
* Arguments: Daily Fuel amount

Adds/removes daily fuel gain for player

### fullscreen

Toggles fullscreen

### gain_xp
* Arguments: \<trait\>

Gain xp for selected leader or for a leader trait

### gamespeed
* Arguments: speed \<0-5\>

Set the current game speed, pausing the game at speed 0.

### gamestate_timer
* Aliases: gstimer
* Arguments: on / off

Enable / Disable recording of how long an hour / day / week etc takes to process.

### gbpaint
* Arguments: layer, channel
* Not available in release build

Toggles gradient border painting

### gbreload
* Not available in release build

Reloads gradient borders

### get_capital
* Arguments: \<Country tag\>

Get the capital of a country

### get_country_flag
* Arguments: \<flag name\>

Gets country flag on specified TAG. Defaults to current country

### get_flag
* Arguments: \<flag name\>

Get a flag

### get_var
* Arguments: \<var name\>

Gets a variable

### goto_province
* Arguments: province id

Centers to province

### goto_region
* Arguments: region id

Centers to region

### goto_state
* Arguments: state id

Centers to state

### grow_intel_network

Grow the intel network in the specified tag

### guibounds
* Aliases: gui

Toggles GUI bounds debug

### hdr
* Not available in release build

Toggles hdr

### hdr_debug
* Not available in release build

Toggles hdr debugging

### help
* Arguments: command name

Print out all console commands or a specific command description.

### helphelp

Double Rainbow help.

### helplog

Print out all console commands to game.log file.

### highlight_encirclements

Toggle highlighting of detected encirclements

### history_logger

Toggle history logger

### hsv
* Not available in release build

Converts RGB to HSV

### human_ai

Toggles AI for Human countries

### imgui

Controls ImGui UIs. See the sub commands.

### instant_prepare

Instantly prepares naval invasions

### instant_wargoal

Generation of wargoals are instant

### instantconstruction
* Aliases: ic

Toggles instant construction cheat.

### instantevents

Ignores event mth s

### instantshiprefit
* Aliases: isr

Toggles instant ship refitting cheat.

### instanttraining
* Aliases: it

Toggles instant army training cheat.

### ironman
* Not available in release build

Applies Ironman status to current game.

### list_flags
* Arguments: \<scope\>

Lists all flags in a scope or for the selected country/state/unitleader

### list_ideas

Dump all ideas to console (ministers or national spirits)

### list_modifiers
* Arguments: \<scope\>

Lists all modifiers in a scope or for the selected country/state/unitleader

### list_temporary_buffs

lists all temporary buffs on selected units

### list_vars
* Arguments: \<scope\>

Lists all variables in a scope or for the selected country/state/unitleader

### lock_air_det
* Arguments: \<CountryTag\>, \<Detection\> (0.0-1.0) OPTIONAL

Locks Air Detection for a country, omit detection value to reset

### lock_air_eff
* Arguments: \<CountryTag\>, \<Efficiency\> (0.0-1.0) OPTIONAL

Locks Air Efficiency for a country, omit efficiency value to reset

### manpower
* Arguments: \<Amount\>

Adds manpower to player

### map_icon_reload_type
* Arguments: \<NUM\> or \<help\>
* Not available in release build

Specify a map icon type to reload

### mapmode
* Arguments: Mapmode type (int)

Change mapmode.

### mapnames

Toggle map names

### massconquer
* Aliases: massc
* Not available in release build

Mass conquer tool.

### metrics
* Not available in release build

Toggles collecting metrics

### morehumans
* Aliases: humans
* Arguments: num

Adds more humans

### moveunit
* Arguments: \<Unit ID\>, \<Province ID\>

Moves a unit to a province

### navalcombatlog
* Not available in release build

logs naval combat

### night
* Not available in release build

Toggles night

### no_wargoal

No need to have a wargoal for declaring war

### nomapicons

Toggles map icons.

### nopausetext

Toggles the pausebanner for nicer screenshots.

### nudge

Go to the nudge tool

### nukes
* Aliases: nuke
* Arguments: \<count\>

add nukes

### observe
* Aliases: spectator

Switches to play no country at all, and no longer shows messages or pauses the game

### occupationpaint
* Aliases: op
* Arguments: tag\<OPTIONAL\>

Toggles occupation painting. If specifying a tag, that country will be occupied.

### oos
* Not available in release build

Out of Synch

### operation_debug

Allows to execute all operations.

### operation_start

Allows to execute all operations.

### operation_test_phase_selection

Test an operation phase.

### particle_editor

Spawns a particle editor

### pathfind_cache
* Arguments: on / off
* Not available in release build

Enable / Disable the PathFind Cache

### pathfind_stats
* Not available in release build

Print PathFind Cache Stats

### pause_in_hours

Pauses the game after X hours have passed after command is called

### pdxmp_netstats

Reports PDX MP network statistics

### pdxmp_status

Reports whether PDX MP is online and connected.

### pops_account_login
* Arguments: email, password
* Not available in release build

Login to a POPS Account

### pops_account_logout
* Not available in release build

Login to a POPS Account

### pops_account_status
* Not available in release build

Show whether you are currently logged into POPS or not.

### pp
* Aliases: fuhrer_mana, political_power
* Arguments: PP amount

Gives political power to player

### prep_for_war
* Arguments: \<TAG\>

Make AI country with specified TAG to prepare fight for another country 

### prevent_operative_detection

Prevent a country from detecting and harming foreign operatives

### prices

Price Info

### print_intel_network

Print intel network related information

### print_intel_values

Print the intel a country has over another

### print_operation_tokens

Runs a scripted effect on selected scope

### print_radar_intel

Print the intel value breakdown generated by radar

### profile
* Arguments: \<on\> \<off\> \<print\> \<clear\>

profile options

### profilelog
* Not available in release build

Prints out the profiling informations into time.log

### provtooltipdebug
* Aliases: tdebug

Toggles the debug info in province tooltip

### random_seed

reseeds random with specified seed or reseeds random

### randomlog
* Aliases: rlog
* Not available in release build

Toggles the random logs.

### rebuildfronts
* Arguments: \<Country tag\>
* Not available in release build

Rebuild fronts.

### rebuildlayers

Reload mapmodes.

### release
* Aliases: rls
* Arguments: Tag of a country to be released

Released a given country

### reload
* Arguments: file name

Reloads assets

### reload_textures
* Aliases: rt, reload_texture
* Arguments: \<optional file name filters...\>

Reloads all textures, with an optional filter to reload only files that include the given text

### reloadfx
* Arguments: Arguments: map/mapname/postfx or *.fx filename

Reloads the shader

### reloadinterface

Reloads the entire interface

### reloadoob
* Arguments: \<Target Country Tag\>

Reloads OOBs

### reloadsupply
* Aliases: relsup

Reinitializes the supply systems.

### reloadtechnologies

Reloads the technology database

### reloadweather
* Arguments: \<randomseed\>

Reload and regenerate weather

### remove_core
* Arguments: \<Province ID\>

Remove core

### remove_ideas

Removes ideas (ministers or national spirits) with \<ID\> to the country. Use 'all' to remove them all

### remove_interest
* Arguments: \<Country tag\>

Removes specified country tag from your interest

### rendertype

Reports what render backend is used

### research
* Arguments: \<slot id\> or "all"

Researches an technology from research slot or all.

### research_on_icon_click

Research a technology when clicking on technology tree icon

### resign

Resign from the game

### resistance
* Arguments: amount

increases decreases resistance in a state

### run

Runs the specified file with list of commands

### save
* Aliases: savegame

save a savegame.

### savecheck

Makes a savegame (Test_01), loads the savegame, makes a new savegame (Test_02). Those savegames should look the same.

### savegame

Creates an savefile.

### select
* Aliases: sel
* Arguments: \<object id\>, \<object type id\> (optional)
* Not available in release build

select object by id

### set_cosmetic_tag
* Arguments: \<country tag\>, \<cosmetic tag\>

Sets 'cosmetic tag' for a specified country

### set_country_flag
* Arguments: \<flag name\>

Sets country flag on specified TAG for a duration. Defaults to current country and value 1 with infinite duration.

### set_debug_unit_controller
* Aliases: dbg_unit_controller
* Not available in release build

Sets debug unit controller tag, other countries will not update units

### set_flag
* Arguments: \<flag name\>

Set a flag

### set_global_flag
* Arguments: \<flag name\>

Sets the specified global flag to a value. Defaults to 1

### set_ruling_party
* Arguments: \<ideology\>

Sets ruling party for the country

### set_var
* Arguments: \<var name\>

Set a variable

### setcontroller
* Arguments: country tag, province id

Sets province controller

### setowner
* Arguments: country tag, state id

Sets state owner

### show_enemy_ships

Toggle always showing of enemy ships

### show_ships

Toggle always showing of player ships

### show_xp_gain
* Aliases: xp_gain

Show XP gain information.

### simplified_transport

Toggle simplified naval transports

### sleep
* Aliases: wait
* Arguments: time in sec
* Not available in release build

Sleep

### social_addfriend
* Arguments: Context Index, Account ID
* Not available in release build

Add a friend to friends list

### social_debuginfo
* Not available in release build

Print debug info about the social layer

### social_joinroom
* Arguments: Context Index, Room Name, Nick Name
* Not available in release build

Join a chat room using the given social context

### social_sendmessage
* Arguments: Context Index, Room Name, Message
* Not available in release build

Send a message to a chat room.

### spawn
* Arguments: \<SubUnit Type\>, \<Province ID\>, \<Amount\>
* Not available in release build

Spawns a unit in a province

### spawnactor
* Arguments: \<Actorname\>, \<Province ID\>, \<Animation\> OPTIONAL
* Not available in release build

Spawns an actor with an optional animation

### srgb
* Not available in release build

Toggles sRGB

### tag
* Arguments: \<Country tag\>

Switch tag to another country

### tag_color

Test setting a country's color

### teleport
* Aliases: tp
* Arguments: \<province_id\>

Teleports selected armies or ships to the specified province

### test_log

Enable / Disable tests

### test_naval_move_danger
* Arguments: \<from region id\>, \<to region id\>, \<avoid as block = 1\>
* Not available in release build

Tests if path between two region is blocked

### test_save_mode

Sets if save game for failed test should be for current or previous day

### testevent
* Arguments: \<Event ID\>, \<Character ID\>

Tests an event without triggering it

### testrtti
* Arguments: \<test case\>

Tests performance for RTTI

### testtool
* Aliases: test
* Not available in release build

Testing tool.

### theatersrebuild
* Aliases: trebuild
* Not available in release build

Rebuilds all theatres in the world. All orders will be cleaned.

### threat
* Arguments: threat amount

Adds or show thread level of player

### time

What time is it?

### timer

Prints out debug timing info

### timer_dump

Dumps debug timing info

### timer_reset

Resets debug timing

### timer_restart

Restarts (resets and starts) debug timing

### timer_start

Starts debug timing

### timer_stop

Stops debug timing

### toggle_offset_ai_daily_update
* Not available in release build

Whether a country's ai daily update should be spread over a day

### track_unit_controller_weights
* Aliases: track_ucw

Will start tracking unit controller weights for current country, should be used together with debug_unit_controller_weights to view the data.

### traderoutes

Toggle visibility of trade routes

### trigger
* Aliases: t
* Arguments: \<tag\> scripted_trigger_name

Runs a scripted trigger on selected scope

### trigger_ability
* Arguments: \<ability_name\>

triggers an ability

### trigger_docs
* Aliases: effect_docs, scripting_docs, docs

Print docs for triggers, effects and variables

### tweakergui

Spawns a tweaker GUI

### unit_address

Get the address of the first selected unit, for debugging

### unit_stats

lists stats of selected units

### update_loc
* Arguments: localization tag

Updates the localization tag file

### updateequipments

Updates the equipment database

### updatesubunits

Updates the subunit database

### version

Show current game version

### war_relations
* Arguments: \<tag\>

Prints war relations info

### weather

Toggle weather simulation

### whitepeace
* Aliases: wp
* Arguments: \<country tags\>

White peace with the specified countries.

### window
* Aliases: wnd
* Arguments: Arguments: open/close, window gui name

Opens or closes the specified window

### xp
* Arguments: XP amount

Gives Army, navy and air experience to player

## All Tweakable Variables


Tweakable variables have a type which defines how they are used.

Boolean variables are toggled on and off just by entering their name in the
console. They can also be force enabled by entering the name of the variable
followed by a none zero number, or force disabled by using zero.

Examples:
```
> Agency.AutoComplete
[ Agency.AutoComplete ] Enabled
> Agency.AutoComplete
[ Agency.AutoComplete ] Disabled
> Agency.AutoComplete
[ Agency.AutoComplete ] Enabled
> Agency.AutoComplete 1
[ Agency.AutoComplete ] Enabled
> Agency.AutoComplete 0
[ Agency.AutoComplete ] Disabled
```

Integer and Float variables are set to a value by entering the name of the
variable followed by the desired value. Only entering the name of the variable
will print its current value. Note that they can be clamped within a range by
code.

Examples:
```
> Audio.Debug.LevelsSampleRate
[ Audio.Debug.LevelsSampleRate ] Value 20
> Audio.Debug.LevelsSampleRate 40
[ Audio.Debug.LevelsSampleRate ] Value 40
> Audio.Debug.LevelsSampleRate
[ Audio.Debug.LevelsSampleRate ] Value 40
```
### Agency.AutoComplete
* Type: Boolean
### Agency.InstantSlotUnlock
* Type: Boolean
### Agency.KeepExcessOperatives
* Type: Boolean
### ApplicationUtils.Update
* Type: Boolean
* Not available in release build
### Audio.Compressor
* Type: Boolean
* Not available in release build
### Audio.Debug
* Type: Boolean
* Not available in release build
### Audio.Debug.ExtendedRange
* Type: Boolean
* Not available in release build
### Audio.Debug.Levels
* Type: Boolean
* Not available in release build
### Audio.Debug.LevelsSampleRate
* Type: Integer
* Not available in release build
### Audio.DebugMax
* Type: Boolean
* Not available in release build
### Audio.DebugMin
* Type: Boolean
* Not available in release build
### BattleSound.Debug
* Type: Boolean
* Not available in release build
### BattleSound.PlayBackground
* Type: Boolean
* Not available in release build
### BorderLOD.Threaded
* Type: Boolean
* Not available in release build
### BoundingVolumes
* Type: Boolean
* Not available in release build
### Collisions
* Type: Boolean
* Not available in release build
### CounterIntelligence.TestShieldColors
* Type: Boolean
### Debug.DeleteUnitEachTick
* Type: Boolean
* Not available in release build
### Decision.NoChecks
* Type: Boolean
### Draw.Borders
* Type: Boolean
* Not available in release build
### Draw.Objects
* Type: Boolean
* Not available in release build
### Draw.Postfx
* Type: Boolean
* Not available in release build
### Draw.Refractions
* Type: Boolean
* Not available in release build
### Draw.Rivers
* Type: Boolean
* Not available in release build
### Draw.ShadowBlur
* Type: Boolean
* Not available in release build
### Draw.Shadows
* Type: Boolean
* Not available in release build
### Draw.Terrain
* Type: Boolean
* Not available in release build
### Draw.Transparent
* Type: Boolean
* Not available in release build
### Draw.Tree
* Type: Boolean
* Not available in release build
### Draw.Water
* Type: Boolean
* Not available in release build
### Focus.AutoComplete
* Type: Boolean
### Focus.IgnorePrerequisites
* Type: Boolean
### Focus.NoChecks
* Type: Boolean
### GUI.Wireframe
* Type: Boolean
* Not available in release build
### IntelNetwork.Instant
* Type: Boolean
### Mesh.MipLevels
* Type: Boolean
* Not available in release build
### Mesh.Names
* Type: Boolean
### Mesh.TextureNames
* Type: Boolean
### Mesh.Wireframe
* Type: Boolean
* Not available in release build
### Normals
* Type: Boolean
* Not available in release build
### Operation.Instant
* Type: Boolean
### Particle.MipLevels
* Type: Boolean
* Not available in release build
### Particle.UseRingbuffer
* Type: Boolean
* Not available in release build
### Particle.Wireframe
* Type: Boolean
* Not available in release build
### PostEffectVolumes.Draw
* Type: Boolean
* Not available in release build
### PostEffectVolumes.Enabled
* Type: Boolean
* Not available in release build
### ShowTechBonus
* Type: Boolean
### Terrain.MipLevels
* Type: Boolean
* Not available in release build
### Tree.MipLevels
* Type: Boolean
* Not available in release build
### Update.Animations
* Type: Boolean
* Not available in release build
### Update.Particles
* Type: Boolean
* Not available in release build
### fa
* Type: Boolean
### guibounds
* Type: Boolean
### resistance_system
* Type: Boolean
