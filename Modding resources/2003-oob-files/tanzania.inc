
##############################
# Country definition for TAN #
##############################

country =
{ tag                 = TAN
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 50
  capital             = 1140
  transports          = 5
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1062 1139 1140 1141
                        }
  ownedprovinces      = { 1062 1139 1140 1141
                        }
  controlledprovinces = { 1062 1139 1140 1141
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300
                                        2400
                                        2200 2210
                                        2500
                                        2600
                                        2700
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1980
					1900
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700
                                        4750
                                        4640
                                        4570
					#Secret Techs
                                        7330
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 6
    political_left    = 5
    free_market       = 6
    freedom           = 4
    professional_army = 3
    defense_lobby     = 2
    interventionism   = 5
  }
}
