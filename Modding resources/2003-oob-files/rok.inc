
##############################
# Country definition for KOR #
##############################

province =
{ id       = 1196
  naval_base = { size = 8 current_size = 8 }
    air_base = { size = 8 current_size = 8 }
}            # Busan

province =
{ id       = 1199
    air_base = { size = 6 current_size = 6 }
 rocket_test = { size = 2 current_size = 2 }
}            # Seoul

country =
{ tag                 = KOR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 90
  manpower            = 34
  capital             = 1199
  transports          = 150
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1194 1195 1196 1197 1198 1199 1200 1201 1376 1391 1392 1393 }
  ownedprovinces      = { 1194 1195 1196 1197 1198 1199 }
  controlledprovinces = { 1194 1195 1196 1197 1198 1199 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2600 2610 2620 2630
					2800 2810 2820 2830
					2700 2710 2720 2730
					2500 2510 2520 2530
					2400 2410 2420 2430
					2300 2310 2320 2330
                                        2000 2050 2110
                                        2010      2120
					#Army Org
					1260 1990
					1900 1910 1920 1930
					1800 1810 1820
					1500 1510 1520 1530
					1200 1210 1220 1230
					1400 1410 1420 1430
					1300 1310 1320 1330
					1600 1610 
					1650 1660
                                        1000 1050 1110
                                        1010 1060 1120
					1700
					#Aircraft
                                        4640 4650
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
                                        4000 4010 4020 4030
                                        4100 4110
                                        4400 4410
					4900 4910 4920
					#Land Docs
                                        6910 6920 6930
					6020 6030 6040
					6600 6630
					6700 6730
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9100 9110 9120
					9130 9140 9150 9170 9180 9190 9200
					9210 9280
					#Secret Weapons
					7010 7060 7070 7080
					7180 7190
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010
                                        3100 3110 3120 3130
                                        3590
                                        3700 3710 37710 3720
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                        }

  blueprints          = { 3200 3210 3220 3400 3410 }

  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 6
    free_market       = 7
    freedom           = 8
    professional_army = 2
    defense_lobby     = 4
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 20000 id = 1 }
    location = 1199
    name     = "Special Warfare Command"
    division =
    { experience    = 10
      id            = { type = 20000 id = 2 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 10
      id            = { type = 20000 id = 3 }
      name          = "3rd Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 10
      id            = { type = 20000 id = 4 }
      name          = "5th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 10
      id            = { type = 20000 id = 5 }
      name          = "7th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 10
      id            = { type = 20000 id = 6 }
      name          = "11th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 10
      id            = { type = 20000 id = 7 }
      name          = "13th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 20000 id = 8 }
    location = 1198
    name     = "First Army"
    division =
    { id            = { type = 20000 id = 9 }
      name          = "First ROK Army HQ"
      strength      = 100
      type          = hq
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 20000 id = 10 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id       = { type = 20000 id = 11 }
      name     = "11th Infantry Division (Mech)"
      strength = 100
      type     = infantry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 12 }
    location = 1199
    name     = "II Corps"
    division =
    { id            = { type = 20000 id = 13 }
      name          = "7th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 14 }
      name          = "15th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 15 }
      name          = "27th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 16 }
    location = 1199
    name     = "III Corps"
    division =
    { id            = { type = 20000 id = 17 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 18 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 19 }
      name          = "21st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 20 }
    location = 1198
    name     = "VIII Corps"
    division =
    { id            = { type = 20000 id = 21 }
      name          = "22nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 22 }
      name          = "23rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id       = { type = 20000 id = 23 }
      name     = "102nd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 24 }
    location = 1199
    name     = "IX CORPS"
    division =
    { id       = { type = 20000 id = 25 }
      name     = "2nd ROK Army"
      strength = 100
      type     = hq
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 20000 id = 26 }
      name     = "201st Special Assault Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
    }
    division =
    { id       = { type = 20000 id = 27 }
      name     = "205th Special Assault Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
    }
    division =
    { id       = { type = 20000 id = 28 }
      name     = "700th Special Assault Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
    }
    division =
    { id       = { type = 20000 id = 29 }
      name     = "17th Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 20000 id = 30 }
      name     = "103rd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 31 }
    location = 1198
    name     = "I Corps"
    division =
    { id       = { type = 20000 id = 32 }
      name     = "3rd ROK Army"
      strength = 100
      type     = hq
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 20000 id = 33 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 20000 id = 34 }
      name          = "101st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 35 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 36 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 37 }
      name          = "25th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 38 }
      name          = "30th Infantry Division (Mech)"
      strength      = 100
      type          = infantry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 39 }
    location = 1198
    name     = "V Corps"
    division =
    { id            = { type = 20000 id = 40 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 20000 id = 41 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 42 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 43 }
      name          = "8th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 44 }
    location = 1196
    name     = "VI Corps"
    division =
    { id       = { type = 20000 id = 45 }
      name     = "4th ROK Army HQ"
      strength = 100
      type     = hq
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 20000 id = 46 }
      name          = "5th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 20000 id = 47 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 48 }
      name          = "26th Infantry Division (Mech)"
      strength      = 100
      type          = infantry
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 49 }
      name          = "28th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 50 }
    location = 1199
    name     = "VII Corps"
    division =
    { id       = { type = 20000 id = 51 }
      name     = "7th Assault Group"
      strength = 100
      type     = bergsjaeger
      model    = 13
    }
    division =
    { id            = { type = 20000 id = 52 }
      name          = "'Tiger' Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 2
    }
    division =
    { id            = { type = 20000 id = 53 }
      name          = "20th Infantry Division (Mech)"
      strength      = 100
      type          = infantry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 20000 id = 54 }
    location = 1196
    name     = "I Marine Army"
    division =
    { id            = { type = 20000 id = 55 }
      name          = "6th Marine Brigade"
      strength      = 100
      type          = marine
      model         = 12
    }
    division =
    { id            = { type = 20000 id = 56 }
      name          = "1st Marine Division"
      strength      = 100
      type          = marine
      model         = 17
    }
    division =
    { id            = { type = 20000 id = 57 }
      name          = "2nd Marine Division"
      strength      = 100
      type          = marine
      model         = 17
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 20000 id = 200 }
    location = 1196
    base     = 1196
    name     = "1st Fleet"
    division =
    { id    = { type = 20000 id = 201 }
      name  = "Kwanggaeto"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 20000 id = 202 }
      name  = "Che Ju"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 203 }
      name  = "Ulsan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 204 }
      name  = "Masan"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 20000 id = 218 }
    location = 1196
    base     = 1196
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 20000 id = 219 }
      name  = "Lee Jongmu"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 220 }
      name  = "Jeong Un"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 221 }
      name  = "Lee Sunsin"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 222 }
      name  = "Na Daeyong"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 223 }
      name  = "Lee Eokgi"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 20000 id = 224 }
    location = 1196
    base     = 1196
    name     = "2nd Fleet"
    division =
    { id    = { type = 20000 id = 225 }
      name  = "Ulchimundok"
      type  = light_cruiser
      model = 7
    }
    division =
    { id    = { type = 20000 id = 226 }
      name  = "Busan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 227 }
      name  = "Seoul"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 228 }
      name  = "Keong Buk"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 20000 id = 229 }
    location = 1196
    base     = 1196
    name     = "2nd Submarine Fleet"
    division =
    { id    = { type = 20000 id = 230 }
      name  = "Jang Bogo"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 231 }
      name  = "Lee Chun"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 232 }
      name  = "Choi Museon"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 20000 id = 233 }
      name  = "Park Wi"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 20000 id = 234 }
    location = 1196
    base     = 1196
    name     = "3rd Fleet"
    division =
    { id    = { type = 20000 id = 235 }
      name  = "Yang Manchun"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 20000 id = 236 }
      name  = "Chung Ju"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 237 }
      name  = "Chung Nam"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 20000 id = 238 }
      name  = "Chon Nam"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 20000 id = 239 }
    location = 1196
    base     = 1196
    name     = "5th Flotilla"
    division =
    { id    = { type = 20000 id = 240 }
      name  = "1st Transport Flottila"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 20000 id = 241 }
      name  = "2nd Transport Flottila"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 20000 id = 242 }
      name  = "3rd Transport Flottila"
      type  = transport
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 20000 id = 100 }
    location = 1196
    base     = 1196
    name     = "1st Tactical Fighter Wing"
    division =
    { id       = { type = 20000 id = 101 }
      name     = "1st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 102 }
      name     = "8th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 103 }
      name     = "10th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 104 }
      name     = "16th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20000 id = 105 }
    location = 1196
    base     = 1196
    name     = "7th Tactical Fighter Wing"
    division =
    { id       = { type = 20000 id = 106 }
      name     = "21st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 107 }
      name     = "55th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 108 }
      name     = "19th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20000 id = 109 }
    location = 1199
    base     = 1199
    name     = "3rd Tactical Fighter Wing"
    division =
    { id       = { type = 20000 id = 110 }
      name     = "17th Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 111 }
      name     = "18th Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 112 }
      name     = "13th Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20000 id = 113 }
    location = 1199
    base     = 1199
    name     = "17th Tactical Fighter Wing"
    division =
    { id       = { type = 20000 id = 114 }
      name     = "37th Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 115 }
      name     = "81st Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20000 id = 116 }
      name     = "27th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 20000 id = 117 }
      name     = "26th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 20000 id = 118 }
    location = 1199
    base     = 1199
    name     = "3rd Tactical Fighter Wing"
    division =
    { id       = { type = 20000 id = 119 }
      name     = "28th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 20000 id = 120 }
      name     = "29th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 20000 id = 121 }
      name     = "39th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 20000 id = 122 }
    location = 1196
    base     = 1196
    name     = "Airlift Command"
    division =
    { id       = { type = 20000 id = 123 }
      name     = "Airlift Command"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 20000 id = 300 }
    name  = "Chungmugong Yi Sunshin"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 12 month = april year = 2003 }
  }
  division_development =
  { id    = { type = 20000 id = 301 }
    name  = "Munmu the Great"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 24 month = september year = 2004 }
  }
  division_development =
  { id    = { type = 20000 id = 302 }
    name  = "Dae Joyeong"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 6 month = march year = 2005 }
  }
}
