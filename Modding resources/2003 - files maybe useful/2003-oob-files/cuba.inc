
##############################
# Country definition for CUB #
##############################

province =
{ id       = 654
  naval_base = { size = 2 current_size = 2 }
    air_base = { size = 4 current_size = 4 }
}            # Havanna

country =
{ tag                 = CUB
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  manpower            = 12
  capital             = 654
  transports          = 45
  escorts             = 0
  diplomacy           = { 
relation = { tag = VEN value = 200 }
 }
  nationalprovinces   = { 654 655 656 657 }
  ownedprovinces      = { 654 655 656 657 }
  controlledprovinces = { 654 655 656 657 }
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
                                             1700
                                             1800
					#Air techs
                                        4700
                                        4750
                                        4640
                                        4570
                                        4000 4010 4020
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Land Docs
					6910 6010 6030 6040 6600 6620
					6100 6110 6120 6140 6150 6160 6170
					#Secret
					7330
					#Navy
                                        3000
                                        3590
                                        3700
					#Navy Docs
                                        8900
                                        8950
                                        8400
                                        8000
                                        8500
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 10
    free_market       = 3
    freedom           = 1
    professional_army = 10
    defense_lobby     = 5
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8700 id = 1 }
    location = 654
    name     = "Western Command"
    division =
    { id       = { type = 8700 id = 2 }
      name     = "Cuban Army HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8700 id = 3 }
    location = 657
    name     = "1st Army"
    division =
    { id            = { type = 8700 id = 4 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 8700 id = 5 }
      name          = "1st Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 8700 id = 6 }
      name          = "2nd Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 8700 id = 7 }
    location = 655
    name     = "2nd Army"
    division =
    { id            = { type = 8700 id = 8 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 8700 id = 9 }
      name          = "3rd Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 8700 id = 10 }
      name          = "4th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 8700 id = 11 }
    location = 655
    name     = "3nd Army"
    division =
    { id            = { type = 8700 id = 12 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 8700 id = 13 }
      name          = "5th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 8700 id = 14 }
      name          = "6th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 8700 id = 15 }
    location = 657
    name     = "4th Army"
    division =
    { id            = { type = 8700 id = 16 }
      name          = "4th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 8700 id = 17 }
      name          = "7th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 8700 id = 18 }
      name          = "8th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 8700 id = 19 }
    location = 654
    name     = "5th Army"
    division =
    { id            = { type = 8700 id = 20 }
      name          = "5th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 8700 id = 21 }
      name          = "9th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 8700 id = 22 }
      name          = "1st Airborne Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 8700 id = 301 }
    location = 654
    base     = 654
    name     = "Cuban Navy"
    division =
    { id    = { type = 8700 id = 302 }
      name  = "U-001"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8700 id = 303 }
      name  = "1st transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8700 id = 304 }
      name  = "2nd transport Fleet"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 8700 id = 200 }
    location = 654
    base     = 654
    name     = "3rd Air Division"
    division =
    { id       = { type = 8700 id = 201 }
      name     = "1st Fighter Rgt"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8700 id = 202 }
      name     = "2nd Fighter Rgt"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8700 id = 206 }
      name     = "3rd Fighter Rgt"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8700 id = 208 }
      name     = "4th Fighter Rgt"
      type     = interceptor
      strength = 70
      model    = 2
    }
  }
}
