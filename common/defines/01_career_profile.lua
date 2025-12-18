NDefines_CareerProfile = {

NCareerProfile = {
	-- Mod defines
	MOD_STATISTICS_GROUP = "Millennium Dawn", -- Can be set by mods to collect statistics in a separate data set for the mod. Will also be used as the display name if MOD_STATISTICS_GROUP_NAME is not set.
	MOD_STATISTICS_GROUP_NAME = "MILLENIUM_DAWN_CUSTOM_ACHIEVEMENTS", -- Can be set by mods as a display name for the mod's statistics data set. It can be a localized.

	-- Statistics parameters
	NAVAL_INVASION_MEDAL_MAX_DURATION = 96, -- Maximum duration in hours to finish naval invasion and get a Naval Invasion Medal
	PARADROP_AWARD_DIVISION_MIN_BATTALION_COUNT = 5, -- Minimum count of battalions in the division required to count that division for paradrop awards ("Paradrop Medal" and "They came from Above")
	NAVAL_INVASION_MEDAL_DIVISION_MIN_BATTALION_COUNT = 5, -- Minimum count of battalions in the division required to count that division for Naval Invasion Medal
	TURNING_TIDE_MEDAL_DIVISION_MIN_BATTALION_COUNT = 5, -- Minimum count of battalions in the division required to count that division for Turning the Tide Medal
	STEEL_AT_HIGH_SPEED_RIBBON_TANK_SPEED = 12, -- Minimum speed to count deployed tanks for Steel at High Speed Ribbon
	ORCHESTRA_OF_BOOM_RIBBON_SPECIAL_BATTALION_COUNT = 4, -- Amount of special battalion types(anti-air, anti-tank, artillery and rocket artillery) required for the division for Orchestra of Boom Ribbon
	NEVERMINE_ME_MEDAL_MIN_RATIO = 0.5, -- Minimum effect mines should have on the supremacy to count current naval region for Nevermine Me Medal
	BLITZ_THIS_TACTIC_NAME = "tactic_elastic_defense", -- The tactic required to be applied to a leader or a country for Blitz This Ribbon
	ENGINEERING_BEHEMOTH_MEDAL_ARMOR_RATING_BRONZE = 100, -- The armor rating required for the tanks to get the Engineering The Behemoth Bronze Medal
	ENGINEERING_BEHEMOTH_MEDAL_ARMOR_RATING_SILVER = 160, -- The armor rating required for the tanks to get the Engineering The Behemoth Silver Medal
	ENGINEERING_BEHEMOTH_MEDAL_ARMOR_RATING_GOLD = 200, -- The armor rating required for the tanks to get the Engineering The Behemoth Gold Medal
	CASTLES_IN_THE_AIR_MEDAL_AIR_DEFENSE_BRONZE = 20, -- The air defense required for the airplanes to get the Castles in the Air Bronze Medal
	CASTLES_IN_THE_AIR_MEDAL_AIR_DEFENSE_SILVER = 50, -- The air defense required for the airplanes to get the Castles in the Air Silver Medal
	CASTLES_IN_THE_AIR_MEDAL_AIR_DEFENSE_GOLD = 100, -- The air defense required for the airplanes to get the Castles in the Air Gold Medal
},

NCareerProfileGUI = {
	AWARD_POPUP_DURATION = 8000, -- Show an award popup for this many milliseconds
	AWARD_POPUP_CONTENT_DELAY = 400, -- Show the content of the award popup after this many milliseconds

	CAREER_POINTS_ANIMATION_DELAY = 950, -- Delay the career points count-up animation by this many milliseconds
	CAREER_POINTS_ANIMATION_DURATION = 950, -- Count the career points up for this many milliseconds
	PROFILE_PICTURE_BACKGROUND_OPACITY = 0.8, -- The opacity of the dark background square behind profile pictures
},

}

for k,v in pairs( NDefines_CareerProfile ) do NDefines[k] = v end
