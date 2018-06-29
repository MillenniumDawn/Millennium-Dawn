
##############################
# Country definition for NEP #
##############################

country =
{ tag                 = NEP
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 5
  capital             = 1473
  diplomacy           = { }
  nationalprovinces   = { 1473 }
  ownedprovinces      = { 1473 }
  controlledprovinces = { 1473 }
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
                                        #Land Docs
					6010 6020 
					6910
					6100 6110 6120
                                        6160
					6600 6610
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1960
					1900
                                        #Secret Tech:
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 3
    free_market       = 5
    freedom           = 5
    professional_army = 10
    defense_lobby     = 3
    interventionism   = 5
  }
}
