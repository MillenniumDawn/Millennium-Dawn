
##############################
# Country definition for SAF #
##############################

province =
{ id       = 1116
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 2 current_size = 2 }
}            # Cape Town

province =
{ id       = 1120
    air_base = { size = 4 current_size = 4 }
}            # Johannesburg

country =
{ tag                 = SAF
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 90
  manpower            = 49
  transports          = 50
  escorts             = 0
  capital             = 1121
  diplomacy           = { }
  nationalprovinces   = { 1115 1116 1114 1117 1118 1120 1113 1121 1119 }
  ownedprovinces      = { 1115 1116 1114 1117 1118 1120 1113 1121 1119 }
  controlledprovinces = { 1115 1116 1114 1117 1118 1120 1113 1121 1119 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210 2220
					2600 2610 2620
					2800 2810 2820
					2700 2710 2720
					2300 2310 
					2400 2410
					2000 2010
					2500 2510
					#Army Org
					1000 1010
					1960 1970
					1900 1910
					1800
					1700
					1260
					1500 1510
					1400 1410
					1300 1310
					1200 1210
					#Aircraft
                                        4700 4710 4720
                                        4750 4760 4770
                                        4800 4810
                                        4000 4010 4020 4030
                                        4100 4110
                                        4900 4910
					4640 4650 4660
                                        4400 4410
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9120
					9130 9140 9150
					#Secret Weapons
					7180
					7010 7060 7070
                                        7330 7310
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3700 37700 3710 37710
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 10
    free_market       = 7
    freedom           = 8
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 19900 id = 1 }
    location = 1121
    name     = "I Corps"
    division =
    { id       = { type = 19900 id = 2 }
      name     = "4th Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 19900 id = 3 }
      name     = "1st Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 19900 id = 4 }
      name     = "South African Army HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 19900 id = 5 }
    location = 1116
    name     = "II Corps"
    division =
    { experience    = 5
      id       = { type = 19900 id = 6 }
      name     = "1st Special Forces Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
    }
    division =
    { id       = { type = 19900 id = 7 }
      name     = "1st Airborne Brigade"
      strength = 100
      type     = paratrooper
      model    = 14
    }
  }
  landunit =
  { id       = { type = 19900 id = 8 }
    location = 1117
    name     = "III Corps"
    division =
    { id       = { type = 19900 id = 9 }
      name     = "1st Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 19900 id = 300 }
    location = 1116
    base     = 1116
    name     = "Submarine Fleet"
    division =
    { id    = { type = 19900 id = 301 }
      name  = "SAS Umkhonto"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 19900 id = 302 }
      name  = "SAS Assegaai"
      type  = submarine
      model = 0
    }
  }
  navalunit =
  { id       = { type = 19900 id = 303 }
    location = 1116
    base     = 1116
    name     = "Surface Fleet"
    division =
    { id    = { type = 19900 id = 304 }
      name  = "SAS Amatola"
      type  = destroyer
      model = 3
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 19900 id = 200 }
    location = 1120
    base     = 1120
    name     = "1st Air Force"
    division =
    { id       = { type = 19900 id = 201 }
      name     = "1st Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 19900 id = 202 }
    location = 1116
    base     = 1116
    name     = "2nd Air Force"
    division =
    { id       = { type = 19900 id = 203 }
      name     = "2nd Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 19900 id = 401 }
    name  = "SAS Manthatisi"
    type  = submarine
    model = 3
    cost  = 2
    date  = { day = 28 month = november year = 2003 }
  }
  division_development =
  { id    = { type = 19900 id = 402 }
    name  = "SAS Charlotte Maxeke"
    type  = submarine
    model = 3
    cost  = 2
    date  = { day = 13 month = june year = 2004 }
  }
  division_development =
  { id    = { type = 19900 id = 403 }
    name  = "SAS Queen Modjadji I"
    type  = submarine
    model = 3
    cost  = 2
    date  = { day = 4 month = september year = 2005 }
  }
  division_development =
  { id    = { type = 19900 id = 404 }
    name  = "SAS Isandlwana"
      type  = destroyer
      model = 3
    cost  = 2
    date  = { day = 28 month = april year = 2003 }
  }
  division_development =
  { id    = { type = 19900 id = 405 }
    name  = "SAS Spioenkop"
      type  = destroyer
      model = 3
    cost  = 2
    date  = { day = 13 month = june year = 2004 }
  }
  division_development =
  { id    = { type = 19900 id = 406 }
    name  = "SAS Mendi"
      type  = destroyer
      model = 3
    cost  = 2
    date  = { day = 4 month = september year = 2004 }
  }
}
