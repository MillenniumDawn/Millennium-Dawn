
##############################
# Country definition for OMN #
##############################

province =
{ id       = 1819
  naval_base = { size = 2 current_size = 2 }
    air_base = { size = 2 current_size = 2 }
}            # Mascate
country =
{ tag                 = OMN
  # Resource Reserves
  energy              = 500
  metal               = 500
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  capital             = 1819
  manpower            = 15
  transports          = 10
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1819 }
  ownedprovinces      = { 1819 }
  controlledprovinces = { 1819 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        #Army Equip:
                                        2000 2050 2110
                                        2010      2120
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
                                        1000      1110
                                        1010      1120
                                        1500 1510 1520
                                        1300 1310 1320
					1260 1270
					1970
                                        1900 1910 1920
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700
                                        4750
                                        4640 4650
                                        4570
					#Secret Techs
                                        7330 7310
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
					6200 6210 6220 6260 6270
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 2
    political_left    = 5
    free_market       = 7
    freedom           = 3
    professional_army = 10
    defense_lobby     = 9
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 17300 id = 1 }
    location = 1819
    name     = "Oman Royal Army"
    division =
    { id            = { type = 17300 id = 2 }
      name          = "Royal Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
  }
}
