
##############################
# Country definition for YEM #
##############################

province =
{ id         = 1813
  naval_base = { size = 2 current_size = 2 }
  air_base = { size = 2 current_size = 2 }
}              # Aden
country =
{ tag                 = YEM
  # Resource Reserves
  energy              = 200
  metal               = 200
  rare_materials      = 200
  oil                 = 200
  supplies            = 200
  money               = 10
  manpower            = 40
  capital             = 1812
  transports          = 5
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1812 1813 1814 1815 }
  ownedprovinces      = { 1812 1813 1814 1815 }
  controlledprovinces = { 1812 1813 1814 1815 }
  techapps            = {
                                        #Army Equip
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Army Org
                                        1000 1050
                                        1010
                                        1500
                                        1200
                                        1300 1310
                                        1400 1410
                                        1900
                                             1700
                                             1800
                                        1260
                                        1960 1970
                                        #Army Doc
                                        6100
                                        6110
                                        6120
                                        6140
                                        6150
                                        6160
                                        6170
                                        6010
                                        6020
                                        6910
                                        6600
                                        6630
                                        #Industry
                                        5010
                                        5020
                                        5030
                                        5040
                                        5050
                                        5060
                                        5070
                                        5080
                                        5090
                                        #Air Force
                                        4000 4010
                                        4570
                                        4640
                                        4700
                                        4750
                                        4400
                                        #Air Docs
                                        9050
                                        9060
                                        9070
                                        9090
                                        9010
                                        9510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 4
    freedom           = 4
    professional_army = 3
    defense_lobby     = 7
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12230 id = 1 }
    location = 1812
    name     = "Armored Corps"
    division =
    { id            = { type = 12230 id = 2 }
      name          = "Yemen HQ"
      strength      = 100
      type          = hq
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 3 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 4 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 5 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 6 }
      name          = "4th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 7 }
      name          = "5th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 8 }
      name          = "6th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 12230 id = 9 }
      name          = "7th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 10 }
      name          = "8th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 11 }
      name          = "9th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 12 }
      name          = "10th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
  }
  landunit =
  { id       = { type = 12230 id = 13 }
    location = 1813
    name     = "Special Command Corps"
    division =
    { id            = { type = 12230 id = 14 }
      name          = "1st Airborne Brigade"
      strength      = 100
      type          = paratrooper
      model         = 14
    }
    division =
    { id            = { type = 12230 id = 15 }
      name          = "2nd Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12230 id = 16 }
    location = 1814
    name     = "Army Corps"
    division =
    { id            = { type = 12230 id = 17 }
      name          = "1st Motorized Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 18 }
      name          = "2nd Motorized Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 19 }
      name          = "3rd Motorized Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 20 }
      name          = "4th Motorized Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12230 id = 21 }
      name          = "5th Motorized Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12230 id = 100 }
    location = 1813
    base     = 1813
    name     = "Aden Transport Wing"
    division =
    { id       = { type = 12230 id = 101 }
      name     = "1st Squadron"
      type     = transport_plane
      strength = 100
      model    = 0
    }
  }
}
