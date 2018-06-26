
##############################
# Country definition for CYN #
##############################

country =
{ tag                 = CYN
  puppet              = U06
  control             = U06
  regular_id          = SER
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 3
  capital             = 415
  transports          = 0
  escorts             = 0
  diplomacy =
  {
  }
  nationalprovinces   = { 415 }
  ownedprovinces      = { 415 }
  controlledprovinces = { 415 }
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
					1980
					1900
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 6
    free_market       = 6
    freedom           = 8
    professional_army = 10
    defense_lobby     = 1
    interventionism   = 1
  }
}
