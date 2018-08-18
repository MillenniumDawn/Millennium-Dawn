
##############################
# Country definition for MAN #
##############################

province =
{ id         = 31
  naval_base = { size = 1 current_size = 1 }
}              # Malta

country =
{ tag                 = MAN
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 1
  transports          = 30
  escorts             = 0
  capital             = 31
  diplomacy           = { }
  nationalprovinces   = { 31 }
  ownedprovinces      = { 31 }
  controlledprovinces = { 31 }
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
                                        #Secret Tech:
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 4
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12227 id = 1 }
    location = 31
    name     = "Malta Defence Force"
    division =
    { id            = { type = 12227 id = 2 }
      name          = "1st Regiment"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
}
