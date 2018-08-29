
##############################
# Country definition for CON #
##############################

province =
{ id         = 1075
   air_base = { size = 1 current_size = 1 }
}

country =
{ tag                 = CON
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 10
  capital             = 1075
  diplomacy           = { }
  nationalprovinces   = { 1075 1076 1093
                        }
  ownedprovinces      = { 1075 1076 1093
                        }
  controlledprovinces = { 1075 1076 1093
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
                                        4000 4010
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
    democratic        = 4
    political_left    = 6
    free_market       = 4
    freedom           = 3
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12256 id = 1 }
    location = 1075
    name     = "1st Corps"
    division =
    { id            = { type = 12256 id = 2 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12256 id = 4 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12256 id = 100 }
    location = 1075
    base     = 1075
    name     = "1st Wing"
    division =
    { id       = { type = 12256 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
  }
}
