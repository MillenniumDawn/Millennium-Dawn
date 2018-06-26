
##############################
# Country definition for EUS #
##############################

province =
{ id       = 1125
  air_base = { size = 2 current_size = 2 }
}            # Harare


country =
{ tag                 = EUS
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 45
  capital             = 1125
  diplomacy           = { 
    relation = { tag = CHC value = 150 }}

  nationalprovinces   = { 1124 1125
                        }
  ownedprovinces      = { 1124 1125
                        }
  controlledprovinces = { 1124 1125
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500 1510
                                        1300 1310
					1260
					1980
					1900 1910
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
                                        4000 4010
                                        4570
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
    democratic        = 3
    political_left    = 2
    free_market       = 3
    freedom           = 1
    professional_army = 1
    defense_lobby     = 4
    interventionism   = 8
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12202 id = 1 }
    location = 1125
    name     = "Zimbabwe Army Corps"
    division =
    { id            = { type = 12202 id = 2 }
      name          = "Presidential Guard Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12202 id = 3 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { experience    = 5
      id            = { type = 12202 id = 4 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12202 id = 100 }
    location = 1125
    base     = 1125
    name     = "National Liberation Airforce"
    division =
    { id       = { type = 12202 id = 101 }
      name     = "1st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
}
