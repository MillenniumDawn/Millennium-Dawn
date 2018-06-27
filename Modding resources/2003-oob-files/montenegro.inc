
##############################
# Country definition for MTN #
##############################

province =
{ id       = 389
  naval_base = { size = 2 current_size = 2 }
}            # Podgorica

country =
{ tag                 = MTN
  puppet              = SER
  control             = SER
  regular_id          = SER
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 3
  capital             = 389
  transports          = 2
  escorts             = 0
  diplomacy =
  { relation = { tag = SER value = 200 access = yes }
  }
  nationalprovinces   = { 389 }
  ownedprovinces      = { 389 }
  controlledprovinces = { 389 }
  techapps            = 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Org
					1260
                                        1000 1050
                                        1010 1060
                                        1300 1310
                                        1500 1510
                                        1900 1910
					#Army Equip
					2200
                                        2000 2050
                                        2010 2060
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Aircraft
					4800 4700 4710 4750 4760
                                        4000 4010
                                        4640 4650
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160
					#Air Docs
					9010 9510
					9050 9060 9070
					#Navy docs
                                        8900
                                        8950
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 3
    free_market       = 6
    freedom           = 8
    professional_army = 3
    defense_lobby     = 4
    interventionism   = 5
  }
}
