
##############################
# Country definition for BOS #
##############################

province =
{ id       = 387
  naval_base = { size = 2 current_size = 2 }
}            # Mostar

province =
{ id       = 383
  air_base = { size = 2 current_size = 2 }
}            # Sarajevo

country =
{ tag                 = BOS
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 8
  capital             = 386
  diplomacy           = { }
  nationalprovinces   = { 386 383 385 387 1402 1403 1449 1595 1875 1876 1886 1890 }
  ownedprovinces      = { 386 383 385 387 1402 1403 1449 1595 1875 1876 1886 1890 }
  controlledprovinces = { 386 383 385 387 1402 1403 1449 1595 1875 1876 1886 1890 }
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
                                        2400 2410
                                        2200 2210 2220
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Army Organisation:
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6160 6260
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 4
    free_market       = 4
    freedom           = 5
    professional_army = 4
    defense_lobby     = 6
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 6900 id = 1 }
    location = 386
    name     = "I Corps"
    division =
    { id            = { type = 6900 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 6900 id = 3 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 6900 id = 4 }
    location = 386
    name     = "II Corps"
    division =
    { id            = { type = 6900 id = 5 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 6900 id = 6 }
    location = 385
    name     = "III Corps"
    division =
    { id       = { type = 6900 id = 7 }
      name     = "3rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
}
