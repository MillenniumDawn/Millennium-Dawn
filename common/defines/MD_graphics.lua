
	NDefines.NWiki.BASE_URL = ""
	NDefines.NWiki.FORUM_URL = "https://gitlab.com/Millennium_Dawn/Millennium_Dawn/-/wikis/home"

	NDefines.NMapIcons.STATES_PRIORITY_VICTORY_POINTS = 0

	NDefines.NAirGfx.AIRPLANES_ANIMATION_GLOBAL_SPEED_PER_GAMESPEED = { 0.18, 0.2, 0.2, 0.20, 0.50, 0.85 } -- Speed factor for each game speed (begin with paused). Larger value = faster animation.
	NDefines.NAirGfx.ROCKET_SPEED = 15.0							-- Speed of rockets launched from rocket sites
	NDefines.NAirGfx.AIRPLANES_CURVE_POINT_DENSITY = 5.0 			-- Higher value = more midpoints in the flight path.
	NDefines.NAirGfx.AIRPLANES_CURVE_MAX_EXTRAPOLATION = 30.0 		-- It's the limit value that avoid making gigantic curves that may happen when flight path is very long.
	NDefines.NAirGfx.AIRPLANES_CURVE_MIN_ELEVATION = 4.0 			-- Minimum height above the ground that the curve will generate it's points. Excludes first and last point (takeoff/landing).
	NDefines.NAirGfx.AIRPLANES_SCALE_TAKEOFF_DIST = 0.1 				-- Until first x% of the flight path, the airplane will scale up.
	NDefines.NAirGfx.AIRPLANES_SCALE_MIN = 0.1 						-- Minimum airplane scale down when takeoff/landing.
	NDefines.NAirGfx.AIRPLANES_SCALE_LANDING_DIST = 0.9 				-- After last x% of the flight path, the airplane will scale down.
	NDefines.NAirGfx.AIRPLANES_SMOOTH_INTERPOLATION_MOVE = 0.13	 	-- How smooth is the movement interpolation.
	NDefines.NAirGfx.AIRPLANES_SMOOTH_INTERPOLATION_TURN = 0.095 	-- How smooth is the turning interpolation.
	NDefines.NAirGfx.AIRPLANES_BANK_STRENGTH = 210.0 				-- Multiplier of how much the curve affects the wings banking. (angle limited by the following value)
	NDefines.NAirGfx.AIRPLANES_BANK_ANGLE_LIMIT = 55.0 				-- Bank angle limit.
	NDefines.NAirGfx.AIRPLANES_GROUND_COLLISION_OFFSET_Y = -5.0 		-- Lets the 3d airplanes disappear after going a bit under the ground.
	NDefines.NAirGfx.AIRPLANES_1_FIGHTER_PATROL_ANIM = 1			-- Number of fighters needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_3_FIGHTER_PATROL_ANIM = 3			-- Number of fighters needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_1_BOMBER_BOMBING_ANIM = 1 			-- Number of bombers needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_3_BOMBER_BOMBING_ANIM = 3				-- Number of bombers needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_1_FIGHTER_VS_1_FIGHTER_ANIM = 1 		-- Number of fighters needed per side for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_3_FIGHTER_VS_3_FIGHTER_ANIM = 3		-- Number of bombers needed per side for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_1_TRANSPORT_SUPPLY_ANIM = 1			-- Number of planes needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_3_TRANSPORT_SUPPLY_ANIM = 3			-- Number of planes needed for a single instance of this animation
	NDefines.NAirGfx.AIRPLANES_1_SCOUT_PLANE_PATROL_ANIM = 1
	NDefines.NAirGfx.AIRPLANES_3_SCOUT_PLANE_PATROL_ANIM = 3

	NDefines.NAirGfx.BOMBERS_DIVISION_FACTOR = 60					-- Number of effective bombers in a strategic region will be divided by this factor.
	NDefines.NAirGfx.MISSILES_DIVISION_FACTOR = 60					-- Number of missiles shown in a strategic region will be divided by this factor.
	NDefines.NAirGfx.FIGHTERS_DIVISION_FACTOR = 60					-- Number of missiles shown in a strategic region will be divided by this factor.
	NDefines.NAirGfx.SCOUT_PLANE_DIVISION_FACTOR = 60				-- Number of missiles shown in a strategic region will be divided by this factor.
	NDefines.NAirGfx.TRANSPORT_DIVISION_FACTOR = 60
	NDefines.NAirGfx.MAX_MISSILE_BOMBING_SCENARIOS = 6				-- Max number of missile bombing scenarios in a strategic region.
	NDefines.NAirGfx.MAX_PATROL_SCENARIOS = 4					-- Max number of patrol scenarios in a strategic region.
	NDefines.NAirGfx.MAX_BOMBING_SCENARIOS = 4						-- Max number of bombings scenarios in a strategic region.
	NDefines.NAirGfx.MAX_DOGFIGHTS_SCENARIOS = 4					-- Max number of dogfight scenarios in a strategic region.
	NDefines.NAirGfx.MAX_TRANSPORT_SCENARIOS = 4					-- Max number of transport scenarios in a strategic region
	NDefines.NAirGfx.MAX_TRAINING_SCENARIOS = 4						-- Max number of training scenarios in a strategic region
	NDefines.NAirGfx.MAX_SCOUT_SCENARIOS = 1

	NDefines.NGraphics.PROVINCE_NAME_DRAW_DISTANCE = 800.0
	NDefines.NGraphics.DRAW_SHADOWS_CUTOFF = 400
	NDefines.NGraphics.DRAW_SHADOWS_FADE_LENGTH = 50
	NDefines.NGraphics.DRAW_FOW_CUTOFF = 310
	NDefines.NGraphics.DRAW_FOW_FADE_LENGTH = 220
	
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_COUNTRY_CENTER_THICKNESS = 0
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_THICKNESS_DIPLOMACY = 5
	NDefines_Graphics.NGraphics.BORDER_WIDTH = 1.0
	NDefines_Graphics.GRADIENT_BORDERS_THICKNESS_STATE = 5.0
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_FIELD_COUNTRY_LOW = 300.0 -- country area in sum of pixels ...
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_FIELD_COUNTRY_HIGH = 9000.0 -- ... the value is squared, so fe. country of size 100x100pix = 10000
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_THICKNESS_COUNTRY_LOW = 6 -- thickness in pixels
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_THICKNESS_COUNTRY_HIGH = 17 -- Border thickness
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_THICKNESS_STATE = 30
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_OUTLINE_CUTOFF_COUNTRY = 0.98
	NDefines_Graphics.NGraphics.GRADIENT_BORDERS_OUTLINE_CUTOFF_DIPLOMACY = 0.98

	NDefines.NGraphics.GRADIENT_BORDERS_THICKNESS_SUPPLY_AREA_B = 15.0 --20
	NDefines.NGraphics.GRADIENT_BORDERS_THICKNESS_STRATEGIC_REGIONS = 45.0 --150
	NDefines.NGraphics.GRADIENT_BORDERS_OUTLINE_CUTOFF_STRATEGIC_REGIONS = 0.999
	NDefines.NGraphics.STRATEGIC_AIR_COLOR_NEUTRAL = {165.0/255, 165.0/255, 165.0/255, 1} -- {140.0/255, 131.0/255, 119.0/255, 1}
	NDefines.NGraphics.STRATEGIC_NAVY_COLOR_NEUTRAL = {41.0/255, 45.0/255, 64.0/255, 1} -- {0.3, 0.3, 0.3, 0}
 	NDefines.NGraphics.COUNTRY_FLAG_TEX_MAX_SIZE = 1024							-- Vanilla is 256, Tweak dependly on amount of countries. Must be power of 2. No more then 2048.
	NDefines.NGraphics.COUNTRY_FLAG_MEDIUM_TEX_MAX_SIZE = 1024							-- Vanilla is 256, Tweak dependly on amount of countries. Must be power of 2. No more then 2048.
	-- NDefines.NGraphics.COUNTRY_FLAG_SMALL_TEX_MAX_SIZE = 1024					-- Vanilla is 64, Tweak dependly on amount of countries. Must be power of 2. No more then 2048.
	-- -- NDefines.NGraphics.COUNTRY_FLAG_STRIPE_TEX_MAX_WIDTH = 10					-- Vanilla is 10
	-- -- NDefines.NGraphics.COUNTRY_FLAG_STRIPE_TEX_MAX_HEIGHT = 4096				-- Vanilla is 2048
	-- -- NDefines.NGraphics.COUNTRY_FLAG_LARGE_STRIPE_MAX_WIDTH = 41					-- Vanilla is 41
	-- -- NDefines.NGraphics.COUNTRY_FLAG_LARGE_STRIPE_MAX_HEIGHT = 8192				-- Vanilla is 8192
	NDefines.NGraphics.VICTORY_POINT_MAP_ICON_AFTER = {0, 4, 9} -- 1-4 - small icon (square), 5-9 - medium icon (pentagon figure), 10 and above - big icon (circle)
	NDefines.NGraphics.VICTORY_POINT_MAP_ICON_TEXT_CUTOFF = {180, 420, 1000}
	NDefines.NGraphics.VICTORY_POINTS_DISTANCE_CUTOFF = {180, 420, 1000}
	NDefines.NGraphics.NAVALBASE_ICON_DISTANCE_CUTOFF = 900
	NDefines.NGraphics.CAPITAL_ICON_CUTOFF = 1000
	NDefines.NGraphics.MAP_ICONS_GROUP_CAM_DISTANCE = 120.0
	NDefines.NGraphics.MAP_ICONS_STATE_GROUP_CAM_DISTANCE = 330.0
	NDefines.NGraphics.MAP_ICONS_STRATEGIC_GROUP_CAM_DISTANCE = 600
	NDefines.NGraphics.MAPICON_GROUP_STRATEGIC_SIZE = 600
	NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE = 200
	NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE_STRATEGIC = 800
	NDefines.NGraphics.CAMERA_OUTSIDE_MAP_DISTANCE_TOP = 100.0
	NDefines.NGraphics.CAMERA_OUTSIDE_MAP_DISTANCE_BOTTOM = 100.0
	NDefines.NGraphics.CAMERA_ZOOM_SPEED = 12
	NDefines.NGraphics.CAMERA_ZOOM_KEY_SCALE = 0.01
	NDefines.NGraphics.CAMERA_ZOOM_SPEED_DISTANCE_MULT = 50.0

	NDefines.NFrontend.CAMERA_LOOKAT_SETTINGS_X = 2058.0
	NDefines.NFrontend.CAMERA_MIN_HEIGHT = 30.0
	
	NDefines.NGraphics.ACCLIMATIZATION_CAMO_SHOW_AT = 0.05				-- The moment at which the division gains enough acclimatization to change it's model to the camouflage one.
