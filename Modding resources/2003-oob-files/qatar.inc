##############################
# Country definition for QUE #
##############################
province =
{ id       = 1820
  air_base = { size = 2 current_size = 2 }
}            # Doha
country =
{ tag                 = QUE
  manpower            = 5
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  capital             = 1820
  transports          = 22
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1820 }
  ownedprovinces      = { 1820 }
  controlledprovinces = { 1820 }
  techapps            = {
                                        #Industry:
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060 5160
                                        5070 5170
                                        5080 5180
                                        5090 5190
                                        #Army Equipment:
                                        2000 2050 2110
                                        2010 2060
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050 1110
                                        1010 1060
                                        1500 1510 1520
                                        1300 1310 1320
                                             1700 1710
                                        1900 1910 1920
                                        1260 1270
                                        1970
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6120 6220
                                        6150
                                        6160 6260
                                        6170
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
                                        #Air Force:
                                        4700 4710
                                        4750 4760
                                        4640 4650
                                        4100 4110 4120
                                        4570
                                        4400 4410
                                        4000 4010
                                        #Air Force Docs:
                                        9510 9520 9020
                                        9120
                                        9050
                                        9060
                                        9070
                                        #Secret Techs:
                                        7330 7310
                        }
    policy = {
        date = { year = 0 month = march day = 0 }
        democratic = 1
        political_left = 5
        free_market = 6
        freedom = 3
        professional_army = 8
        defense_lobby = 9
        interventionism = 4
    }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12288 id = 1 }
    location = 1820
    name     = "Royal Qatar Army"
    division =
    { id            = { type = 12288 id = 2 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 12288 id = 3 }
      name          = "1st Armor Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12288 id = 100 }
    location = 1820
    base     = 1820
    name     = "Royal Qatar Air Force"
    division =
    { id       = { type = 12288 id = 101 }
      name     = "1st Fighter Squadron"
      type     = multi_role
      strength = 50
      model    = 2
    }
  }
}