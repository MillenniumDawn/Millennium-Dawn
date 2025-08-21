	-- NGame ssection
	NDefines.NGame.START_DATE = "2000.1.1.12"
	NDefines.NGame.END_DATE = "2100.1.1.1"
	NDefines.NGame.LAG_DAYS_FOR_LOWER_SPEED = 500
	NDefines.NGame.LAG_DAYS_FOR_PAUSE = 100
	NDefines.NGame.MAX_SCRIPTED_LOC_RECURSION = 40

	-- NDiplomacy Defines
	NDefines.NDiplomacy.MAX_OPINION_VALUE = 300
	NDefines.NDiplomacy.MIN_OPINION_VALUE = -300
	NDefines.NDiplomacy.BASE_NEGATIVE_OPINION_AFTER_BEING_KICKED = 50
	NDefines.NDiplomacy.DECAY_RATE_OF_NEGATIVE_OPINION_AFTER_BEING_KICKED = 0.5
	NDefines.NDiplomacy.TRUCE_BREAK_COST_PP = 100
	NDefines.NDiplomacy.BASE_PEACE_LIBERATE_FACTOR = 110
	NDefines.NDiplomacy.BASE_PEACE_TAKE_UNCONTROLLED_STATE_FACTOR = 2
	NDefines.NDiplomacy.BASE_PEACE_FORCE_GOVERNMENT_COST = 20
	NDefines.NDiplomacy.BASE_IMPROVE_RELATION_SAME_IDEOLOGY_GROUP_MAINTAIN_COST = 0.25
	NDefines.NDiplomacy.BASE_IMPROVE_RELATION_DIFFERENT_IDEOLOGY_GROUP_MAINTAIN_COST = 0.5
	NDefines.NDiplomacy.BASE_SEND_ATTACHE_COST = 80
	NDefines.NDiplomacy.BASE_SEND_ATTACHE_CP_COST = 40.0
	NDefines.NDiplomacy.BASE_BOOST_PARTY_POPULARITY_DAILY_PP = 1
	NDefines.NDiplomacy.BASE_BOOST_PARTY_POPULARITY_DAILY_DRIFT = 0.1
	NDefines.NDiplomacy.BASE_STAGE_COUP_DAILY_PP = 2.5
	NDefines.NDiplomacy.BASE_STAGE_COUP_TOTAL_COST = 2000
	NDefines.NDiplomacy.TRADE_OPINION_FACTOR_FACTOR = 0.5
	NDefines.NDiplomacy.DIPLOMACY_HOURS_BETWEEN_REQUESTS = 72 -- 24 exp
	NDefines.NDiplomacy.IC_TO_EQUIPMENT_COUP_RATIO = 0.3
	NDefines.NDiplomacy.VOLUNTEERS_RETURN_EQUIPMENT = 1
	NDefines.NDiplomacy.VOLUNTEERS_TRANSFER_SPEED = 7
	NDefines.NDiplomacy.VOLUNTEERS_DIVISIONS_REQUIRED = 7
	NDefines.NDiplomacy.TENSION_STATE_VALUE = 3.25
	NDefines.NDiplomacy.TENSION_CIVIL_WAR_IMPACT = 0.4
	NDefines.NDiplomacy.TENSION_NO_CB_WAR = 10
	NDefines.NDiplomacy.TENSION_CB_WAR = 3.75
	NDefines.NDiplomacy.TENSION_PUPPET = 1.5 -- Reduced from 2.0
	NDefines.NDiplomacy.TENSION_ANNEX_NO_CLAIM = 3
	NDefines.NDiplomacy.TENSION_ANNEX_CLAIM = 2
	NDefines.NDiplomacy.TENSION_VOLUNTEER_FORCE_DIVISION = 0.25  -- Reduced from 0.50
	NDefines.NDiplomacy.TENSION_DECAY_DAILY = 0.025						-- Each months tension decays this much
	NDefines.NDiplomacy.TENSION_TIME_SCALE_START_DATE = "2000.1.1.12" 	-- Starting at this date, the tension values will be scaled down (will be equal to 1 before that)
	NDefines.NDiplomacy.TENSION_TIME_SCALE_MONTHLY_FACTOR = 0		-- Timed tension scale will be modified by this amount starting with TENSION_TIME_SCALE_START_DATE
	NDefines.NDiplomacy.TENSION_TIME_SCALE_MIN = 0 					-- Timed tension scale won't decrease under this value
	NDefines.NDiplomacy.TENSION_GUARANTEE = -10
	NDefines.NDiplomacy.TENSION_PEACE_FACTOR = 0.25					-- scale of the amount of tension (from war declaration) reduced when peace is completed.
	NDefines.NDiplomacy.TENSION_CAPITULATE = 0
	NDefines.NDiplomacy.TENSION_WAR_REPARATION = 0
	NDefines.NDiplomacy.TENSION_FACTION_JOIN = 2
	NDefines.NDiplomacy.TENSION_JOIN_ATTACKER = 1
	NDefines.NDiplomacy.GUARANTEE_COST = 50
	NDefines.NDiplomacy.REVOKE_GUARANTEE_COST = 30
	NDefines.NDiplomacy.OPINION_PER_VOLUNTEER = 15
	NDefines.NDiplomacy.MAX_OPINION_FROM_VOLUNTEERS = 50
	NDefines.NDiplomacy.LICENSE_ACCEPTANCE_TECH_DIFFERENCE = 3
	NDefines.NDiplomacy.LICENSE_ACCEPTANCE_TECH_DIFFERENCE_BASE = 20
	NDefines.NDiplomacy.MASTER_BUILD_AUTONOMY_FACTOR = -0.5  -- was -0.7

	NDefines.NDiplomacy.LL_TO_OVERLORD_AUTONOMY_DAILY_BASE = 0  -- If puppet lend leases equipment to overlord of at least same tech level as they have, they gain autonomy
	NDefines.NDiplomacy.LL_TO_OVERLORD_AUTONOMY_DAILY_FACTOR = 0.05  -- If puppet lend leases equipment to overlord of at least same tech level as they have, they gain autonomy
	NDefines.NDiplomacy.LL_TO_PUPPET_AUTONOMY_DAILY_BASE = 0  -- If overlord lend leases equipment to puppet of higher tech level as they have, puppet losses autonomy
	NDefines.NDiplomacy.LL_TO_PUPPET_AUTONOMY_DAILY_FACTOR = -0.001  -- If overlord lend leases equipment to puppet of higher tech level as they have, puppet losses autonomy

	NDefines.NDiplomacy.EMBARGO_THREAT_THRESHOLD = 20
	NDefines.NDiplomacy.EMBARGO_DIFFERENT_IDEOLOGY_AI_WEIGHT = -5
	NDefines.NDiplomacy.EMBARGO_DIFFERENT_IDEOLOGY_AT_OFFENSIVE_WAR_AI_WEIGHT = 15
	NDefines.NDiplomacy.EMBARGO_NEIGHBOUR_AI_WEIGHT = -15
	NDefines.NDiplomacy.EMBARGO_RECIPIENT_IS_MAJOR_AI_WEIGHT = 5
	NDefines.NDiplomacy.EMBARGO_COST = 50									-- One-time cost

	-- Faction related stuff
	NDefines.NDiplomacy.TRUCE_PERIOD_AFTER_KICKING_FROM_FACTION = 30				-- Truce period after kicking someone from faction in days.
	NDefines.NDiplomacy.NUM_DAYS_TO_ENABLE_KICKING_NEW_MEMBERS_OF_FACTION = 90			-- Number of days before being able to kick a new member of faction
	NDefines.NDiplomacy.NUM_DAYS_TO_ENABLE_REINVITE_KICKED_NATIONS = 90			-- Number of days before being able to re invite a kicked nation to your faction
	NDefines.NDiplomacy.IDEOLOGY_JOIN_FACTION_MIN_LEVEL = 0.2  --0.3 in Vanilla 	-- ideology limit required to join faction
	NDefines.NDiplomacy.JOIN_FACTION_LIMIT_CHANGE_AT_WAR = 1 --0.5 in Vanilla, value of 1 should mean defensive war gives no reduction to tension limit	-- if in defensive war this or your modifier is counted as limit to join factions (so if you have 80% join limit this now means you can join at 50%)
	NDefines.NDiplomacy.ASSUME_FACTION_LEADERSHIP_PP_COST = 200				-- Political power cost to assume faction leadership
	NDefines.NDiplomacy.ASSUME_FACTION_LEADERSHIP_MIN_MANPOWER_RATIO = 2		-- The minimum ratio of manpower that a country must have compared to the current leader in order to assume leadership.
	NDefines.NDiplomacy.ASSUME_FACTION_LEADERSHIP_MIN_FACTORY_RATIO = 1.5		-- The minimum ratio of factories that a country must have compared to the current leader in order to assume leadership.
	NDefines.NDiplomacy.ASSUME_FACTION_LEADERSHIP_COOLDOWN_DAYS = 180			-- Number of days after formation of faction or change in leadership before another country is allowed to assume leadership.
	NDefines.NDiplomacy.ASSUME_FACTION_SPYMASTER_COOLDOWN_DAYS = 180			-- Number of days after change of Spy Master before another country is allowed to become Spy Master.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_ALERT_THRESHOLD = 0.8		-- Threshold for showing an alert when a faction member is close to being able to assume leadership of the faction that a player currently leads.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_NOT_SUBJECT_WEIGHT = 2		-- Importance of subject status when determining how close a faction member is to being able to assume leadership.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_NOT_CAPITULATED_WEIGHT = 2	-- Importance of capitulation status when determining how close a faction member is to being able to assume leadership.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_IN_ALL_WARS_WEIGHT = 1		-- Importance not being in all faction leader wars when determining how close a faction member is to being able to assume leadership.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_COOLDOWN_WEIGHT = 1			-- Importance of leadership change cooldown when determining how close a faction member is to being able to assume leadership.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_MANPOWER_WEIGHT = 2			-- Importance of manpower in field when determining how close a faction member is to being able to assume leadership.
	NDefines.NDiplomacy.FACTION_LEADERSHIP_CHANGE_FACTORY_WEIGHT = 2			-- Importance of factory count when determining how close a faction member is to being able to assume leadership.

	-- Peace related defines
	NDefines.NDiplomacy.BASE_PEACE_PUPPET_FACTOR = 100							-- (100 in vanilla) Base factor for puppet in %.
	NDefines.NDiplomacy.BASE_PEACE_LIBERATE_FACTOR = 100						-- (100 in vanilla) Base factor for liberate in %.
	NDefines.NDiplomacy.BASE_PEACE_TAKE_UNCONTROLLED_STATE_FACTOR = 10.0		-- (10.0 in vanilla) Base factor for taking state you do not control
	NDefines.NDiplomacy.BASE_PEACE_TAKE_FACTION_CONTROLLED_STATE_FACTOR = 0.5	-- (0.5 in vanilla) Base factor for taking state you do not control, but someone in faction does
	NDefines.NDiplomacy.BASE_PEACE_FORCE_GOVERNMENT_COST = 100 				-- (100 in vanilla) Base cost for forcing a country to change government.
	-- In peace conference, cost is factored based on how many times the state has been contested and for how long it has been uncontested (for everyone else)
	NDefines.NDiplomacy.PEACE_COST_FACTOR_CONTESTED_MAX = 10										-- (15 in vanilla) To prevent overflows due to the exponential increase, cap the contested factor to this
	NDefines.NDiplomacy.PEACE_COST_FACTOR_UNCONTESTED_MAX = 10										-- (15 in vanilla) To prevent overflows due to the exponential increase, cap the uncontested factor to this
	NDefines.NDiplomacy.PEACE_COST_FACTOR_CONTESTED_BID = 1.20										-- (1.20 in vanilla) Cost factor for each contested bid on the state.
	NDefines.NDiplomacy.PEACE_COST_FACTOR_UNCONTESTED_BID_MIN = 1.15								-- (1.15 in vanilla) Minimum cost factor for each turn a bid has been uncontested on the state.
	NDefines.NDiplomacy.PEACE_COST_FACTOR_UNCONTESTED_BID_MAX = 1.60								-- (1.60 in vanilla) Maximum cost factor for each turn a bid has been uncontested on the state.
	NDefines.NDiplomacy.PEACE_COST_FACTOR_UNCONTESTED_BID_STEP = 0.15								-- (0.15 in vanilla) Uncontested cost factor will increase by this much each turn.
	NDefines.NDiplomacy.PEACE_COST_FACTOR_CAPITAL_SHIP_IC = 0.002									-- (0.005 in vanilla) In peace conference, cost for taking one capital ship per IC
	NDefines.NDiplomacy.PEACE_COST_FACTOR_SCREENING_SHIP_IC = 0.001								-- (0.005 in vanilla) In peace conference, cost for taking a part of the screening ships per IC
	NDefines.NDiplomacy.PEACE_INCREASE_COST_FACTOR_PER_MISSING_PERCENT_FOR_CAPITULATION = 0.002	-- (0.002 in vanilla) increase factor if loser has not capitulated, for every percent between surrender level and BASE_SURRENDER_LEVEL
	-- peace action taker has a discount if they occupy the state depending on compliance
	-- it's a table where first value is the compliance level, and the second the factor
	NDefines.NDiplomacy.PEACE_COST_FACTOR_COMPLIANCE_STEPS = {
		0,   1.0, -- between 0%  and 30% compliance, factor is 1.0
		30,  0.9, -- between 30% and 70%
		70,  0.8, -- above 70%
	}
	-- In peace conference, adding a stackable to a peace action, increment the cost by a percentage
	NDefines.NDiplomacy.PEACE_COST_FACTOR_STACK_DEMILITARIZED_ZONE = 0.1 -- vanilla is 0.25
	NDefines.NDiplomacy.PEACE_COST_FACTOR_STACK_WAR_REPARATION = 0.1 -- vanilla is 0.25
	NDefines.NDiplomacy.PEACE_COST_FACTOR_STACK_RESOURCE_RIGHTS = 0.3 -- vanilla is 0.25
	NDefines.NDiplomacy.PEACE_COST_FACTOR_STACK_DISMANTLE_INDUSTRY = 0.4 -- vanilla is 0.25
	-- peace conference can set timed effect, set length in days
	NDefines.NDiplomacy.PEACE_TIMED_EFFECT_LENGTH_DEMILITARIZED_ZONE = 1095 -- vanilla is 1825 days (5 years)
	NDefines.NDiplomacy.PEACE_TIMED_EFFECT_LENGTH_WAR_REPARATION = 1095
	NDefines.NDiplomacy.PEACE_TIMED_EFFECT_LENGTH_RESOURCE_RIGHTS = 1095
	NDefines.NDiplomacy.PEACE_TIMED_EFFECT_RATIO_CIVILIAN_FACTORY_WAR_REPARATION = 0.5 	-- ratio of civilian factories taken via stackable war reparation

	-- The Influence cost modifier is basically the inverse of distance. Nearby states are cheaper, and far-away states are more expensive.
	-- We basically do a two-segment lerp:
	-- if distance is between [0, NEUTRAL_DIST], we lerp the cost modifier between [MIN_DIST_COST_MODIFIER, 1.0]
	-- if distance is between [NEUTRAL_DIST, MAX_DIST], we lerp the cost modifier between [1.0, MAX_DIST_COST_MODIFIER]
	-- The below values represent (pixel distance / INFLUENCE_DISTANCE_DIVISOR)
	NDefines.NDiplomacy.INFLUENCE_NEUTRAL_DIST_CAPITAL = 80.0			-- distance to capital that results in a cost modifier of 1.0
	NDefines.NDiplomacy.INFLUENCE_MAX_DIST_CAPITAL = 100.0				-- distance to capital that results in a cost modifier of INFLUENCE_MAX_DIST_COST_MODIFIER
	NDefines.NDiplomacy.INFLUENCE_NEUTRAL_DIST_CORE = 20.0				-- distance to nearest core state that results in a cost modifier of 1.0
	NDefines.NDiplomacy.INFLUENCE_MAX_DIST_CORE = 30.0					-- distance to nearest core state that results in a cost modifier of INFLUENCE_MAX_DIST_COST_MODIFIER
	NDefines.NDiplomacy.INFLUENCE_NEUTRAL_DIST_CONTROLLED = 10.0		-- distance to nearest controlled state that results in a cost modifier of 1.0
	NDefines.NDiplomacy.INFLUENCE_MAX_DIST_CONTROLLED = 14.0			-- distance to nearest controlled state that results in a cost modifier of INFLUENCE_MAX_DIST_COST_MODIFIER
	NDefines.NDiplomacy.INFLUENCE_MIN_DIST_COST_MODIFIER = 0.80		-- Cost modifier at min (zero) distance
	NDefines.NDiplomacy.INFLUENCE_MAX_DIST_COST_MODIFIER = 1.20		-- Cost modifier at max distance
	NDefines.NDiplomacy.INFLUENCE_RATIO_CAPITAL = 0.2					-- Ratio of influence based on distance to capital
	NDefines.NDiplomacy.INFLUENCE_RATIO_CORE = 0.3						-- Ratio of influence based on distance to nearest core territory
	NDefines.NDiplomacy.INFLUENCE_RATIO_CONTROLLED = 0.5				-- Ratio of influence based on distance to neared controlled territory (including uncontested peace conference bids)
	NDefines.NDiplomacy.INFLUENCE_DISTANCE_DIVISOR = 30.0				-- Divide pixel distance with this when determining distance to capital / core / controlled states. Just an arbitrary way of scaling the distance numbers.

	NDefines.NDiplomacy.INFLUENCE_MAJOR_FACTOR = 1.0					--How much influence discount a major will get
	NDefines.NDiplomacy.INFLUENCE_MINOR_FACTOR = 0.65					--How much influence discount a minor will get

	NDefines.NDiplomacy.PEACE_TRIGGER_AI_MAX_INFLUENCE_VALUE = 0.89	-- Max influence value for pc_is_state_outside_influence_for trigger

	-- NMarket Related Defines
	NDefines.NProduction.CIC_BANK_SPEED_BOOST_FACTOR = 0 -- 0.25
	NDefines.NMarket.IC_TO_CIC_FACTOR = 0.5 -- 2.0
	NDefines.NMarket.PURCHASE_CONTRACT_DELIVERY_TOTAL_DAYS = 45 -- 30
	NDefines.NMarket.MAX_CIV_FACTORIES_PER_CONTRACT = 1 -- 15
	NDefines.NMarket.LOW_PRICE_LEVEL_FACTOR = 0.90 -- 0.75
	NDefines.NMarket.HIGH_PRICE_LEVEL_FACTOR = 1.10 -- 1.25
	-- Raid AI
	NDefines.NAI.RAIDS_MIN_SUCCESS_FOR_LAUNCH = 0.12 -- 0.65 -- Scaled by 0.10 more for some reason
	NDefines.NAI.RAIDS_CREATE_FREQUENCEY_DAYS = 30 -- 7 -- Changed this to monthly to reduce the performance hit, given the number of raids present
	NDefines.NAI.RAIDS_COMMAND_POWER_CAP_TO_CREATE = 60 -- 60
	NDefines.NAI.RAIDS_CANCEL_AFTER_DAYS_LAUNCHABLE = 90 -- 60 -- Increased to give the AI more time to try and make a raid happen
	NDefines.NAI.RAIDS_AVOID_SAME_TARGET_DURATION_DAYS = 180 -- 180
	NDefines.NAI.RAIDS_AVOID_SAME_TARGET_FACTOR = 0.4 -- 0.4
	NDefines.NAI.RAIDS_NUKE_TARGET_CUT_OFF = 10 -- 10
	NDefines.NAI.RAIDS_UNIT_SCORE_SUCCESS_CHANCE_FACTOR = 500.0 -- 500.0
	NDefines.NAI.RAIDS_UNIT_SCORE_DISTANCE_KM_FACTOR = 0.1 -- 0.1
	-- Market AI
	NDefines.NAI.MAX_CIVS_FOR_PURCHASES_RATIO = 0.05 -- 0.1
	NDefines.NAI.EQUIPMENT_MARKET_BASE_MARKET_RATIO = 0.1 -- 0.2
	NDefines.NAI.EQUIPMENT_MARKET_NR_DELIVERIES_SOFT_MAX = 400 -- 10 -- this should get AI to never add more than one factory
	-- NCountry Releated Defines
	NDefines.NCountry.AIR_SUPPLY_CONVERSION_SCALE = 0.1 -- 0.01
	NDefines.NCountry.AIR_SUPPLY_DROP_EXPIRATION_HOURS = 168 -- 168
	NDefines.NCountry.FUEL_LEASE_CONVOY_RATIO = 0.00005 -- 0.0005
	NDefines.NCountry.BASE_RESEARCH_SLOTS = 2 -- Maintains Vanilla's 2 RS default. RSs are handled via the dynamic system
	NDefines.NCountry.POPULATION_YEARLY_GROWTH_BASE = 0.008 --0.015 in vanilla, reduced from the 0.01 in MD to accomdate for the migration system
	NDefines.NCountry.RESISTANCE_STRENGTH_FROM_VP = 0.001
	NDefines.NCountry.RESISTANCE_STRENGTH_FROM_UNIT = 0.002
	NDefines.NCountry.RESOURCE_LENDLEASE_PRIORITY = 2
	NDefines.NCountry.SUPPLY_CONVOY_FACTOR = 0.5
	NDefines.NCountry.CONVOY_RANGE_FACTOR = 1.5
	NDefines.NCountry.LOCAL_MANPOWER_ACCESSIBLE_FACTOR = 0.01
	NDefines.NCountry.LOCAL_MANPOWER_ACCESSIBLE_NON_CORE_FACTOR = 0.01
	NDefines.NCountry.DEFAULT_STABILITY = 0.65 		-- Default stability if not scripted otherwise.
	NDefines.NCountry.DEFAULT_WAR_SUPPORT = 0.5 		-- Default war support if not scripted otherwise.
	NDefines.NCountry.BASE_STABILITY_WAR_FACTOR = -0.15
	NDefines.NCountry.WAR_SUPPORT_OFFNSIVE_WAR = -0.1
	NDefines.NCountry.WAR_SUPPORT_DEFENSIVE_WAR = 0.2 -- 1
	NDefines.NCountry.MAJOR_IC_RATIO = 3                            -- difference in total factories needed to be considered major with respect to other nation
	NDefines.NCountry.MAJOR_MIN_FACTORIES = 35						-- need at least these many factories to become a major
	NDefines.NCountry.MIN_MAJOR_COUNTRIES	= 8						-- MIN_MAJOR_COUNTRIES countries with most factories will be considered as major countries
	NDefines.NCountry.ADDITIONAL_MAJOR_COUNTRIES_IC_RATIO = 0.7		-- Countries will also be considered major when having more factories that the average of top MIN_MAJOR_COUNTRIES countries' factories times ADDITIONAL_MAJOR_COUNTRIES_IC_RATIO
	NDefines.NCountry.MAX_INTELLIGENCE_MILITARY_DATA_DEVIATION = 0.5
	NDefines.NCountry.MAX_INTELLIGENCE_AIR_DATA_DEVIATION = 0.3
	NDefines.NCountry.MAX_INTELLIGENCE_INDUSTRY_DATA_DEVIATION = 0.2
	NDefines.NCountry.MAX_INTELLIGENCE_MANPOWER_DATA_DEVIATION = 0.3
	NDefines.NCountry.STATE_VALUE_BUILDING_SLOTS_MULT = 3.0 -- value of each building slot in a state
	NDefines.NCountry.SPECIAL_FORCES_CAP_BASE = 0.075
	NDefines.NCountry.SPECIAL_FORCES_CAP_MIN = 6
	NDefines.NCountry.DAYS_OF_WAR_BEFORE_SURRENDER = 7
	NDefines.NCountry.BASE_MOBILIZATION_SPEED = 0.01 --0.01
	NDefines.NCountry.SCORCHED_EARTH_STATE_COST = 25                        -- pp cost to scorch a state -- 5 in vanilla
	NDefines.NCountry.BASE_MAX_COMMAND_POWER = 250.0                       -- base value for maximum command power -- 200 in vanilla
	NDefines.NCountry.AIR_VOLUNTEER_PLANES_RATIO = 0.25				-- Ratio for volunteer planes available for sending in relation to sender air force
	NDefines.NCountry.AIR_VOLUNTEER_BASES_CAPACITY_LIMIT = 0.2		-- Ratio for volunteer planes available for sending in relation to receiver air base capacity
	NDefines.NCountry.STARTING_FUEL_RATIO = 1					-- starting fuel ratio compared to max fuel for countries
	NDefines.NCountry.BASE_FUEL_GAIN_PER_OIL = 16						-- base amount of fuel gained hourly per excess oil
	NDefines.NCountry.BASE_FUEL_GAIN = 0.1							-- base amount of fuel gained hourly, independent of excess oil
	NDefines.NCountry.BASE_FUEL_CAPACITY = 750000

	NDefines.NProduction.MAX_EQUIPMENT_RESOURCES_NEED = 4
	NDefines.NProduction.MAX_LINE_RESOURCE_PENALTY = 50
	NDefines.NProduction.BASE_FACTORY_SPEED_MIL = 3
	NDefines.NProduction.BASE_FACTORY_SPEED_NAV = 8
	NDefines.NProduction.BASE_FACTORY_START_EFFICIENCY_FACTOR = 5
	NDefines.NProduction.BASE_CONSUMER_GOODS_NEED_FACTOR = 0
	NDefines.NProduction.EQUIPMENT_BASE_LEND_LEASE_WEIGHT = 1
	NDefines.NProduction.EQUIPMENT_LEND_LEASE_WEIGHT_FACTOR = 0.01
	NDefines.NProduction.ANNEX_STOCKPILES_RATIO = 0.4
	NDefines.NProduction.ANNEX_FIELD_EQUIPMENT_RATIO = 0.1
	NDefines.NProduction.INFRA_MAX_CONSTRUCTION_COST_EFFECT = 0.75
	NDefines.NProduction.LICENSE_IC_COST_YEAR_INCREASE = 0
	NDefines.NProduction.LICENSE_EQUIPMENT_BASE_SPEED = -0.2 -- -0.2 exp
	NDefines.NProduction.LICENSE_EQUIPMENT_TECH_SPEED_PER_YEAR = -0.01
	NDefines.NProduction.LICENSE_EQUIPMENT_TECH_SPEED_MAX_YEARS = 40
	NDefines.NProduction.EQUIPMENT_MODULE_ADD_XP_COST = 5.0					-- XP cost for adding a new equipment module in an empty slot when creating an equipment variant.
	NDefines.NProduction.EQUIPMENT_MODULE_REPLACE_XP_COST = 6.0				-- XP cost for replacing one equipment module with an unrelated module when creating an equipment variant.
	NDefines.NProduction.EQUIPMENT_MODULE_CONVERT_XP_COST = 3.0				-- XP cost for converting one equipment module to a related module when creating an equipment variant.
	NDefines.NProduction.BASE_NAVAL_EQUIPMENT_CONVERSION_IC_COST_FACTOR  = 0.01
	NDefines.NProduction.DEFAULT_MAX_NAV_FACTORIES_PER_LINE = 5
	NDefines.NProduction.CONVOY_MAX_NAV_FACTORIES_PER_LINE = 15
	NDefines.NProduction.CAPITAL_SHIP_MAX_NAV_FACTORIES_PER_LINE = 5
	NDefines.NProduction.MINIMUM_NUMBER_OF_FACTORIES_TAKEN_BY_CONSUMER_GOODS_VALUE = 0		-- The minimum number of factories we have to put on consumer goods, by value.
	NDefines.NProduction.MINIMUM_NUMBER_OF_FACTORIES_TAKEN_BY_CONSUMER_GOODS_PERCENT = 0	-- The minimum number of factories we have to put on consumer goods, in percent.

	NDefines.NTechnology.MAX_SUBTECHS = 5
	NDefines.NTechnology.BASE_YEAR_AHEAD_PENALTY_FACTOR = 1.0
	NDefines.NTechnology.BASE_TECH_COST = 250 -- 100 is vanilla --300 was the old MD cost
	NDefines.NTechnology.MIN_RESEARCH_SPEED = 0.01 -- 0.10 in vanilla
	NDefines.NTechnology.MAX_TECH_SHARING_BONUS = 0.10 -- vanilla is 0.50 from Tech Sharing

	NDefines.NProject.SCIENTIST_SKILL_LEVEL_SPEED_MODIFIER = {		-- Bonus to apply to daily phase progress according to the skill level of the scientist
	    -0.10,    -- -1.0 means -100%         also name loc key is SCIENTIST_SKILL_LEVEL_NAME_0
		-0.05,  -- -0.05 means -5%			also name loc key is SCIENTIST_SKILL_LEVEL_NAME_1
		0.05,	-- 0 means no change		also name loc key is SCIENTIST_SKILL_LEVEL_NAME_2
		0.1,   -- 0.15 means +15%			...
		0.15,
		0.25,	-- Size MUST be SCIENTIST_SKILL_LEVEL_THRESHOLDS's size + 1
	}
	NDefines.NProject.BREAKTHROUGH_DAILY_SCIENTIST_SKILL_GAIN = 15       -- Amount in 1/100th percentage gained per skill when doing basic research. E.g. 5 = 0.05% per skill level.
	NDefines.NProject.BREAKTHROUGH_DAILY_TECHNOLOGY_GAIN = 10           -- Amount in 1/100th percentage. E.g. 25 = 0.25%
	NDefines.NProject.BREAKTHROUGH_DAILY_ROCKET_SITE_GAIN = 0		   -- Amount in 1/100th percentage gained per rocket site level. E.g. 1 = 0.01% per rocket site level.
	NDefines.NProject.BREAKTHROUGH_DAILY_NUCLEAR_REACTOR_GAIN = 0       -- Amount in 1/100th percentage gained per nuclear reactor. E.g. 2 = 0.02% per nuclear reactor.

	NDefines.NBuildings.MAX_BUILDING_LEVELS = 50
	NDefines.NBuildings.SAM_MISSION_SUPERIORITY = 15.0	-- How much air superiority each SAM mission gives per rocket wing performing SAM missions.
	NDefines.NBuildings.AIRBASE_CAPACITY_MULT = 50
	NDefines.NBuildings.ROCKETSITE_CAPACITY_MULT = 50
	NDefines.NBuildings.NAVALBASE_REPAIR_MULT = 0.075 -- 0.05 -- Each level of navalbase building repairs X strength and can repair as many ships as its level
	NDefines.NBuildings.RADAR_RANGE_MAX = 220
	NDefines.NBuildings.RADAR_INTEL_EFFECT = 60 -- 40
	NDefines.NBuildings.BASE_FACTORY_REPAIR = 0.25
	NDefines.NBuildings.MAX_SHARED_SLOTS = 56
	NDefines.NBuildings.OWNER_CHANGE_EXTRA_SHARED_SLOTS_FACTOR = 0.5
	NDefines.NBuildings.INFRASTRUCTURE_RESOURCE_BONUS = 0.05	--upped from 0.02, vanilla 0.2
	NDefines.NBuildings.ANTI_AIR_SUPERIORITY_MULT = 1.0 -- was 4.0 --Fucked with this to see

	NDefines.NMilitary.MAX_DIVISION_BRIGADE_WIDTH = 4 -- 5
	NDefines.NMilitary.MIN_DIVISION_BRIGADE_HEIGHT = 5
	NDefines.NMilitary.HOURLY_ORG_MOVEMENT_IMPACT = -0.1 -- -0.2
	NDefines.NMilitary.ZERO_ORG_MOVEMENT_MODIFIER = -0.2 -- -0.8
	NDefines.NMilitary.INFRASTRUCTURE_MOVEMENT_SPEED_IMPACT = -0.02 -- -0.05

	NDefines.NMilitary.SOFT_ATTACK_TARGETING_FACTOR = 1.0 -- 1.0
	NDefines.NMilitary.HARD_ATTACK_TARGETING_FACTOR = 1.4 -- 1.2 Increase the target priority of armored targets
	NDefines.NMilitary.PIERCING_THRESHOLDS = { 1.00, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.10, 0.00 } -- Adjusted these to give more granularity to armor vs pen
	NDefines.NMilitary.PIERCING_THRESHOLD_DAMAGE_VALUES = { 1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50 }
	NDefines.NMilitary.SPOTTING_QUALITY_DROP_HOURS = 6 -- 4
	NDefines.NMilitary.BASE_CHANCE_TO_AVOID_HIT = 80 -- 90
	NDefines.NMilitary.CHANCE_TO_AVOID_HIT_AT_NO_DEF = 50 -- 60
	NDefines.NMilitary.ARMOR_VS_AVERAGE = 0.35 -- 0.4 Decrease armor from individual units, to make needing to average armor out more important
	NDefines.NMilitary.PEN_VS_AVERAGE = 0.45 -- 0.4 Increase pen avaiable to units, so that infantry has a better chance against armor

	NDefines.NMilitary.CORPS_COMMANDER_DIVISIONS_CAP = 18 -- Vanilla 24
	NDefines.NMilitary.FIELD_MARSHAL_DIVISIONS_CAP = 15 --24
	NDefines.NMilitary.FIELD_MARSHAL_ARMIES_CAP = 4 -- Vanilla 5
	NDefines.NMilitary.BASE_DIVISION_SUPPORT_SLOT_COST = 5 -- 10
	NDefines.NMilitary.COMBAT_MINIMUM_TIME = 8 -- 4
	NDefines.NMilitary.LAND_COMBAT_ORG_DICE_SIZE = 4 -- 4
	NDefines.NMilitary.LAND_COMBAT_STR_DICE_SIZE = 3 -- 2
	NDefines.NMilitary.LAND_COMBAT_STR_DAMAGE_MODIFIER = 0.05 -- 0.05
	NDefines.NMilitary.LAND_COMBAT_ORG_DAMAGE_MODIFIER = 0.053 -- 0.053
	NDefines.NMilitary.LAND_AIR_COMBAT_STR_DAMAGE_MODIFIER = 0.08 -- 0.04
	NDefines.NMilitary.LAND_AIR_COMBAT_ORG_DAMAGE_MODIFIER = 0.08 -- 0.04
	NDefines.NMilitary.LAND_AIR_COMBAT_MAX_PLANES_PER_ENEMY_WIDTH = 2 -- 3
	NDefines.NMilitary.LAND_COMBAT_STR_ARMOR_ON_SOFT_DICE_SIZE = 4 -- 6
	NDefines.NMilitary.LAND_COMBAT_ORG_ARMOR_ON_SOFT_DICE_SIZE = 4 -- 6
	NDefines.NMilitary.LAND_COMBAT_STR_ARMOR_DEFLECTION_FACTOR = 0.4 -- 0.5
	NDefines.NMilitary.LAND_COMBAT_ORG_ARMOR_DEFLECTION_FACTOR = 0.4 -- 0.5
	NDefines.NMilitary.LAND_COMBAT_COLLATERAL_FACTOR = 0.05 -- 0.005
	NDefines.NMilitary.LAND_COMBAT_FORT_DAMAGE_CHANCE = 15
	NDefines.NMilitary.ATTRITION_DAMAGE_ORG = 0.04 -- 0.08
	NDefines.NMilitary.ATTRITION_EQUIPMENT_LOSS_CHANCE = 0.005 -- 0.1
	NDefines.NMilitary.ATTRITION_EQUIPMENT_PER_TYPE_LOSS_CHANCE = 0.005 -- 0.1
	NDefines.NMilitary.CHANCE_TO_AVOID_HIT_AT_NO_DEF = 50 -- 60
	NDefines.NMilitary.COMBAT_MOVEMENT_SPEED = 0.10
	NDefines.NMilitary.TACTIC_SWAP_FREQUENCEY = 24 -- 24
	NDefines.NMilitary.LAND_SPEED_MODIFIER = 0.05 -- 0.05
	NDefines.NMilitary.RIVER_CROSSING_PENALTY = -0.2 -- -0.3
	NDefines.NMilitary.RIVER_CROSSING_PENALTY_LARGE = -0.4 -- -0.6
	NDefines.NMilitary.RIVER_CROSSING_SPEED_PENALTY = -0.25 -- -0.25
	NDefines.NMilitary.RIVER_CROSSING_SPEED_PENALTY_LARGE = -0.45 -- -0.5
	NDefines.NMilitary.BASE_FORT_PENALTY = -0.075 -- -0.15
	NDefines.NMilitary.RECON_SKILL_IMPACT = 2.5 -- 5
	NDefines.NMilitary.ENEMY_AIR_SUPERIORITY_IMPACT = -0.45 -- -0.35
	NDefines.NMilitary.ENEMY_AIR_SUPERIORITY_SPEED_IMPACT = -0.4 -- -0.3
	NDefines.NMilitary.SLOWEST_SPEED = 4 -- 4
	NDefines.NMilitary.BASE_NIGHT_ATTACK_PENALTY = -0.6 -- -0.5
	NDefines.NMilitary.UNIT_DIGIN_CAP = 10 -- 5
	NDefines.NMilitary.EXPERIENCE_COMBAT_FACTOR = 0.05 -- 0.25
	NDefines.NMilitary.EXPERIENCE_LOSS_FACTOR = 0.7 -- 1.00
	NDefines.NMilitary.EQUIPMENT_COMBAT_LOSS_FACTOR = 0.7 -- 0.7
	NDefines.NMilitary.BATALION_CHANGED_EXPERIENCE_DROP = 0.25 -- 0.5
	NDefines.NMilitary.SUPPLY_GRACE = 336 -- 72
	NDefines.NMilitary.MAX_OUT_OF_SUPPLY_DAYS = 45 -- 30
	NDefines.NMilitary.OUT_OF_SUPPLY_SPEED = -0.6	-- -0.8
	NDefines.NMilitary.NON_CORE_SUPPLY_SPEED = -0.20 -- -0.5
	NDefines.NMilitary.NON_CORE_SUPPLY_AIR_SPEED = -0.10 -- -0.25
	NDefines.NMilitary.OUT_OF_SUPPLY_MORALE = -0.15 -- -0.30
	NDefines.NMilitary.AIR_SUPPORT_BASE = 0.5 -- 0.25
	NDefines.NMilitary.REINFORCE_CHANCE = 0.05 -- 0.02
	NDefines.NMilitary.PARACHUTE_DISRUPTED_AA_PENALTY = 0.75 -- 1
	NDefines.NMilitary.PARACHUTE_COMPLETE_ORG = 0.3 -- 0.1
	NDefines.NMilitary.PARACHUTE_ORG_REGAIN_PENALTY_DURATION = 80 -- 120
	NDefines.NMilitary.PARACHUTE_ORG_REGAIN_PENALTY_MULT = -0.6 -- -0.8
	NDefines.NMilitary.PARADROP_PENALTY = -0.15 -- -0.3
	NDefines.NMilitary.PARADROP_HOURS = 12 -- 48
	NDefines.NMilitary.ENCIRCLED_DISBAND_MANPOWER_FACTOR = 0.25 -- 0.20
	NDefines.NMilitary.ORG_LOSS_FACTOR_ON_CONQUER = 0.3 -- 0.2
	NDefines.NMilitary.PLANNING_MAX = 0.1 -- 0.3
	NDefines.NMilitary.CIVILWAR_ORGANIZATION_FACTOR = 1.0 -- 0.3
	NDefines.NMilitary.PLAN_CONSIDERED_GOOD = 2.5 -- 0.25
	NDefines.NMilitary.PLAN_PROVINCE_BASE_IMPORTANCE = 1.0 -- 2.0
	NDefines.NMilitary.PLAN_AREA_DEFENSE_ENEMY_UNIT_FACTOR = -3.0 -- -2.0
	NDefines.NMilitary.PLAN_EXECUTE_BALANCED_LIMIT = 2 -- 0
	NDefines.NMilitary.COMBAT_OVER_WIDTH_PENALTY = -1.5 -- -1
	NDefines.NMilitary.COMBAT_OVER_WIDTH_PENALTY_MAX = -0.66 -- -0.33
	NDefines.NMilitary.RETREAT_SPEED_FACTOR = 1.0 -- 0.25
	NDefines.NMilitary.WITHDRAWING_SPEED_FACTOR = 0.35 -- 0.15
	NDefines.NMilitary.STRATEGIC_SPEED_INFRA_BASE = 5.0               -- Base speed of strategic redeployment when not on railways
	NDefines.NMilitary.STRATEGIC_SPEED_INFRA_MAX = 10.0               -- Additional speed of strategic redeployment on max-level infrastructure
	NDefines.NMilitary.STRATEGIC_SPEED_RAIL_BASE = 20.0               -- Base speed of strategic redeployment when on railways -- vanilla is 15
	NDefines.NMilitary.STRATEGIC_SPEED_RAIL_MAX = 40.0                -- Additional speed of strategic redeployment on max-level railways -- vanilla is 25
	NDefines.NMilitary.STRATEGIC_REDEPLOY_ORG_RATIO = 0.5 -- 0.1
	NDefines.NMilitary.LAND_EQUIPMENT_BASE_COST = 5 -- 10 --Used to determine Upgrade Cost
	NDefines.NMilitary.LAND_EQUIPMENT_RAMP_COST = 3 -- 5
	NDefines.NMilitary.NAVAL_EQUIPMENT_BASE_COST = 15 -- 25
	NDefines.NMilitary.AIR_EQUIPMENT_BASE_COST = 25 -- 25
	NDefines.NMilitary.FASTER_ORG_REGAIN_MULT = 0.40 -- 1.0
	NDefines.NMilitary.SLOWER_ORG_REGAIN_MULT = -0.6 -- -0.5
	NDefines.NMilitary.FRONT_MIN_PATH_TO_REDEPLOY = 3 -- 8
	NDefines.NMilitary.BASE_CAPTURE_EQUIPMENT_RATIO = 0.075 -- 0.0
	NDefines.NMilitary.GARRISON_ORDER_ARMY_CAP_FACTOR = 2.0 -- 3.0
	NDefines.NMilitary.ACCLIMATIZATION_SPEED_GAIN = 0.1 -- 0.15
	NDefines.NMilitary.ACCLIMATIZATION_LOSS_SPEED_FACTOR = 0.5 -- 2.0
	NDefines.NMilitary.UNIT_LEADER_ASSIGN_TRAIT_COST = 15.0 -- 15
	NDefines.NMilitary.ATTACHED_WINGS_ORDER_UPDATE_DAYS = 1 -- 5
	NDefines.NMilitary.BORDER_WAR_WIN_DAYS_AGAINST_EMPTY_OPPONENTS = 21 -- 14
	NDefines.NMilitary.XP_GAIN_FOR_SHATTERING = 20.0 -- 35.0
	NDefines.NMilitary.XP_GAIN_PER_OVERRUN_UNIT = 20.0 -- 35.0
	NDefines.NMilitary.ARMY_IDLE_FUEL_MULT = 0.05 -- 0.0
	NDefines.NMilitary.OUT_OF_FUEL_SPEED_MULT = 0.7 -- 0.4
	NDefines.NMilitary.ANTI_AIR_TARGETTING_TO_CHANCE = 0.02 -- 0.07
	NDefines.NMilitary.ANTI_AIR_ATTACK_TO_AMOUNT = 0.005 -- 0.005
	NDefines.NMilitary.UNIT_EXPERIENCE_PER_COMBAT_HOUR = 0.0003 -- 0.0001
	NDefines.NMilitary.UNIT_EXPERIENCE_SCALE = 0.25 -- 1.0
	NDefines.NMilitary.UNIT_EXPERIENCE_PER_TRAINING_DAY = 0.0035 -- 0.0015
	NDefines.NMilitary.TRAINING_EXPERIENCE_SCALE = 92.0 -- 62.0
	NDefines.NMilitary.UNIT_EXP_LEVELS = { 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1 }
	NDefines.NMilitary.ARMY_EXP_BASE_LEVEL = 3
	NDefines.NMilitary.TRAINING_MAX_LEVEL = 5
	NDefines.NMilitary.DEPLOY_TRAINING_MAX_LEVEL = 2
	NDefines.NMilitary.FIELD_EXPERIENCE_SCALE = 0.001 -- 0.0015
	NDefines.NMilitary.FIELD_EXPERIENCE_MAX_PER_DAY = 2 -- 1.2
	NDefines.NMilitary.LEADER_EXPERIENCE_SCALE = 1.25 -- 1.0
	NDefines.NMilitary.BASE_LEADER_TRAIT_GAIN_XP = 0.55 -- 0.45
	NDefines.NMilitary.ARMY_LEADER_XP_GAIN_PER_UNIT_IN_COMBAT = 0.175 -- 0.1
	NDefines.NMilitary.TRAINING_ATTRITION = 0.0001				-- amount of extra attrition from being in training. Base value 0.05 Reduced to prevent training destroying all equipment
	NDefines.NMilitary.MAX_ARMY_EXPERIENCE = 1000 --500 --Increased Max Experience cuz reasons
	NDefines.NMilitary.MAX_AIR_EXPERIENCE = 1000 --500
	NDefines.NMilitary.MAX_NAVY_EXPERIENCE = 1000 --500
	NDefines.NMilitary.SHIP_MORALE_TO_ORG_REGAIN_BASE = 0.5 -- buffed from 0.2 -- Handles the Hourly Reorganization
	NDefines.NMilitary.ENGAGEMENT_WIDTH_PER_WIDTH = 3.0			-- how much enemy combat width we are allowed to engage per width of our own -- vanilla is 2.0
	NDefines.NMilitary.DAMAGE_SPLIT_ON_FIRST_TARGET = 0.29 -- increased by 0.03 by cnc tech, 1995 is vanilla level, vanilla 0.35

	NDefines.NMilitary.NEW_ARMY_LEADER_LEVEL_CHANCES = {			-- chances for new army leaders to start at a given level
		0.90, -- 90% for level one
		0.10  -- 10% for level two
			  -- 0% for level three to ten
	}
	NDefines.NMilitary.BATALION_NOT_CHANGED_EXPERIENCE_DROP = 0.0		-- Division experience drop if unit has same batalion
	NDefines.NMilitary.BATALION_CHANGED_EXPERIENCE_DROP = 0.75		-- Division experience drop if unit has different batalion

	--Operative Stuff in NMilitary
	NDefines.NMilitary.NEW_OPERATIVE_RANDOM_PERSONALITY_TRAIT_CHANCES = {  			-- chances to gain a personality trait for new operatives
		0.6, -- up from vanilla 50% for first trait
		0.2  -- up from vanilla 10% for second trait after that
	}
	NDefines.NMilitary.NEW_OPERATIVE_RANDOM_BASIC_TRAIT_CHANCES = {  				-- chances to gain a basic trait for new operatives
		0.35, -- up from vanilla 25% for first trait
		0.15  -- up from vanilla 5% for second trait after that
	}
	NDefines.NMilitary.WAR_SCORE_AIR_WORTH = 0.02	            	-- how much strategic bombing will affect warscore
	NDefines.NMilitary.WAR_SCORE_AIR_WORTH_CAP = 500				-- the warscore liit we get from strategic bombing
	NDefines.NMilitary.WAR_SCORE_AIR_MONTHLY_FALLOFF = 20			-- how much the warscore we got from the strategic bombing falls off every month.
	NDefines.NMilitary.WAR_SCORE_LOSSES_RATIO = 4	         	-- Scale how much losses will affect warscore ( per 1000 losses ).
	NDefines.NMilitary.NUKE_MIN_DAMAGE_PERCENT = 0.0					-- Minimum damage from nukes as a percentage of current strength/organisation
	NDefines.NMilitary.NUKE_MAX_DAMAGE_PERCENT = 0.0					-- Minimum damage from nukes as a percentage of current strength/organisation
	NDefines.NMilitary.NUKE_DELAY_HOURS = 0.0							-- How many hours does it take for the nuclear drop to happen

	NDefines.NAir.THRUST_WEIGHT_AGILITY_FACTOR = 0 -- 0.5
	NDefines.NAir.ACCIDENT_CHANCE_BASE = 0.05 -- vanilla 0.1
	NDefines.NAir.ACCIDENT_CHANCE_RELIABILITY_MULT = 0.2 -- vanilla 2.0 Multiplier to accident chance per point of missing reliability.
	NDefines.NAir.ACCIDENT_CHANCE_CARRIER_MULT = 0.5 -- vanilla 1.5
	NDefines.NAir.ACCIDENT_CHANCE_BALANCE_MULT = 0.02 -- vanilla 0.1
	NDefines.NAir.ACCIDENT_EFFECT_MULT = 0.007 -- vanill 0.007
	NDefines.NAir.AIR_WING_MAX_STATS_ATTACK = 999 -- 100
	NDefines.NAir.AIR_WING_MAX_STATS_DEFENCE = 999 -- 100
	NDefines.NAir.AIR_WING_MAX_STATS_AGILITY = 999 -- 100
	NDefines.NAir.AIR_WING_MAX_STATS_SPEED = 4000 -- 800
	NDefines.NAir.AIR_WING_MAX_STATS_BOMBING = 999 -- 100
	NDefines.NAir.AIR_WING_AVERAGE_SIZE = 50 -- Eyeballed average amount of airplanes in the airwings
	NDefines.NAir.AIR_WING_BOMB_DAMAGE_FACTOR = 20 -- 2
	NDefines.NAir.AI_ALLOWED_PLANES_KEPT_IN_RESERVE = 0.15
	NDefines.NAir.BIGGEST_AGILITY_FACTOR_DIFF = 6 -- 2.5
	NDefines.NAir.COMBAT_BETTER_AGILITY_DAMAGE_REDUCTION = 0.70 -- 0.3
	NDefines.NAir.COMBAT_BETTER_SPEED_DAMAGE_INCREASE = 0.45 -- 0.6
	NDefines.NAir.COMBAT_MULTIPLANE_CAP = 3.0 -- 3.0
	NDefines.NAir.COMBAT_DAMAGE_STATS_MULTILPIER = 0.3 -- 0.2
	NDefines.NAir.COMBAT_DAMAGE_SCALE = 1.1 -- 0.25
	NDefines.NAir.COMBAT_DAMAGE_SCALE_CARRIER = 6 -- 6
	NDefines.NAir.COMBAT_MAX_WINGS_AT_ONCE = 10000 -- 10000 --Upped the count to ensure more airusages and coverage
	NDefines.NAir.COMBAT_MAX_WINGS_AT_GROUND_ATTACK = 7000 -- 10000
	NDefines.NAir.COMBAT_MAX_WINGS_AT_ONCE_PORT_STRIKE = 7000 -- 10000
	NDefines.NAir.DETECT_CHANCE_FROM_OCCUPATION = 0.05 -- 0.10
	NDefines.NAir.DETECT_CHANCE_FROM_RADARS = 0.85 -- 0.5
	NDefines.NAir.DETECT_CHANCE_FROM_AIRCRAFTS = 0.975 -- 0.8
	NDefines.NAir.DETECT_CHANCE_FROM_AIRCRAFTS_EFFECTIVE_COUNT = 100 -- 3000
	NDefines.NAir.DETECT_CHANCE_FROM_NIGHT = -0.10 -- -0.2
	NDefines.NAir.CARRIER_HOURS_DELAY_AFTER_EACH_COMBAT = 4 -- 4
	NDefines.NAir.HOURS_DELAY_AFTER_EACH_COMBAT = 4 -- 4
	NDefines.NAir.NAVAL_STRIKE_TARGETTING_TO_AMOUNT = 0.3 -- 0.3
	NDefines.NAir.NAVAL_STRIKE_DETECTION_BALANCE_FACTOR = 0.65 -- 0.7
	NDefines.NAir.NAVAL_RECON_DETECTION_BALANCE_FACTOR = 0.875 -- 0.7
	NDefines.NAir.NAVAL_STRIKE_DAMAGE_TO_STR = 1 -- 2
	NDefines.NAir.NAVAL_STRIKE_DAMAGE_TO_ORG = 1.5 -- 3
	NDefines.NAir.NAVAL_STRIKE_CARRIER_MULTIPLIER = 7.5 -- 5.0
	NDefines.NAir.ACCIDENT_CHANCE_BASE = 0.025 -- 0.05
	NDefines.NAir.ACCIDENT_CHANCE_CARRIER_MULT = 0.875 -- 2.0
	NDefines.NAir.ACCIDENT_CHANCE_BALANCE_MULT = 0.25 -- 0.5
	NDefines.NAir.AIR_AGILITY_TO_NAVAL_STRIKE_AGILITY = 0.04 -- 0.01
	NDefines.NAir.AIR_DAMAGE_TO_DIVISION_LOSSES = 1.5 -- 1.0
	NDefines.NAir.BASE_STRATEGIC_BOMBING_HIT_SHIP_CHANCE = 0.30 -- 0.01
	NDefines.NAir.BASE_STRATEGIC_BOMBING_HIT_SHIP_DAMAGE_FACTOR = 80 -- 50
	NDefines.NAir.BASE_STRATEGIC_BOMBING_HIT_PLANE_CHANCE = 0.75 -- 0.5
	NDefines.NAir.BASE_STRATEGIC_BOMBING_HIT_PLANE_DAMAGE_FACTOR = 0.5 -- 0.2
	NDefines.NAir.AIR_COMBAT_FINAL_DAMAGE_SCALE = 0.25 -- 0.015 was 0.01 in MD
	NDefines.NAir.AIR_COMBAT_FINAL_DAMAGE_PLANES = 50 -- 50
	NDefines.NAir.AIR_COMBAT_FINAL_DAMAGE_PLANES_FACTOR = 0.1 -- 0.1 was 0.04 in MD
	NDefines.NAir.AA_INDUSTRY_AIR_DAMAGE_FACTOR = -0.06 -- -0.12
	NDefines.NAir.ANTI_AIR_PLANE_DAMAGE_FACTOR = 0.01 -- 0.8
	NDefines.NAir.ANTI_AIR_PLANE_DAMAGE_CHANCE = 0.04 -- 0.1
	NDefines.NAir.AIR_DEPLOYMENT_DAYS = 1 -- 2
	NDefines.NAir.ANTI_AIR_ATTACK_TO_DAMAGE_REDUCTION_FACTOR = 4 -- 1.0
	NDefines.NAir.ANTI_AIR_MAXIMUM_DAMAGE_REDUCTION_FACTOR = 0.90 -- 0.75
	NDefines.NAir.NAVAL_STRIKE_BASE_STR_TO_PLANES_RATIO = 0.06 -- 0.03
	NDefines.NAir.NAVAL_COMBAT_EXTERNAL_PLANES_JOIN_RATIO = 0.025 -- 0.05
	NDefines.NAir.NAVAL_COMBAT_EXTERNAL_PLANES_JOIN_RATIO_PER_DAY = 1 -- 0.2
	NDefines.NAir.NAVAL_COMBAT_EXTERNAL_PLANES_MIN_CAP = 1 -- 20
	NDefines.NAir.EFFICIENCY_REGION_CHANGE_PENALTY_FACTOR = 0.2 -- 0.9
	NDefines.NAir.AIR_WING_XP_MAX = 1500.0 -- 1000.0
	NDefines.NAir.AIR_WING_XP_TRAINING_MAX = 700 -- 300
	NDefines.NAir.AIR_WING_XP_LEVELS = { 100, 250, 400, 550, 700, 850, 1000, 1150, 1300 } -- {100, 300, 700, 900}
	NDefines.NAir.AIR_WING_XP_LOSS_WHEN_KILLED = 400
	NDefines.NAir.AIR_WING_XP_TRAINING_MISSION_GAIN_DAILY = 2.5 -- 3.3
	NDefines.NAir.AIR_WING_XP_AIR_VS_AIR_COMBAT_GAIN = 2.0 -- 0.8
	NDefines.NAir.AIR_WING_XP_GROUND_MISSION_COMPLETED_GAIN = 1.2 -- 0.28
	NDefines.NAir.AIR_WING_XP_RECON_MISSION_COMPLETED_GAIN = 0.12 -- 0.05
	NDefines.NAir.AIR_WING_COUNTRY_XP_FROM_TRAINING_FACTOR = 0.01 -- 0.005
	NDefines.NAir.AIR_WING_XP_TRAINING_MISSION_ACCIDENT_FACTOR = 0.85 -- 1.5
	NDefines.NAir.AIR_WING_XP_LOSS_REDUCTION_OVER_FRIENDLY_TERRITORY_FACTOR = 0.6 -- 0.3
	NDefines.NAir.CARRIER_PLANES_AMOUNT_FOR_POSITIONING = 30 -- 50
	NDefines.NAir.CAS_NIGHT_ATTACK_FACTOR = 0.5 -- 0.1
	NDefines.NAir.BOMBING_TARGETING_RANDOM_FACTOR = 0.15 -- 0.25
	NDefines.NAir.RECON_LAND_SPOT_CHANCE = 0.07 -- 0.02
	NDefines.NAir.CAPACITY_PENALTY = 4 -- 2
	NDefines.NAir.DISRUPTION_FACTOR = 6.0 -- 4.0
	NDefines.NAir.DISRUPTION_FACTOR_CARRIER = 8.0 -- 8.0
	NDefines.NAir.CARRIER_SIZE_STAT_INCREMENT = 10 -- 10
	NDefines.NAir.MIN_PLANE_COUNT_PARADROP = 5 -- 50 is vanilla
	NDefines.NAir.BASE_UNIT_WEIGHT_IN_TRANSPORT_PLANES = 5 -- fuck this fucking define fuck you. 45 is vanilla
	NDefines.NAir.MISSILE_LAUNCHER_CAPACITY = 50
	NDefines.NAir.MISSILE_LAUNCHER_SLOTS = 10
	NDefines.NAir.MAX_QUICK_WINGS_FOR_AIR_SUPERIORITY = 8 -- Thank you for the idea Ebby
	NDefines.NAir.MISSION_FUEL_COSTS = {
		1.0, -- AIR_SUPERIORITY
		1.0, -- CAS
		0.4, -- INTERCEPTION
		1.0, -- STRATEGIC_BOMBER
		1.0, -- NAVAL_BOMBER
		1.0, -- DROP_NUKE
		1.0, -- PARADROP
		0.75, -- NAVAL_KAMIKAZE
		1.0, -- PORT_STRIKE
		1.0, -- ATTACK_LOGISTICS
		1.0, -- AIR_SUPPLY
		0.4, -- TRAINING
		1.0, -- NAVAL_MINES_PLANTING
		1.0, -- NAVAL_MINES_SWEEPING
		1.0, -- RECON
		1.0, -- NAVAL_PATROL
		0.0, -- BARRAGE
		0,0, -- NUCLEAR
		0,0, -- SAM
	}

	NDefines.NNavy.MAX_SUBMARINES_PER_AUTO_TASK_FORCE = 4 -- 30
	NDefines.NNavy.BEST_CAPITALS_TO_CARRIER_RATIO = 4 -- 1
	NDefines.NNavy.BEST_CAPITALS_TO_SCREENS_RATIO = 0.5 -- 0.25
	NDefines.NNavy.DETECTION_CHANCE_BALANCE = 1.5 -- 2.5
	NDefines.NNavy.DECRYPTION_SPOTTING_BONUS = 0.3 -- 0.2
	NDefines.NNavy.COMBAT_EVASION_TO_HIT_CHANCE_TORPEDO_MULT = 1 -- 40
	NDefines.NNavy.COMBAT_LOW_ORG_HIT_CHANCE_PENALTY = -0.8 -- -0.5
	NDefines.NNavy.COMBAT_TORPEDO_CRITICAL_CHANCE = 0.85 -- 0.2
	NDefines.NNavy.COMBAT_TORPEDO_CRITICAL_DAMAGE_MULT = 5.0 -- 2.0
	NDefines.NNavy.COMBAT_DAMAGE_RANDOMNESS = 0.75 -- 0.5, increased this number to decrease the amount of randomization in damage
	NDefines.NNavy.COMBAT_DAMAGE_TO_STR_FACTOR = 1.6-- 1.6 -- 0.6
	NDefines.NNavy.COMBAT_DAMAGE_TO_ORG_FACTOR = 1.6 -- 1.9 -- 1
	NDefines.NNavy.COMBAT_DAMAGE_REDUCTION_ON_RETREAT = 0.75 -- 0.8
	NDefines.NNavy.COMBAT_ESCAPING_SPEED_BALANCE = 0.9 -- 0.8
	NDefines.NNavy.COMBAT_SHIP_SPEED_TO_FIELD_FACTOR = 0.15 -- 0.03
	NDefines.NNavy.COMBAT_MAX_DISTANCE_TO_CENTER_LINE = 350 -- 50
	NDefines.NNavy.COMBAT_MAX_DISTANCE_TO_ARRIVE = 600 -- 80
	NDefines.NNavy.COMBAT_MIN_DURATION = 16 -- 8
	NDefines.NNavy.COMBAT_CHASE_RESIGNATION_HOURS = 6 -- 8
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_LOW = 0.35 -- 0.2
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_MEDIUM = 0.55 -- 0.5
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_HIGH = 0.85 -- 0.9
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_LOW_COMBAT = 0.35 -- 0.6
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_MEDIUM_COMBAT = 0.5 -- 0.3
	NDefines.NNavy.REPAIR_AND_RETURN_PRIO_HIGH_COMBAT = 0.75 -- 0.1
	NDefines.NNavy.REPAIR_AND_RETURN_UNIT_DYING_STR = 0.35 -- 0.2
	NDefines.NNavy.NAVY_EXPENSIVE_IC = 18000 -- 5500
	NDefines.NNavy.CONVOY_EFFICIENCY_MIN_VALUE = 0.1 -- 0.05
	NDefines.NNavy.AMPHIBIOUS_LANDING_PENALTY = -0.5 -- -0.7
	NDefines.NNavy.BASE_CARRIER_SORTIE_EFFICIENCY = 0.5 -- 0.5
	NDefines.NNavy.NAVAL_SPEED_MODIFIER = 0.1 -- 0.1
	NDefines.NNavy.NAVAL_TRANSFER_BASE_SPEED = 12 -- 6
	NDefines.NNavy.NAVAL_INVASION_PREPARE_HOURS = 96 -- 168
	NDefines.NNavy.ANTI_AIR_TARGETING = 2.4 -- 0.9
	NDefines.NNavy.ANTI_AIR_TARGETTING_TO_CHANCE = 4 -- 0.2
	NDefines.NNavy.ANTI_AIR_ATTACK_TO_AMOUNT = 0.0005 -- 0.01
	NDefines.NNavy.SHIP_TO_FLEET_ANTI_AIR_RATIO = 0.1 -- 0.2
	NDefines.NNavy.ANTI_AIR_POW_ON_INCOMING_AIR_DAMAGE = 0.2 -- 0.2
	NDefines.NNavy.ANTI_AIR_MULT_ON_INCOMING_AIR_DAMAGE = 0.35 -- 0.15
	NDefines.NNavy.MAX_ANTI_AIR_REDUCTION_EFFECT_ON_INCOMING_AIR_DAMAGE = 0.99 -- 0.75
	NDefines.NNavy.ENEMY_AIR_SUPERIORITY_IMPACT = -1.25

	NDefines.NNavy.MISSION_FUEL_COSTS = {
		0.1, -- HOLD (consumes fuel HOLD_MISSION_MOVEMENT_COST fuel while moving)
		0.8, -- PATROL
		1.0, -- STRIKE FORCE (does not cost fuel at base, and uses IN_COMBAT_FUEL_COST in combat. this is just for the movement in between)
		1.0, -- CONVOY RAIDING
		0.8, -- CONVOY ESCORT
		1.0, -- MINES PLANTING
		1.0, -- MINES SWEEPING
		0.8, -- TRAIN
		0.0, -- RESERVE_FLEET (consumes fuel HOLD_MISSION_MOVEMENT_COST fuel while moving)
		1.0, -- NAVAL_INVASION_SUPPORT (does not cost fuel at base, only costs while doing bombardment and escorting units)
	}
	NDefines.NNavy.ORG_COST_WHILE_MOVING = {
		0.3, -- HOLD
		0.2, -- PATROL
		0.25, -- STRIKE FORCE
		0.2, -- CONVOY RAIDING
		0.2, -- CONVOY ESCORT
		0.2, -- MINES PLANTING
		0.2, -- MINES SWEEPING
		0.2, -- TRAIN
		0.3, -- RESERVE_FLEET
		0.2, -- NAVAL_INVASION_SUPPORT
	}
	NDefines.NNavy.MISSION_SUPREMACY_RATIOS = {
		0.5, -- HOLD
		1.0, -- PATROL
		0.5, -- STRIKE FORCE
		0.75, -- CONVOY RAIDING
		0.75, -- CONVOY ESCORT
		0.35, -- MINES PLANTING
		0.35, -- MINES SWEEPING
		0.20, -- TRAIN
		0.0, -- RESERVE_FLEET
		1.0, -- NAVAL_INVASION_SUPPORT
	}
	NDefines.NNavy.MIN_HOURS_TO_SHUFFLE_NEWLY_ASSIGNED_PATROLS = 10 * 24
	NDefines.NNavy.BASE_SPOTTING_FROM_RADAR = 15 -- 5
	NDefines.NNavy.BASE_SPOTTING = 5 -- 1
	NDefines.NNavy.SPOTTING_MULTIPLIER_FOR_SUB = 0.60 -- Reduced by 40% -- Should help subs
	NDefines.NNavy.SPOTTING_MULTIPLIER_FOR_SURFACE = 1.2 -- buffed by 10%
	NDefines.NNavy.ESCAPE_SPEED_HIDDEN_SUB = 0.45 --escape speed
	NDefines.NNavy.ESCAPE_SPEED_SUB_BASE = 0.30 -- escape speed base
	NDefines.NNavy.SUB_DETECTION_CHANCE_BASE = 3 -- 5 -- huge buff to subs detection
	NDefines.NNavy.SUB_DETECTION_CHANCE_BASE_SPOTTING_EFFECT = 0.3 -- 0.5
	NDefines.NNavy.SUB_DETECTION_CHANCE_SPOTTING_SPEED_EFFECT = 1.2 -- 2.0
	NDefines.NNavy.SUB_DETECTION_CHANCE_BASE_SPOTTING_POW_EFFECT = 1.01
	NDefines.NNavy.SHORE_BOMBARDMENT_CAP = 1 -- Reduced to 100% from 200% -- 25% is vanilla
	NDefines.NNavy.HEAVY_GUN_ATTACK_TO_SHORE_BOMBARDMENT = 0.005
	NDefines.NNavy.LIGHT_GUN_ATTACK_TO_SHORE_BOMBARDMENT = 0.01
	NDefines.NNavy.COMBAT_BASE_HIT_CHANCE = 0.1
	NDefines.NNavy.COMBAT_MIN_HIT_CHANCE = 0.05	-- never less hit chance then this?
	NDefines.NNavy.MIN_HIT_PROFILE_MULT = 0.1 -- largest hit profile penalty to hitting (higher value of the define makes ships easier to hit, i assume by reducing the penalty caused by small hit profile of target ship)
	NDefines.NNavy.GUN_HIT_PROFILES = { -- hit profiles for guns, if target ih profile is lower the gun will have lower accuracy
		150.0,	-- Anti-Ship Missiles
		145.0,	-- torpedos
		200.0,	-- Guns
	}
	NDefines.NNavy.BASE_GUN_COOLDOWNS = { -- number of hours for a gun to be ready after shooting
		1.0,	-- Anti-Ship Missiles
		3.0,	-- torpedos
		1.0,	-- Guns
	}

	NDefines.NNavy.DEPTH_CHARGES_HIT_CHANCE_MULT = 1.5 -- multiplies hit chance of depth charges
	NDefines.NNavy.DEPTH_CHARGES_DAMAGE_MULT = 2 	-- multiplies damage of depth charges
	NDefines.NNavy.DEPTH_CHARGES_HIT_PROFILE = 24.0	-- hit profile for depth charges, default 100
	NDefines.NNavy.CARRIER_STACK_PENALTY = 2
	NDefines.NNavy.CARRIER_STACK_PENALTY_EFFECT = 0.5
	NDefines.NNavy.CARRIER_ONLY_COMBAT_ACTIVATE_TIME = 0 -- 0
	NDefines.NNavy.CAPITAL_ONLY_COMBAT_ACTIVATE_TIME = 2 -- 6
	NDefines.NNavy.ALL_SHIPS_ACTIVATE_TIME = 4 -- 8
	NDefines.NNavy.NAVAL_MINES_DECAY_AT_PEACE_TIME = 0.05 -- 0.25
	NDefines.NNavy.ATTRITION_WHILE_MOVING_FACTOR = 2.5 -- 1.5
	NDefines.NNavy.ATTRITION_DAMAGE_ORG = 0.03 -- 0.01
	NDefines.NNavy.ATTRITION_DAMAGE_STR = 0.09 -- 0.03
	NDefines.NNavy.ATTRITION_STR_DAMAGE_CHANCE = 0.4 -- 0.2
	NDefines.NNavy.TRAINING_ACCIDENT_CHANCES = 0.005 -- 0.02
	NDefines.NNavy.TRAINING_ACCIDENT_STRENGTH_LOSS_FACTOR = 0.02 -- 0.05
	NDefines.NNavy.TRAINING_EXPERIENCE_FACTOR = 0.15 -- 0.3
	NDefines.NNavy.UNIT_EXPERIENCE_PER_COMBAT_HOUR = 15 -- 10
	NDefines.NNavy.LEADER_EXPERIENCE_SCALE = 2 -- 1
	NDefines.NNavy.CHANCE_TO_DAMAGE_PART_ON_CRITICAL_HIT = 0.01 -- 0.1
	NDefines.NNavy.CHANCE_TO_DAMAGE_PART_ON_CRITICAL_HIT_FROM_AIR = 0.1 -- 0.1
	NDefines.NNavy.SCREEN_RATIO_FOR_FULL_SCREENING_FOR_CAPITALS = 1.5 -- 3.0
	NDefines.NNavy.SCREEN_RATIO_FOR_FULL_SCREENING_FOR_CAPITALS = 1.5 -- 3.0
	NDefines.NNavy.SCREEN_RATIO_FOR_FULL_SCREENING_FOR_CONVOYS = 0.25 -- 0.5
	NDefines.NNavy.CAPITAL_RATIO_FOR_FULL_SCREENING_FOR_CONVOYS = 0.1 -- 0.25
	NDefines.NNavy.NEW_NAVY_LEADER_LEVEL_CHANCES = {                                -- chances for new navy leaders to start at a given level
		0.90, -- 90% for level one
		0.10  -- 10% for level two
              -- 0% for level three to ten
	}
	NDefines.NNavy.CARRIER_TASKFORCE_MAX_CARRIER_COUNT = 1 		-- optimum carrier count for carrier taskforces
	NDefines.NNavy.CAPITAL_TASKFORCE_MAX_CAPITAL_COUNT = 6 		-- optimum capital count for capital taskforces
	NDefines.NNavy.SCREEN_TASKFORCE_MAX_SHIP_COUNT = 2			-- optimum screen count for screen taskforces
	NDefines.NNavy.SUB_TASKFORCE_MAX_SHIP_COUNT = 4				-- optimum sub count for sub taskforces
	NDefines.NNavy.MAX_SUBMARINES_PER_AUTO_TASK_FORCE = 4
	NDefines.NNavy.MAX_CAPITALS_PER_AUTO_TASK_FORCE = 6

	NDefines.NNavy.MIN_CAPITALS_FOR_CARRIER_TASKFORCE = 4			-- carrier fleets will at least have this amount of capitals
	NDefines.NNavy.CAPITALS_TO_CARRIER_RATIO = 4				-- capital to carrier count in carrier taskfoces
	NDefines.NNavy.SCREENS_TO_CAPITAL_RATIO = 2				-- screens to capital/carrier count in carrier & capital taskforces

	NDefines.NNavy.BASE_POSITIONING = 0.70 -- 1.0
	NDefines.NNavy.RELATIVE_SURFACE_DETECTION_TO_POSITIONING_FACTOR = 0.01 -- 0.01
	NDefines.NNavy.MAX_POSITIONING_BONUS_FROM_SURFACE_DETECTION = 0 -- 0.0
	NDefines.NNavy.HIGHER_SHIP_RATIO_POSITIONING_PENALTY_FACTOR = 0.5 -- 0.25
	NDefines.NNavy.MAX_POSITIONING_PENALTY_FROM_HIGHER_SHIP_RATIO = 1 -- 0.5
	NDefines.NNavy.HIGHER_CARRIER_RATIO_POSITIONING_PENALTY_FACTOR = 0.4 -- 0.2
	NDefines.NNavy.MAX_CARRIER_RATIO_POSITIONING_PENALTY_FACTOR = 0.2 -- 0.2
	NDefines.NNavy.POSITIONING_PENALTY_FOR_SHIPS_JOINED_COMBAT_AFTER_IT_STARTS = 0.025 -- 0.05
	NDefines.NNavy.MAX_POSITIONING_PENALTY_FOR_NEWLY_JOINED_SHIPS = 0.3 -- 0.5
	NDefines.NNavy.POSITIONING_PENALTY_HOURLY_DECAY_FOR_NEWLY_JOINED_SHIPS = 0.04 -- 0.002
	NDefines.NNavy.DAMAGE_PENALTY_ON_MINIMUM_POSITIONING = 0.9 -- 0.5
	NDefines.NNavy.SCREENING_EFFICIENCY_PENALTY_ON_MINIMUM_POSITIONING = 0.65 -- 0.5
	NDefines.NNavy.AA_EFFICIENCY_PENALTY_ON_MINIMUM_POSITIONING = 0.9 -- 0.7
	NDefines.NNavy.SUBMARINE_REVEAL_ON_MINIMUM_POSITIONING = 3.0 -- 2.0

	NDefines.NNavy.NAVAL_COMBAT_SUB_DETECTION_FACTOR = 1.5      -- balance value for sub detection in combat by ships
	NDefines.NNavy.SUBMARINE_HIDE_TIMEOUT = 20		-- Amount of in-game-hours that takes the submarine (with position unrevealed), to hide.
	NDefines.NNavy.SUBMARINE_REVEALED_TIMEOUT = 16		-- Amount of in-game-hours that makes the submarine visible if it is on the defender side.
	NDefines.NNavy.SUBMARINE_REVEAL_BASE_CHANCE = 8		-- Base factor for submarine detection. It's modified by the difference of a spotter's submarines detection vs submarine visibility. Use this variable for game balancing. setting this too low will cause bad spotting issues.
	NDefines.NNavy.SUBMARINE_REVEAL_POW = 3.0		-- A scaling factor that is applied to the reveal chance in order to make large differences in detection vs visibility more pronounced
	NDefines.NNavy.SUBMARINE_BASE_TORPEDO_REVEAL_CHANCE = 0.05		-- Chance of a submarine being revealed when it fires. 1.0 is 100%. this chance is then multiplied with modifier created by comparing firer's visibiility and target's detection

	-- those two work together in the formula f(x) = Y(x/(x+X)) where Y is MAX and X is SLOPE
	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_MAX = 10.0
	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_SLOPE = 10.0						-- lower means sharper curve (ramps up very fast, then flatten out very fast). Must be >0

	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_EXTERNAL_FACTOR = 1				-- Factor applied to the stats of external air planes
	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_INTERNAL_EFFICIENCY_FACTOR = 1.0			-- Factor of Carrier's sortie efficiency on the stats bellow
	NDefines.NNavy.NAVAL_COMBAT_AIR_AGILITY_TO_SUB_DETECTION = 0.0					-- Factor to apply to the agility of air planes active in a naval combat to deduce their contibution to sub detection
	NDefines.NNavy.NAVAL_COMBAT_AIR_STRIKE_ATTACK_TO_SUB_DETECTION = 0.0					-- Same, but for strike attack (aka naval attack)
	NDefines.NNavy.NAVAL_COMBAT_AIR_STRIKE_TARGETING_TO_SUB_DETECTION = 0.0				-- Same, but for strike targeting (aka naval targeting)
	NDefines.NNavy.NAVAL_COMBAT_AIR_MAX_SPEED_TO_SUB_DETECTION = 0.0					-- Same, but for Max Speed
	NDefines.NNavy.NAVAL_COMBAT_AIR_PLANE_COUNT_TO_SUB_DETECTION = 1				-- Factor applied to the number of active plane in a naval combat to deduce their contribution to sub detection
	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_DECAY_RATE = 1.0					-- Factor to decay the value of sub detection contributed by planes on the last hour. Note: the maximum value between the decayed value and the newly computed one is taken into account. A decay rate of 1 means that nothing is carried over, the previous value is zerod out. A decay rate of 0 means that the previous value is carried over as is.
	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_DETECTION_FACTOR = 0.0						-- A global factor that applies after all others, right before the sub detection contributed by plane is added to the global sub detection of a combatant

	NDefines.NNavy.NAVAL_COMBAT_AIR_SUB_TARGET_SCORE = 10                             -- scoring for target picking for planes inside naval combat, one define per ship typ
	NDefines.NNavy.NAVAL_COMBAT_AIR_CAPITAL_TARGET_SCORE = 25
	NDefines.NNavy.NAVAL_COMBAT_AIR_CARRIER_TARGET_SCORE = 200
	NDefines.NNavy.NAVAL_COMBAT_AIR_CONVOY_TARGET_SCORE = 1.0
	NDefines.NNavy.NAVAL_COMBAT_AIR_STRENGTH_TARGET_SCORE = 5                         -- how much score factor from low health (scales between 0->this number)
	NDefines.NNavy.NAVAL_COMBAT_AIR_LOW_AA_TARGET_SCORE = 5                           -- how much score factor from low AA guns (scales between 0->this number)

	NDefines.NNavy.WAR_SCORE_GAIN_FOR_SUNK_SHIP_MANPOWER_FACTOR = 0.01                        -- war score gained for every manpower killed when sinking a ship
	NDefines.NNavy.WAR_SCORE_GAIN_FOR_SUNK_SHIP_PRODUCTION_COST_FACTOR = 0.01   --0.04                       -- war score gained for every IC of the sunk ship
	NDefines.NNavy.WAR_SCORE_GAIN_FOR_SUNK_CONVOY = 2  --10                       -- war score gained for every sunk convoy
	NDefines.NNavy.WAR_SCORE_DECAY_FOR_BUILT_CONVOY = 1  --5                         -- war score deducted when convoy-raided enemy produces one new convoy

	NDefines.NNavy.UNDERWAY_REPLENISHMENT_RANGE_FACTOR = 0.42 -- bonus factor applied to task force's range when underway replenishment is activated (e.g. 0.2 means +20%) -- 0.42 base game
	NDefines.NNavy.UNDERWAY_REPLENISHMENT_CONVOY_COST_PER_FUEL = 0.42 -- Cost in convoys for underway replenishment multiplied by max daily fuel consumption (rounded up) -- 0.42 base game

	-- NTrade Defines
	NDefines.NTrade.DISTANCE_TRADE_FACTOR = -0.03 -- -0.02
	NDefines.NTrade.BASE_LAND_TRADE_RANGE = 350 -- 1000
	NDefines.NTrade.ANTI_MONOPOLY_TRADE_FACTOR_THRESHOLD = 0.5 -- 0.5
	NDefines.NAI.SEA_PATH_LENGTH_SCORE_BASE = -10 -- Reduced from -30 to -10
	NDefines.NAI.NUM_RESOURCES_TO_ALLOW_MINOR_EMBARGO = 100
	NDefines.NAI.EMBARGO_WORLD_TENSION_THREAT_DIVISOR = 3.0

	-- NAI Defines
	-- BAI fix test
	NDefines.NAI.ASSIGN_FRONT_TERRAIN_ATTACK_FACTOR = 6.0                   -- Importance of unit's terrain adjusted attack stat when assigning to a front
	NDefines.NAI.ASSIGN_FRONT_TERRAIN_DEFENSE_FACTOR = 2.0                  -- Importance of unit's terrain adjusted defense stat when assigning to a front
	NDefines.NAI.ASSIGN_FRONT_TERRAIN_MOVEMENT_FACTOR = 3.0                 -- Importance of unit's terrain adjusted movement stat when assigning to a front
	NDefines.NAI.ASSIGN_DEFENSE_TERRAIN_ATTACK_FACTOR = 0.5                 -- Importance of unit's terrain adjusted attack stat when assigning to an area defense order
	NDefines.NAI.ASSIGN_DEFENSE_TERRAIN_DEFENSE_FACTOR = 4.0               -- Importance of unit's terrain adjusted defense stat when assigning to an area defense order
	NDefines.NAI.ASSIGN_DEFENSE_TERRAIN_MOVEMENT_FACTOR = 0.5               -- Importance of unit's terrain adjusted movement stat when assigning to an area defense order
	NDefines.NAI.ASSIGN_MOUNTAINEERS_TO_MOUNTAINS = 10.0                    -- factor for assigning mountaineer divisions to fronts with mountains (proportional to how much of that terrain type)
	NDefines.NAI.ASSIGN_TANKS_TO_MOUNTAINS = -26.0                           -- factor for assigning tank divisions to fronts with mountains (proportional to how much of that terrain type)
	NDefines.NAI.ASSIGN_TANKS_TO_JUNGLE = -6.0                              -- factor for assigning tank divisions to fronts with jungle (proportional to how much of that terrain type)
	NDefines.NAI.UNIT_ASSIGNMENT_TERRAIN_IMPORTANCE = 10.0                  -- Terrain score for units are multiplied by this when the AI is deciding which front they should be assigned to
	NDefines.NAI.MAX_FACTORY_TO_TRADE_FOR_FUEL_IN_PEACE = 0.45 -- percentage of factories traded away during peace time
	NDefines.NAI.BASE_RELUCTANCE = 40 -- 20
	NDefines.NAI.DIPLOMATIC_ACTION_PROPOSE_SCORE = 25 -- 50
	NDefines.NAI.DILPOMATIC_ACTION_DECLARE_WAR_WARGOAL_BASE = 75 -- 50
	NDefines.NAI.DIPLOMACY_IMPROVE_RELATION_COST_FACTOR = 10.0 -- 5
	NDefines.NAI.DIPLOMACY_ACCEPT_VOLUNTEERS_BASE = 75 -- 50
	NDefines.NAI.DIPLOMACY_ACCEPT_ATTACHE_BASE = 75 -- 50
	NDefines.NAI.MIN_DELIVERED_TRADE_FRACTION = 0.6 -- 0.8
	NDefines.NAI.PRODUCTION_UNAVAILABLE_RESORCE_FACTORY_FACTOR = 0.4 -- 0.75
	NDefines.NAI.MAX_VOLUNTEER_ARMY_FRACTION = 0.5			-- 0.25
	NDefines.NAI.DEPLOY_MIN_EQUIPMENT_WAR_FACTOR = 0.60		-- 0.90
	NDefines.NAI.CALL_ALLY_BASE_DESIRE = 25					-- 20
	NDefines.NAI.CALL_ALLY_DEMOCRATIC_DESIRE = 25			-- 50
	NDefines.NAI.CALL_ALLY_FASCIST_DESIRE = 25				-- -10
	NDefines.NAI.CALL_ALLY_COMMUNIST_DESIRE = 25				-- 75
	NDefines.NAI.JOIN_ALLY_BASE_DESIRE = 25					-- 20
	NDefines.NAI.JOIN_ALLY_DEMOCRATIC_DESIRE = 25			-- 50
	NDefines.NAI.JOIN_ALLY_FASCIST_DESIRE = 25				-- -10
	NDefines.NAI.JOIN_ALLY_COMMUNIST_DESIRE = 25				-- 75
	NDefines.NAI.LENDLEASE_FRACTION_OF_PRODUCTION = 0.6		-- 0.5
	NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_LOW = 0.85		-- 0.85
	NDefines.NAI.PLAN_FRONTUNIT_DISTANCE_FACTOR = 20			-- 10
	NDefines.NAI.PLAN_ATTACK_DEPTH_FACTOR = 1.2				-- 0.5
	NDefines.NAI.PLAN_STEP_COST_LIMIT = 15					-- 11
	NDefines.NAI.PLAN_FRONT_SECTION_MAX_LENGTH = 9			-- 18
	NDefines.NAI.PLAN_FRONT_SECTION_MIN_LENGTH = 4			-- 10
	NDefines.NAI.PLAN_MIN_SIZE_FOR_FALLBACK = 1000			-- 50
	NDefines.NAI.SEND_VOLUNTEER_EVAL_BASE_DISTANCE = 100.0  	-- 175
	NDefines.NAI.SEND_VOLUNTEER_EVAL_CONTAINMENT_FACTOR = 0.05 -- 0.1
	NDefines.NAI.MAIN_ENEMY_FRONT_IMPORTANCE = 2.5			-- 4
	NDefines.NAI.EASY_TARGET_FRONT_IMPORTANCE = 1.3			-- 7.5
	NDefines.NAI.MICRO_POCKET_SIZE = 3						-- 4
	NDefines.NAI.FRONT_REASSIGN_DISTANCE = 40.0				-- 120
	NDefines.NAI.OLD_FRONT_IMPORTANCE_FACTOR = 1.80			-- 1.5
	NDefines.NAI.FRONT_TERRAIN_DEFENSE_FACTOR = 3.75			-- 3.75
	NDefines.NAI.FRONT_TERRAIN_ATTACK_FACTOR = 8.0			-- 5
	NDefines.NAI.BASE_DISTANCE_TO_CARE = 200.0				-- 600
	NDefines.NAI.MIN_FORCE_RATIO_TO_PROTECT = 1.5			-- 0.5
	NDefines.NAI.STR_UNIT_STRONG = 0.85						-- 0.75
	NDefines.NAI.MIN_STATE_VALUE_TO_PROTECT = 3.5			-- 7.5
	NDefines.NAI.FASCISTS_BEFRIEND_COMMUNISTS = -50
	NDefines.NAI.FASCISTS_ALLY_FASCISTS = -25
	NDefines.NAI.FASCISTS_ALLY_DEMOCRACIES = -75
	NDefines.NAI.FASCISTS_ANTAGONIZE_DEMOCRACIES = 75
	NDefines.NAI.DEMOCRACIES_BEFRIEND_COMMUNISTS = -75
	NDefines.NAI.DEMOCRACIES_ALLY_DEMOCRACIES = -25
	NDefines.NAI.DEMOCRACIES_ALLY_COMMUNISTS = -100
	NDefines.NAI.DEMOCRACIES_ANTAGONIZE_FASCISTS = 20
	NDefines.NAI.DEMOCRACIES_ANTAGONIZE_COMMUNISTS = 50
	NDefines.NAI.COMMUNISTS_ALLY_COMMUNISTS = -25
	NDefines.NAI.COMMUNISTS_ANTAGONIZE_FASCISTS = 25
	NDefines.NAI.COMMUNISTS_ANTAGONIZE_DEMOCRACIES = 30
	NDefines.NAI.COMMUNISTS_ANTAGONIZE_COMMUNISTS = -50
	NDefines.NAI.CALL_ALLY_WT_LIMIT = 0.6 -- 0.8
	NDefines.NAI.REFIT_SHIP_RELUCTANCE = 56						-- 28
	NDefines.NAI.REFIT_SHIP_PERCENTAGE_OF_FORCES = 0.25				-- 0.1
	NDefines.NAI.UPGRADE_DIVISION_RELUCTANCE = 30					-- 7
	NDefines.NAI.UPGRADE_PERCENTAGE_OF_FORCES = 0.15				-- 0.1
	NDefines.NAI.STRATEGIC_BOMBING_DEFENCE_IMPORTANCE = 500.0
	NDefines.NAI.ENEMY_NAVY_STRENGTH_DONT_BOTHER = 1.5				-- 2.5
	NDefines.NAI.STATE_CONTROL_FOR_AREA_DEFENSE = 0.2				-- 0.4
	NDefines.NAI.NAVAL_MISSION_INVASION_BASE = 5000					-- 1000
	NDefines.NAI.SCARY_LEVEL_AVERAGE_DEFENSE = -0.6					-- -0.7
	NDefines.NAI.ATTACK_HEAVILY_DEFENDED_LIMIT = 1.2					-- 0.45
	NDefines.NAI.HOUR_BAD_COMBAT_REEVALUATE = 42						-- 100
	NDefines.NAI.AI_FRONT_MOVEMENT_FACTOR_FOR_READY = 0.15 --default 0.25
	NDefines.NAI.PLAN_VALUE_TO_EXECUTE = -0.2 --default -0.5
	NDefines.NAI.REQUEST_LEND_LEASE_CONTAINS_VALUE = 60				-- 100
	NDefines.NAI.REQUEST_LEND_LEASE_STOCKPILE_RATIO_LAND = 0.5			-- 0.1
	NDefines.NAI.REQUEST_LEND_LEASE_PRODUCTION_DAYS_LAND = 500			-- 28
	NDefines.NAI.REQUEST_LEND_LEASE_STOCKPILE_RATIO_AIR = 0.3			-- 0.03
	NDefines.NAI.REQUEST_LEND_LEASE_PRODUCTION_DAYS_AIR = 28			-- 10
	NDefines.NAI.REQUEST_LEND_LEASE_STOCKPILE_RATIO_NAVAL = 0.3			-- 0.1
	NDefines.NAI.INVASION_DISTANCE_RANDOMNESS = 200					-- 300
	NDefines.NAI.NAVAL_TRANSFER_AIR_IMPORTANCE = 1.0				-- 0
	NDefines.NAI.NAVAL_STRIKE_PLANES_PER_SHIP = 30 					--20 reduced by 50% to reduce the AI spamming planes over naval battles
	NDefines.NAI.FOCUS_TREE_CONTINUE_FACTOR = 1		-- Factor for score of how likely the AI is to keep going down a focus tree rather than starting a new path.

	NDefines.NAI.NAVY_PREFERED_MAX_SIZE = 999						-- 20 #Now AI like big fleet
	NDefines.NAI.MAX_DISTANCE_NAVAL_INVASION = 400.0				-- 200.0
	NDefines.NAI.INVASION_COASTAL_PROVS_PER_ORDER = 8				-- 12
	NDefines.NAI.NAVAL_COMBAT_AIR_IMPORTANCE = 24.0					-- 12.0
	NDefines.NAI.TRANSPORTS_PER_PARATROOPER = 10					-- 20

	NDefines.NAI.NAVAL_FIGHTERS_PER_PLANE = 2					-- 1.1
	NDefines.NAI.NAVAL_STRIKE_PLANES_PER_ARMY = 1					-- 0
	NDefines.NAI.MINES_SWEEPING_PLANES_PER_MAX_MINES = 10				-- 150
	NDefines.NAI.MINES_PLANTING_PLANES_PER_MAX_DESIRE = 5				-- 100

	NDefines.NAI.LAND_COMBAT_FIGHTERS_PER_PLANE = 1.2				-- 1.1
	NDefines.NAI.LAND_COMBAT_CAS_PER_ENEMY_ARMY = 20				-- 20
	NDefines.NAI.LAND_COMBAT_CAS_PER_COMBAT = 50					-- 150

	NDefines.NAI.STR_BOMB_PLANES_PER_CIV_FACTORY = 25				-- 20
	NDefines.NAI.STR_BOMB_PLANES_PER_MIL_FACTORY = 30				-- 25
	NDefines.NAI.STR_BOMB_PLANES_PER_NAV_FACTORY = 5				-- 15
	NDefines.NAI.RECON_PLANES_NAVAL = 5						-- 50
	NDefines.NAI.RECON_PLANES_LAND_COMBAT = 5					-- 25
	NDefines.NAI.RECON_PLANES_STRATEGIC = 5						-- 50
	NDefines.NAI.MAX_CARRIER_OVERFILL = 1.50					-- 2.25 -- Reduced to 1.5 to hopefully stop the AI from overcrowding the Carriers
	NDefines.NAI.CARRIER_TASKFORCE_MAX_CARRIER_COUNT = 3				-- 4
	NDefines.NAI.CAPITAL_TASKFORCE_MAX_CAPITAL_COUNT = 16				-- 12
	NDefines.NAI.SCREEN_TASKFORCE_MAX_SHIP_COUNT = 2				-- 12
	NDefines.NAI.SUB_TASKFORCE_MAX_SHIP_COUNT = 3					-- 16
	NDefines.NAI.MIN_CAPITALS_FOR_CARRIER_TASKFORCE = 4				-- 10
	NDefines.NAI.CAPITALS_TO_CARRIER_RATIO = 4					-- 1.5
	NDefines.NAI.SCREENS_TO_CAPITAL_RATIO = 2					-- 4.0
	NDefines.NAI.FRONT_EVAL_UNIT_ACCURACY = 0.85					-- 0.7
	NDefines.NAI.HIGH_PRIO_NAVAL_MISSION_SCORES = {
		0, -- HOLD (consumes fuel HOLD_MISSION_MOVEMENT_COST fuel while moving)
		100000, -- PATROL
		5000, -- STRIKE FORCE
		10000, -- CONVOY RAIDING
		1000, -- CONVOY ESCORT
		-1, -- MINES PLANTING
		300, -- MINES SWEEPING
		100, -- TRAIN
		0, -- RESERVE_FLEET
		1000, -- NAVAL INVASION SUPPORT
	}
	NDefines.NAI.MAX_MISSION_PER_TASKFORCE = {
		0, -- HOLD (consumes fuel HOLD_MISSION_MOVEMENT_COST fuel while moving)
		3.5, -- PATROL
		1, -- STRIKE FORCE
		3, -- CONVOY RAIDING
		4, -- CONVOY ESCORT
		1, -- MINES PLANTING
		1, -- MINES SWEEPING
		1, -- TRAIN
		0, -- RESERVE_FLEET
		4, -- NAVAL INVASION SUPPORT
	}
	NDefines.NAI.LAND_COMBAT_BOMBERS_PER_LAND_FORT_LEVEL = 7			-- 15
	NDefines.NAI.LAND_COMBAT_BOMBERS_PER_COASTAL_FORT_LEVEL = 5		-- 10
	NDefines.NAI.AIR_SCORE_DISTANCE_IMPACT = 0.4
	NDefines.NAI.PLAN_ACTIVATION_SUPERIORITY_AGGRO = 0.1				-- 1.0
	NDefines.NAI.WAIT_YEARS_BEFORE_FREER_BUILDING = 0				-- 3 is vanilla, updated this from 8 to 20 for more AI production control
	NDefines.NAI.UPGRADES_DEFICIT_LIMIT_DAYS = 40				 	-- 50
	NDefines.NAI.FUEL_CONSUMPTION_MULT_FOR_FUEL_SAVING_MODE = 1.0			-- fuel consumptions will be limited by this ratio in fuel saving mode
	NDefines.NAI.FUEL_CONSUMPTION_MULT_REGULAR_FUEL_MODE = 2.0				-- fuel consumptions will be limited by this ratio in regular fuel mode
	NDefines.NAI.FUEL_CONSUMPTION_MULT_AGRESSIVE_FUEL_MODE = 5.0				-- fuel consumptions will be limited by this ratio in aggressive fuel usage mode
	NDefines.NAI.AIR_SUPERIORITY_FACTOR = 2.7
	NDefines.NAI.DAYS_FUEL_REMAINING_TO_ENTER_FUEL_SAVING_MODE = 60				-- countries will enter fuel saving mode if they will be out of fuel in this number of days and their fuel ratio is below next define
	NDefines.NAI.DAYS_FUEL_REMAINING_TO_ENTER_FUEL_SAVING_MODE_FUEL_RATIO = 0.25
	NDefines.NAI.FUEL_RATIO_TO_EXIST_FUEL_SAVING_MODE = 0.30 					-- countries will exit fuel saving mode if they have more fuel ratio than this
	NDefines.NAI.LAND_COMBAT_CAS_WINGS_PER_ENEMY_ARMY_LIMIT = 5	-- Limit of CAS wings requested by enemy armies
	NDefines.NAI.LAND_COMBAT_CAS_PER_ENEMY_ARMY = 20				-- Amount of CAS planes requested per enemy army

	NDefines.NAI.LAND_COMBAT_CAS_PER_COMBAT = 65
	NDefines.NAI.LAND_COMBAT_FIGHTERS_PER_PLANE = 1.3
	NDefines.NAI.MIN_WANTED_MAX_FUEL = 25
	NDefines.NAI.STR_BOMB_IMPORTANCE_SCALE = 2.5 -- Reduced from 5 to 2.5/originally was 10 but caused issues with the AI being unable to use their planes on missions
	NDefines.NAI.LAND_COMBAT_INTERCEPT_PER_PLANE = 1

	NDefines.NAI.TRADEABLE_FACTORIES_FRACTION = 0.80 -- Updated from 0.80
	NDefines.NAI.DIPLOMACY_CREATE_FACTION_FACTOR = 1.25 --0.75 in Vanilla		-- Factor for AI desire to create a new faction. Val < 1.0 makes it less likely to create than to join.
	NDefines.NAI.DIPLOMACY_FACTION_WRONG_IDEOLOGY_PENALTY = 60 -- AI penalty for diplomatic faction acitons between nations of different ideologies
	NDefines.NAI.DIPLOMACY_FACTION_SAME_IDEOLOGY_MAJOR = 10 -- AI bonus acceptance when being asked about faction is a major of the same ideology
	NDefines.NAI.DIPLOMACY_FACTION_NEUTRALITY_PENALTY = 0 --50 in Vanilla (non-aligned arean't necessarily 'neutral' in MD) -- Neutral nations have a separate penalty, not wanting to get involved at all, rather than caring much about the difference in ideology
	NDefines.NAI.DIPLOMACY_FACTION_GLOBAL_TENSION_FACTOR = 0.2 -- How much the AI takes global tension into account when considering faction actions
	NDefines.NAI.DIPLOMACY_FACTION_WAR_RELUCTANCE = -60 --50 in Vanilla	-- Penalty to desire to enter a faction with a country that we are not fighting wars together with.
	NDefines.NAI.DIPLOMACY_FACTION_TAKE_OVER_RELUCTANCE_VERSUS_HUMAN = 2.0	-- Multiplier penalty for how much stronger than a human faction member an AI country must be to choose to assume faction leadership.
	NDefines.NAI.DIPLOMACY_SCARED_MINOR_EXTRA_RELUCTANCE = -60 --50 in Vanilla -- extra reluctance to join stuff as scared minor
	NDefines.NAI.DIPLOMACY_FACTION_PLAYER_JOIN = 0 --20 in Vanilla			-- Bonus for human players asking to join a faction.
	NDefines.NAI.DIPLOMACY_FACTION_MAJOR_AT_WAR = 1000.0	-- Factor that will be multiplied with the surrender level in the desire to offer to the other ai to join a faction
	NDefines.NAI.DIPLOMACY_FACTION_SURRENDER_LEVEL = 20 	-- How much the recipient nation losing matters for joining a faction
	NDefines.NAI.DIPLO_PREFER_OTHER_FACTION = -200			-- The country has yet to ask some other faction it would prefer to be a part of.
	NDefines.NAI.JOIN_FACTION_BOTH_LOSING = -300			-- Desire to be in a faction when both we and htey are in losing wars
	NDefines.NAI.DIFFERENT_FACTION_THREAT = 30			-- Threat caused by not being in the same faction
	NDefines.NAI.TENSION_MIN_FOR_GUARANTEE_VS_MINOR = 20 --10 in Vanilla -- for non faction people AI will not consider you worth guaranteeing below this
	NDefines.NAI.DIPLOMACY_FACTION_WAR_WANTS_HELP = 50	-- Desire to send to nations to join a faction if you are at war
	NDefines.NAI.DIPLOMACY_FACTION_CIVILWAR_WANTS_HELP = -50
	NDefines.NAI.FACTION_UNSTABLE_ACCEPTANCE = -100
	NDefines.NAI.DIPLOMACY_AT_WAR_WITH_ALLY_RELUCTANCE = -1000
	NDefines.NAI.DIPLOMACY_FACTION_JOIN_COUP_INITIATOR_BONUS = 70	-- If a country initiated coup on an another country, civil war revolter is more likely to join initiator's faction
	NDefines.NAI.DEMOCRATIC_AI_FACTION_KICKING_PLAYER_THREAT_DIFFERENCE = 6.0 -- World threat generation difference needed to kick a player from a democratic faction
	NDefines.NAI.GENERATE_WARGOAL_ANTAGONIZE_SCALE = 0.10    -- works to scale the AIs antagonize value vs the threat baseline for when it should act on existing claims: threat used for baseline is min_threat - antagonize * scale
	NDefines.NAI.LAND_COMBAT_OUR_ARMIES_AIR_IMPORTANCE = 100
	NDefines.NAI.LAND_COMBAT_OUR_COMBATS_AIR_IMPORTANCE = 200		-- Strategic importance of our armies in the combats
	NDefines.NAI.LAND_COMBAT_FRIEND_ARMIES_AIR_IMPORTANCE = 25
	NDefines.NAI.NUM_AI_MESSAGES = 300
	NDefines.NAI.AIR_ACTUAL_FUEL_USAGE_WEIGHT_ON_OIL_REQUEST = 0.05
	NDefines.NAI.LAND_DEFENSE_AIR_SUPERIORITY_IMPORTANCE = 1.5
	NDefines.NAI.LAND_COMBAT_AIR_SUPERIORITY_IMPORTANCE = 1.5
	NDefines.NAI.LAND_DEFENSE_FIGHERS_PER_PLANE = 1.8
	NDefines.NAI.LAND_COMBAT_FIGHTERS_PER_PLANE = 1.3
	NDefines.NAI.MAX_AIR_REGIONS_TO_CARE_ABOUT = 7
	NDefines.NAI.AI_FRACTION_OF_FIGHTERS_RESERVED_FOR_INTERCEPTION = 0.10
	NDefines.NAI.WANTED_LAND_PLANES_PER_DIVISION = 30
	NDefines.NAI.BUILDING_TARGETS_BUILDING_PRIORITIES = {				-- buildings in order of priority when considering building targets strategies. First has the greatest priority, omitted has the lowest. NOTE: not all buildings are supported by building targets strategies.
		'fossil_powerplant', 'industrial_complex', 'internet_station', 'synthetic_refinery', 'nuclear_reactor', 'fuel_silo', 'offices', 'infrastructure', 'agriculture_district', 'arms_factory'
	}
	NDefines.NAI.MAX_FUEL_CONSUMPTION_RATIO_FOR_AIR_TRAINING = 0.2
	NDefines.NAI.MAX_FUEL_CONSUMPTION_RATIO_FOR_NAVY_TRAINING = 0.2
	NDefines.NAI.NUM_SILOS_PER_CIVILIAN_FACTORIES = 0.03		-- ai will try to build a silo per this ratio of civ factories
	NDefines.NAI.NUM_SILOS_PER_MILITARY_FACTORIES = 0.03		-- ai will try to build a silo per this ratio of mil factories
	NDefines.NAI.NUM_SILOS_PER_DOCKYARDS = 0.03

	-- AI Research Stuff
	NDefines.NAI.RESEARCH_WEIGHT_TRUNCATION_THRESHOLD = 0.5 -- Reduced this from 0.75
	NDefines.NAI.RESEARCH_DAYS_BETWEEN_WEIGHT_UPDATE = 20 -- 7
	NDefines.NAI.MAX_AHEAD_RESEARCH_PENALTY = 4 -- 2 --Buffing to double so it penalizes more
	NDefines.NAI.RESEARCH_BASE_DAYS = 350 -- 60
	NDefines.NAI.RESEARCH_YEARS_BEHIND_FACTOR = 0.30 -- Try to stay on the cutting edge where possible
	NDefines.NAI.RESEARCH_NEEDS_FACTOR = 0.05
	NDefines.NAI.RESEARCH_LENGTH_FACTOR = 2.5

	-- Peace deal AI stuff
	NDefines.NAI.PEACE_BID_FOLD_AGAINST_PLAYER_CHANCE = 0.7			-- 0.5 in vanilla
	NDefines.NAI.PEACE_BID_FOLD_AGAINST_AI_CHANCE_UNCONTROLLED = 0.60	-- 0.40 in vanilla
	NDefines.NAI.PEACE_BID_FOLD_AGAINST_LIBERATE_CONTEST = 1.0			-- 1.0 in vanilla
	NDefines.NAI.PEACE_BID_FOLD_MINOR_VS_MAJOR = 2.0					-- 1.0 in vanilla
	NDefines.NAI.PEACE_AI_GROUP_PEACE_ACTIONS = false					-- Whether AI should group peace actions or greedily just select the most-desired peace actions
	NDefines.NAI.PEACE_AI_EVALUATE_FOR_SUBJECTS = true					-- Whether AI should include subjects when evaluating giving states to other winners (may affect performance on new conference turn)
	NDefines.NAI.PEACE_AI_EVALUATE_FOR_ALLIES = true					-- Whether AI should include allies when evaluating giving states to other winners (may affect performance on new conference turn)
	NDefines.NAI.PEACE_AI_EVALUATE_FOR_NON_ALLIES = false				-- Whether AI should include non-allies (not in same faction) when evaluating giving states to other winners (may affect performance on new conference turn)
	NDefines.NAI.PEACE_AI_EVALUATE_OTHER_IF_CORE = true				-- Whether AI should evaluate giving states to other winners if state is their core (may affect performance on new conference turn)
	NDefines.NAI.PEACE_AI_EVALUATE_OTHER_IF_CLAIM = true				-- Whether AI should evaluate giving states to other winners if they have a claim on the state (may affect performance on new conference turn)
	NDefines.NAI.PEACE_AI_EVALUATE_OTHER_ALWAYS = false				-- Whether AI should always evaluate giving states to other winners (!!! may heavily affect performance on new conference turn for large peace conferences !!!)
	NDefines.NAI.LAND_DEFENSE_SAM_MISSILE_IMPORTANCE_FACTOR = 0.6 -- Importance of SAMs in strat region Higher value = more -- 0.2
	NDefines.NAI.LAND_COMBAT_MISSILE_IMPORTANCE_FACTOR = 1.75 -- Importance of missiles for regions of strat importance. Higher = more -- 1.5
	NDefines.NAI.LAND_DEFENSE_AA_IMPORTANCE_FACTOR = 1.0 -- Factor of AA on stat importance

	-- NOperatives Defines
	NDefines.NOperatives.AGENCY_AI_BASE_NUM_FACTORIES = 25.0 -- (We do not need factories aside from establishment)
	NDefines.NOperatives.AGENCY_AI_PER_UPGRADE_FACTORIES = 10.0 -- 6 in Vanilla
	NDefines.NOperatives.AGENCY_UPGRADE_DAYS = 100 -- 20 in Vanilla
	NDefines.NResistance.GARRISON_MANPOWER_LOST_BY_ATTACK = 0.02 	-- Ratio of manpower lost by garrison at each attack on garrison (this number will be reduced by the hardness of garrison template)
	NDefines.NResistance.GARRISON_EQUIPMENT_LOST_BY_ATTACK = 0.04 	-- Ratio of equipment lost by garrison at each attack on garrison (this number will be reduced by the hardness of garrison template)
	NDefines.NResistance.RESISTANCE_GROWTH_BASE = 0.1 --base resistance growth
	NDefines.NResistance.COMPLIANCE_GROWTH_BASE = 0.1 --base compliance gain
	NDefines.NOperatives.BASE_COUNTER_INTELLIGENCE_RATING = 1.0 -- Set to 1 to prevent weird negatives
	NDefines.NOperatives.AGENCY_UPGRADE_PER_OPERATIVE_SLOT = 6 -- Reduced from vanilla
	NDefines.NOperatives.BECOME_SPYMASTER_MIN_UPGRADES = 8 -- Boosted from 3

	NDefines.NOperatives.MAX_OPERATIVE_SLOT_FROM_AGENCY_UPGRADES = 4					-- (normaly 1) max operative slots gained from upgrades
	NDefines.NOperatives.INTEL_NETWORK_GAIN_RATE_ON_WRONG_CONTROLLER = -9.9				-- (normaly -10.0) Amount of network strength lost in a state when it does not have the right controller anymore
	NDefines.NOperatives.INTEL_NETWORK_GAIN_RATE_ON_OUT_OF_RANGE = -1.57				-- (normaly -1.75) Amount of network strength lost in a state that has the right controller but is out of range of any operative
	--may come back to below, but makes much more of a diffrence than i thaught
	--NDefines.NOperatives.INTEL_NETWORK_MIN_VP_TO_TARGET = 10,					-- (normaly 15) The minimum value of the highest VP in a state to consider the state as a valid target to start building an intel network
	NDefines.NOperatives.INTEL_NETWORK_OPERATIVE_GAIN_STACKING_FACTOR = 0.6				-- (normaly 0.5) When multiple operative are present in the same location, this factor is applied for each operative with a lower gain than the max. So if operatives have the gain [ 3, 1, 2 ] in the same location, it is sorted to [ 1, 2, 3 ] then converted to [ 1*D^2, 2*D^1, 3 ], with D being this define, so if D=0.5 we have [ 0.25, 1, 3 ] and the final gain from operative at this location will be 4.25. Putting this define to 0 is equivalent to considering the maximum value only.

	NDefines.NOperatives.QUIET_INTEL_NETWORK_DAILY_XP_GAIN = 0.112						-- (normaly 0.0)

	-- used for calculating how many operatives will a spy master gain from its faction members
	-- first number in every now is number of operatives gained
	-- second number is total factory needed (mil and civ) for giving previous ratio
	-- NORMAL BELOW
	--0.0, 		0.0, 	-- 0 operative for [0, 10)
	--0.25,  	10.0,	-- 0.25 operative for [10, 50)
	--0.5, 		50.0,	-- 0.5 operative for >= 50

	NDefines.NOperatives.OPERATIVE_SLOTS_FROM_FACTION_MEMBERS_FOR_SPY_MASTER = {
		0.0, 	0.0, -- 0 operative for [0, 5)
		0.1,  	5.0, -- 0.1 operative for [5, 10)
		0.25, 	10.0, -- 0.25 operative for [10, 25)
		0.5,  	25.0, -- 0.5 operative for [25, 50)
		0.75,  	50.0, -- 0.75 operative for [50, 75)
		1.0,  	75.0, -- 1 operative for [75, 100)
		1.5,  	100.0, -- 1.5 operative for >= 100
	}

	NDefines.NOperatives.OPERATIVE_BASE_INTEL_NETWORK_GAIN = 0.32				-- (normaly 0.4) Base amount of network strength gain per day provided by an operative
	NDefines.NOperatives.COUNTER_INTELLIGENCE_STACKING_FACTOR = 0.6								-- (normaly 0.5) Multiplier applied to each operative after the first one. So if we have the following counter intelligence rating values [ 0.1, 0.3, 0.2 ], the factor is applied twice for the lowest value and once for the 2nd lowest one as such : [ 0.3, 0.2 * D, 0.1 * D * D ] and then the result is summed up to give the final rating value

	NDefines.NOperatives.BOOST_IDEOLOGY_MAX_DRIFT_BY_OPERATIVE = 0.25			-- (normaly 0.25) the maximum drift an operative can cause, a negative value means no maximum
	NDefines.NOperatives.BOOST_IDEOLOGY_DRIFT_STACKING_FACTOR = 0.65				-- (Normaly 0.5) multiplied to the drift of an operative for each operative after the first one, with the greatest drift. So if we have the following drift values [ 0.1, 0.3, 0.2 ], the factor is applied twice for the lowest value and once for the 2nd lowest one as such : [ 0.3, 0.2 * D, 0.1 * D * D ] and then the result is summed up to give the final drift value.
	NDefines.NOperatives.BOOST_IDEOLOGY_DAILY_XP_GAIN = 0.35						-- (normaly 0.274)
	NDefines.NOperatives.OPERATIVE_BASE_BOOST_IDEOLOGY = 0.15					-- (normaly 0.1) Base amount of daily ideology drift provoked by an operative
	NDefines.NOperatives.OPERATIVE_BASE_PROPAGANDA_POWER = 0.0004				-- (normaly 0.0005) Base amount of daily war support and stability change when an operative is assigned to propaganda
	NDefines.NOperatives.PROPAGANDA_OPERATIVE_STACKING_FACTOR = 0.6				-- (normaly 0.5) Multiplied to the Stability/WarSupport drift values of each operative after the one with the greatest values. The process is done separatly for Stability and WarSupport
				--no change made, but kept in case i change my mind
			--NDefines.NOperatives.PROPAGANDA_COUNTRY_STACKING_FACTOR = 0.5,			-- Multiplied to the Stability/WarSupport drift values of each country after the one with the greatest values. The process is done separatly for Stability and WarSupport
	NDefines.NOperatives.PROPAGANDA_DAILY_XP_GAIN = 0.420						-- (normaly 0.35
				--no change made, but kept in case i change my mind
			--NDefines.NOperatives.OPERATIVE_BASE_ROOT_OUT_RESISTANCE_EFFICIENCY = 1.0,	-- The base efficiency of an operative at the RootOutResistance mission (this is a percentage, 1.0 == 100%)
	NDefines.NOperatives.OPERATIVE_BASE_ROOT_OUT_RESISTANCE_EFFICIENCY = 0.9	-- (normaly 1.0) The base efficiency of an operative at the RootOutResistance mission (this is a percentage, 1.0 == 100%)
	NDefines.NOperatives.ROOT_OUT_RESISTANCE_STACKING_FACTOR = 0.6				-- (normaly 0.5) Multiplied to each operative efficiency after the first one
	NDefines.NOperatives.ROOT_OUT_RESISTANCE_RANGE_STEP_FACTOR = 0.6			-- (normaly 0.5) Multiplied to the summed up efficiency from all operative operating in a same state to determine the efficiency in neighboring states
	NDefines.NOperatives.ROOT_OUT_RESISTANCE_DAILY_XP_GAIN = 0.08				-- (normaly 0.068)
	NDefines.NOperatives.OPERATIVE_BASE_CONTROL_TRADE_DRIFT = 0.4				-- (normaly 0.5) The base daily drift in trade influence caused by an operative
	NDefines.NOperatives.CONTROL_TRADE_STACKING_FACTOR = 0.6					-- (normaly 0.6) Multiplied to the drift of each operative after the first one
	NDefines.NOperatives.CONTROL_TRADE_DAILY_XP_GAIN = 0.164					-- (normaly 0.137)

	NDefines.NOperatives.DIPLOMATIC_PRESSURE_OPERATIVE_STACKING_FACTOR = 0.6	-- (normaly 0.5) The diminishing return factor to apply to operative working for the same faction after the first one. Operatives operating for a same faction are ranked by their efficiency and their opinion and tension drift are individually applyied a stacking factor like so: DRIFT * STACKING_FACTOR^RANK where RANK is a value from 0 to the number of operative -1 where the opperative with the highest drift value has rank 0
	NDefines.NOperatives.DIPLOMATIC_PRESSURE_DAILY_XP_GAIN = 0.164				-- (Normaly 0.137)
	NDefines.NOperatives.MAX_RECRUITED_OPERATIVES = 10							-- (Normaly 10)
	NDefines.NOperatives.OPERATION_COMPLETION_XP = 24							-- (normaly 18)
	NDefines.NOperatives.ON_CAPTURE_COUNTERINTELLIGENCE_OPERATIVE_XP_GAIN = 120	-- (normaly 100) Xp gain when an enemy operative is captured in the country the operative is assigned to counter intelligence to. Apply to a single randomly selected operative

	-- NIntel Defines
	NDefines.NIntel.RADAR_INTEL_STACKING_FACTOR = 0.6							-- (Normaly 0.5) Used when multiple radars cover the same province
	NDefines.NIntel.RECON_PLANE_INTEL_BASE = 0.024								-- (normaly 0.02) intel base amount for a strategic area per plane

	-- NChracter defines
	NDefines.NCharacter.OFFICER_CORP_ADVISOR_ENTRIES_IN_MENU = { "high_command", "theorist", "army_chief", "air_chief", "navy_chief" }
	NDefines.NCharacter.OFFICER_CORP_HIGH_COMMAND_SLOTS_IN_MENU = 3 --For Alert manager to count the number of High Command Slots in the UI

	-- NSupply Defines
	NDefines.NSupply.MAX_RAILWAY_LEVEL = 6 -- update railway texture as well, each frame corresponds to a level
	NDefines.NSupply.DEFAULT_STARTING_TRUCK_RATIO = 1 -- countries get this ratio of starting truck in their buffers compared to their need -- vanilla 1.5

	NDefines.NAI.SHIPS_PRODUCTION_BASE_COST = 15000					-- Used by the AI to normalize IC values when picking what ship to build.
	NDefines.NAI.NEEDED_NAVAL_FACTORIES_EXPENSIVE_SHIP_BONUS = 10    -- Amount of naval yards you need to get a bonus to building really expensive ships
	NDefines.NAI.PRODUCTION_MAX_PROGRESS_TO_SWITCH_NAVAL = 0.2		-- AI will not replace ships being built by newer types if progress is above this
	NDefines.NAI.AREA_DEFENSE_SETTING_AIRBASES = true

	NDefines.NAI.MIN_MAIN_SHIP_RATIO = 0.1                      -- if main ship ratio is below this, steal other ships.
	NDefines.NAI.MIN_SUPPORT_SHIP_RATIO = 0.7                   -- if support ship ratio is below this, steal other ships.
	NDefines.NAI.MIN_MAIN_SHIP_RATIO_TO_REINFORCE = 0.5         -- the main ships will be tried to reinforce this level.
	NDefines.NAI.MIN_SUPPORT_SHIP_RATIO_TO_REINFORCE = 0.9      -- the support ships will be tried to reinforce this level.
	NDefines.NAI.MIN_MAIN_SHIP_TO_SPARE = 0.7                   -- can only steal ships from a task force if their main ship ratio is above this.
	NDefines.NAI.MIN_SUPPORT_SHIP_TO_SPARE = 1.0                -- can only steal ships from a task force if their support ship ratio is above this.
	NDefines.NAI.MIN_MAIN_SHIP_RATIO_TO_MERGE = 1.0             -- try merge task force if main ship ratio is lower than this.
	NDefines.NAI.MAX_MAIN_SHIP_RATIO_TO_MERGE = 1.002           -- if resulting main ship ratio would be at most this, allow merging into this task force.
	NDefines.NAI.MAIN_SHIP_RATIO_TO_SPLIT = 3.6                 -- if main ship ratio in a task force is larger than this, split it. (If a carrier TF wants 4 carriers (see defines above), but it has more than [this * 4] carriers, then we try to split the TF.)
	NDefines.NAI.INDUSTRIAL_ORG_TRAIT_UNLOCK_RANDOMNESS = 3		-- AI will pick a random from N top traits when choosing a trait to unlock
	NDefines.NAI.INDUSTRIAL_ORG_POLICY_CHANGE_RANDOMNESS = 3	-- AI will pick a random from N top policies when choosing a policy to attach to an MIO
	NDefines.NAI.INDUSTRIAL_ORG_RESEARCH_ASSIGN_RANDOMNESS = 3	-- AI will pick a random from N top MIOs when choosing an MIO to assign to a research
	NDefines.NAI.INDUSTRIAL_ORG_PRODUCTION_ASSIGN_RANDOMNESS = 3-- AI will pick a random from N top MIOs when choosing an MIO to assign to a production line
	NDefines.NAI.INDUSTRIAL_ORG_POLICY_CHANGE_SCALE = 1.0		-- Policy change weight will be scaled by this value
	NDefines.NAI.INDUSTRIAL_ORG_TRAIT_RANK_FACTOR = 0.90		-- When precomputing weights, traits will affect the final score less the further down the tree they are, by this factor -- 0.8
	NDefines.NAI.INDUSTRIAL_ORG_RESEARCH_BONUS_FACTOR = 1.0		-- Research bonus will be multiplied by this factor when evaluating design teams

	NDefines.NAI.MIN_NAVAL_MISSION_PRIO_TO_ASSIGN = {  -- priorities for regions to get assigned to a mission
		0, -- HOLD (consumes fuel HOLD_MISSION_MOVEMENT_COST fuel while moving)
		200, -- PATROL
		1000, -- STRIKE FORCE
		400, -- CONVOY RAIDING
		200, -- CONVOY ESCORT
		100, -- MINES PLANTING
		100, -- MINES SWEEPING
		0, -- TRAIN
		100, -- RESERVE_FLEET
		200, -- NAVAL INVASION SUPPORT
	}

	-- NDefines.NAI.MIN_UNITS_FACTOR_FRONT_ORDER = 10.0
	NDefines.NIndustrialOrganisation.ASSIGN_DESIGN_TEAM_PP_COST_PER_DAY = 0.1					-- 0.1
	NDefines.NIndustrialOrganisation.ASSIGN_INDUSTRIAL_MANUFACTURER_PP_COST_PER_DAY = 0.0		-- 0
	NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP = 500					-- 700
	NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP_LEVEL_FACTOR = 50 			-- 100
	NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP_LEVEL_POW = 1.8			-- 1.8
	NDefines.NIndustrialOrganisation.UNLOCKED_TRAITS_PER_SIZE_UP = 1			-- 1
	NDefines.NIndustrialOrganisation.DESIGN_TEAM_CHANGE_XP_COST = 5				-- 5
	NDefines.NIndustrialOrganisation.FUNDS_FOR_RESEARCH_COMPLETION_PER_RESEARCH_COST = 500			-- 500
	NDefines.NIndustrialOrganisation.FUNDS_FOR_CREATING_EQUIPMENT_VARIANT = 0		-- 0
	NDefines.NIndustrialOrganisation.FUNDS_FROM_MANUFACTURER_PER_IC_PER_DAY = 0.1		-- 0.1
	NDefines.NIndustrialOrganisation.MAX_FUNDS_FROM_MANUFACTURER_PER_DAY = 100		-- 100
	NDefines.NIndustrialOrganisation.DESIGN_TEAM_RESEARCH_BONUS = 0.05				-- 0.05
	NDefines.NIndustrialOrganisation.ENABLE_TASK_CAPACITY = true					-- false
	NDefines.NIndustrialOrganisation.DEFAULT_INITIAL_TASK_CAPACITY = 5				-- 0
	NDefines.NIndustrialOrganisation.DEFAULT_INITIAL_POLICY_ATTACH_COST = 25		-- 25
	NDefines.NIndustrialOrganisation.DEFAULT_INITIAL_ATTACH_POLICY_COOLDOWN = 180	-- 180
	NDefines.NIndustrialOrganisation.LEGACY_COST_FACTOR_SCALE = 1.0					-- 1.0


	--Ndefines for Air Combat Testing
	-- NDefines.NAir.ENEMY_PASSING_THROUGH_PLANES_PER_BOMBER = 10        -- Amount of planes we assign to intercept enemies en-route to a location
    -- NDefines.NAir.ENEMY_PASSING_THROUGH_PLANES_PER_FIGHTER = 10       -- Amount of planes we assign to intercept enemies en-route to a location
    -- NDefines.NAir.ENEMY_PASSING_THROUGH_PLANES_PER_SUPPORT = 10        -- Amount of planes we assign to intercept enemies en-route to a location
	NDefines.NAir.INTERCEPTION_DISTANCE_SCALE = 150 -- 150 -- At this many pixels of path length, full interception efficiency is applied to air missions. Lerp from 0.
	NDefines.NAir.INTERCEPTION_DAMAGE_SCALE = 0.6 -- 0.3 -- Multiply the interception damage with this value. Works as a cap when interception distance is at maximum.