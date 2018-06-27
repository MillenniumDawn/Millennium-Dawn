
##############################
# Country definition for SIK #
##############################

province =
{ id       = 1353
  naval_base = { size = 4 current_size = 4 }
  air_base = { size = 4 current_size = 4 }
}            # Singapore

country =
{ tag                 = SIK
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 9
  capital             = 1353
  transports          = 50
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1353 }
  ownedprovinces      = { 1353 }
  controlledprovinces = { 1353 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
					2200 2210 2220 2230
					2300 2310 2320 2330
					2400 2410 2420 2430
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1980
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
					1260 1270
					1900 1910 1920
					1800 1810
					1300 1310 1320
					1400 1410 1420
					#Aircraft
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910 4920
                                        4640 4650 4660
                                        4400 4410
                                        4570
                                        4000 4010 4020 4030
					#Land Docs
					6010 6020
					6930
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9120
					9130 9140 9150 9200
                                        #Navy Techs
                                        3000 3010 3020
                                        3700 3710 3720
                                        3590 3600
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        #Secret techs
                                        7330 7310 7320
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 9
    freedom           = 5
    professional_army = 3
    defense_lobby     = 6
    interventionism   = 6
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 19400 id = 1 }
    location = 1353
    name     = "I Corps"
    division =
    { id            = { type = 19400 id = 2 }
      name          = "Singapore Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 19400 id = 3 }
      name          = "3rd Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 19400 id = 4 }
      name          = "6th Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 19400 id = 5 }
      name          = "9th Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 19400 id = 6 }
      name          = "21st Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 19400 id = 200 }
    location = 1353
    base     = 1353
    name     = "1st Fleet"
    division =
    { id    = { type = 19400 id = 207 }
      name  = "RSS Challenger"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 19400 id = 208 }
      name  = "RSS Conqueror"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 19400 id = 209 }
      name  = "RSS Centurion"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 19400 id = 210 }
      name  = "RSS Cavalier"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 19400 id = 212 }
      name  = "RSS Endurance"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 19400 id = 213 }
      name  = "RSS Resolution"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 19400 id = 214 }
      name  = "RSS Presistence"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 19400 id = 215 }
      name  = "RSS Endeavour"
      type  = transport
      model = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 19400 id = 100 }
    location = 1353
    base     = 1353
    name     = "1st Air Force"
    division =
    { id       = { type = 19400 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 19400 id = 102 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 19400 id = 103 }
      name     = "3rd Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
}
