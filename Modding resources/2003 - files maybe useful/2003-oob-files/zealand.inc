
##############################
# Country definition for NZL #
##############################

province =
{ id         = 1871
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 2 current_size = 2 }
}              # Wellington

country =
{ tag                 = NZL
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 10
  capital             = 1871
  transports          = 30
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1868 1869 1870 1871 1872 1873 }
  ownedprovinces      = { 1868 1869 1870 1871 1872 1873 }
  controlledprovinces = { 1868 1869 1870 1871 1872 1873 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        #Army Equip
                                        2300 2310
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Org
                                        1500 1510
                                        1300 1310 1320
                                        1900 1910 1920
                                        1260 1270
                                        1960 1980
                                        #Aircraft
                                        4400 4410
                                        4640 4650
                                        4700 4710
                                        4750 4760
                                        4900 4910
                                        #Land Doctrines
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6160
					6200 6210 6220 6260
                                        #Navy Techs
                                        3000 3010 3020
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8000 8010 8020
                                        8500 8510 8520
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 6
    free_market       = 9
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 5
  }
  # ###################################
  # ARMY
  # ###################################
  landunit =
  { id       = { type = 16600 id = 1 }
    location = 1871
    base     = 1871
    name     = "New Zealand Army"
    division =
    { id            = { type = 16600 id = 2 }
      name          = "2nd Land Force Group"
      strength      = 50
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 16600 id = 3 }
      name          = "3rd Land Force Group"
      strength      = 50
      type          = mechanized
      model         = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 16600 id = 300 }
    location = 1871
    base     = 1871
    name     = "Navy of New Zealand"
    division =
    { id    = { type = 16600 id = 301 }
      name  = "HMNZS Te Kaha"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 16600 id = 302 }
      name  = "HMNZS Te Mana"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 16600 id = 303 }
      name  = "HMNZS Canterbury"
      type  = destroyer
      model = 0
    }
  }
}