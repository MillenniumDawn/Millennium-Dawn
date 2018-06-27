
##############################
# Country definition for PHI #
##############################

province =
{ id       = 1737
  naval_base = { size = 4 current_size = 4 }
}            # Manila

province =
{ id       = 1741
  air_base = { size = 6 current_size = 6 }
}            # Aparri

country =
{ tag                 = PHI
  # Resource Reserves
  energy              = 200
  metal               = 200
  rare_materials      = 200
  oil                 = 200
  supplies            = 500
  money               = 10
  manpower            = 151
  capital             = 1737
  transports          = 419
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1735 1736 1737 1738 1739 1740 1741 1742 1743 1744 1745 1746 1747 1748 1749 1750 }
  ownedprovinces      = { 1735 1736 1737 1738 1739 1740 1741 1742 1743 1744 1745 1746 1747 1748 1749 1750 }
  controlledprovinces = { 1735 1736 1737 1738 1739 1740 1741 1742 1743 1744 1745 1746 1747 1748 1749 1750 }
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
                                        1500 1500
                                        1300 1300
					1260
					1980
                                                  1600
					1900 1900
					#Aircraft
					4800 4700 4750
                                        4400
                                        4640 4650
                                        4550
                                        4570
                                        4700
                                        4750
                                        4800
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6130 6140 6150 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
                                        #Secret Tech:
                                        7330
                                        #Navy Techs
                                        3000
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 6
    free_market       = 7
    freedom           = 7
    professional_army = 4
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 18100 id = 1 }
    location = 1737
    name     = "I Corps"
    division =
    { id            = { type = 18100 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 18100 id = 3 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 18100 id = 4 }
      name     = "7th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 18100 id = 5 }
    location = 1745
    name     = "II Corps"
    division =
    { id            = { type = 18100 id = 6 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 18100 id = 7 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 18100 id = 8 }
    location = 1749
    name     = "III Corps"
    division =
    { id            = { type = 18100 id = 9 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 18100 id = 10 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 18100 id = 11 }
      name          = "1st Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 18100 id = 300 }
    location = 1737
    base     = 1737
    name     = "Philippine Navy"
    division =
    { id    = { type = 18100 id = 301 }
      name  = "BRP Rajah Humabon"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 18100 id = 316 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18100 id = 319 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18100 id = 322 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 18100 id = 200 }
    location = 1741
    base     = 1741
    name     = "5th Fighter Wing"
    division =
    { id       = { type = 18100 id = 201 }
      name     = "6th Tactical Fighter Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18100 id = 202 }
      name     = "'Blue Diamonds' Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
}
