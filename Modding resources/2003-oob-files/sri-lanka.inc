
##############################
# Country definition for SAR #
##############################

country =
{ tag                 = SAR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 40
  manpower            = 37
  capital             = 1517
  transports          = 23
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1516 1517 }
  ownedprovinces      = { 1516 1517 }
  controlledprovinces = { 1516 1517 }
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
                                             1700
                                             1800
					1900 1910
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
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
                                        4100 4110
					#Secret Techs
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 6
    free_market       = 6
    freedom           = 5
    professional_army = 10
    defense_lobby     = 4
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12232 id = 1 }
    location = 1516
    name     = "Special Operations Corps"
    division =
    { experience    = 5
      id            = { type = 12232 id = 2 }
      name          = "1st Commando Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { experience    = 5
      id            = { type = 12232 id = 3 }
      name          = "Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 12232 id = 4 }
      name          = "1st Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12232 id = 5 }
    location = 1517
    name     = "Sri Lankan Army"
    division =
    { id            = { type = 12232 id = 6 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 7 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 8 }
      name          = "3th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 9 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 10 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 11 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 12232 id = 12 }
    location = 1517
    name     = "Mechanized Corps"
    division =
    { id            = { type = 12232 id = 13 }
      name          = "1st Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 14 }
      name          = "2nd Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 15 }
      name          = "3rd Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 12232 id = 16 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
  }
}
