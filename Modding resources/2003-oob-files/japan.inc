
##############################
# Country definition for JAP #
##############################

province =
{ id         = 1184
  naval_base = { size = 10 current_size = 10 }
  rocket_test = { size = 4 current_size = 4 }
}              # Tokyo

province =
{ id         = 1190
  naval_base = { size = 10 current_size = 10 }
  air_base = { size = 8 current_size = 8 }
}              # Fukuoka

province =
{ id       = 1180
    air_base = { size = 10 current_size = 10 }
}            # Sendai

country =
{ tag                 = JAP
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 200
  manpower            = 140
  transports          = 250
  escorts             = 0
  capital             = 1184
  diplomacy =
  { relation = { tag = USA value = 200 access = yes }
  }
  nationalprovinces   = { 1178 1179 1180 1181 1182 1183 1184 1185 1186 1187 1188 1189 1190 1191 1192 1193 1177 1599 1784 1785 }
  ownedprovinces      = { 1178 1179 1180 1181 1182 1183 1184 1185 1186 1187 1188 1189 1190 1191 1192 1599 1784 1785 }
  controlledprovinces = { 1178 1179 1180 1181 1182 1183 1184 1185 1186 1187 1188 1189 1190 1191 1192 1599 1784 1785 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2000 2010
					2050 2060 2070
					2110 2120
					2300 2310 2320 2330
					2400 2410 2420 2430
					2200 2210 2220 2230
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1000 1010
					1050 1060 1070
					1110
					1500 1510 1520 1530
					1200 1210 1220 1230
					1300 1310 1320 1330
					1400 1410 1420 1430
					1960
					1900 1910 1920 1930
					1260 1270
					1700 1710 1720
					1800 1810 1820
					#Aircraft
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4500 4570
                                        4000 4010 4020 4030
                                        4100 4110 4120 4130
                                        4300 4310 4320
                                        4400 4410
					4640 4650 4660 4670
					4900 4910 4920
					#Land Docs
					6010 6020
					6930
					6600 6610
					6700 6710
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					6300 6310 6320 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9100 9110 9120
					9130 9140 9150 9170 9180 9190 9200
					9210 9220 9230 9280
					#Secret Weapons
					7010
					7060 7070 7080
					7180 7190 7200
                                        7330 7310 7320 7380
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3100 3110 3120
                                        3590
                                        3590 3600
                                        3700 37700 3710 37710 3720 37720
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910 8920 8930
                                        8950 8960 8970 8980
                                        8400 8410 8420
                                        8000 8010 8020 8030
                                        8500 8510 8520 8530
                                        8100 8110 8120 8130
                                        8600 8610 8620 8630
                        }
  blueprints          = { 3400 3410 }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 4
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 2
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 13200 id = 1 }
    location = 1179
    name     = "Northern Army"
    division =
    { id            = { type = 13200 id = 2 }
      name          = "Nippon HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 13200 id = 3 }
      name          = "2nd Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
    division =
    { id            = { type = 13200 id = 4 }
      name          = "7th Armored Division"
      strength      = 100
      type          = armor
      model         = 16
    }
    division =
    { id       = { type = 13200 id = 5 }
      name     = "11th Army Division"
      strength = 100
      type     = motorized
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 6 }
      name     = "5th Brigade"
      strength = 100
      type     = cavalry
      model    = 3
    }
  }
  landunit =
  { id       = { type = 13200 id = 7 }
    location = 1180
    name     = "Northeastern Army"
    division =
    { id            = { type = 13200 id = 8 }
      name          = "6th Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
    division =
    { id            = { type = 13200 id = 9 }
      name          = "9th Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
  }
  landunit =
  { id       = { type = 13200 id = 10 }
    location = 1184
    name     = "Eastern Army"
    division =
    { id            = { type = 13200 id = 11 }
      name          = "1st Army Division"
      strength      = 100
      type          = motorized
      model         = 3
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 13200 id = 12 }
      name          = "12th Brigade"
      strength      = 100
      type          = cavalry
      model         = 3
    }
  }
  landunit =
  { id       = { type = 13200 id = 13 }
    location = 1184
    name     = "Special Forces Command"
    division =
    { experience    = 10
      id       = { type = 13200 id = 14 }
      name     = "1st Airborne Brigade"
      strength = 100
      type     = paratrooper
      model    = 16
    }
  }
  landunit =
  { id       = { type = 13200 id = 15 }
    location = 1187
    name     = "Middle Army"
    division =
    { id            = { type = 13200 id = 16 }
      name          = "3rd Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
    division =
    { id            = { type = 13200 id = 17 }
      name          = "10th Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
    division =
    { id       = { type = 13200 id = 18 }
      name     = "13th Brigade"
      strength = 100
      type     = mechanized
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 19 }
      name     = "14th Brigade"
      strength = 100
      type     = mechanized
      model    = 3
    }
  }
  landunit =
  { id       = { type = 13200 id = 20 }
    location = 1189
    name     = "Western Army"
    division =
    { id            = { type = 13200 id = 21 }
      name          = "4th Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
    division =
    { id            = { type = 13200 id = 22 }
      name          = "8th Army Division"
      strength      = 100
      type          = motorized
      model         = 3
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 13200 id = 201 }
    location = 1184
    base     = 1184
    name     = "1st Escort Flotilla"
    division =
    { id    = { type = 13200 id = 202 }
      name  = "JDS Shirane"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 203 }
    location = 1184
    base     = 1184
    name     = "2nd Escort Flotilla"
    division =
    { id    = { type = 13200 id = 204 }
      name  = "JDS Kurama"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 205 }
    location = 1184
    base     = 1184
    name     = "3rd Escort Flotilla"
    division =
    { id    = { type = 13200 id = 206 }
      name  = "JDS Haruna"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 207 }
    location = 1184
    base     = 1184
    name     = "4th Escort Flotilla"
    division =
    { id    = { type = 13200 id = 208 }
      name  = "JDS Hiei"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 209 }
    location = 1184
    base     = 1184
    name     = "1st Destroyer Division"
    division =
    { id    = { type = 13200 id = 210 }
      name  = "JDS Murasame"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 211 }
      name  = "JDS Harusame"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 212 }
      name  = "JDS Kirisame"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 213 }
      name  = "JDS Ariake"
      type  = destroyer
      model = 3
    }
  }
  navalunit =
  { id       = { type = 13200 id = 214 }
    location = 1184
    base     = 1184
    name     = "2nd Destroyer Division"
    division =
    { id    = { type = 13200 id = 215 }
      name  = "JDS Imazuma"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 216 }
      name  = "JDS Yamayuki"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 13200 id = 217 }
      name  = "JDS Matsuyuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 218 }
    location = 1184
    base     = 1184
    name     = "3rd Destroyer Division"
    division =
    { id    = { type = 13200 id = 219 }
      name  = "JDS Yudachi"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 220 }
      name  = "JDS Samidare"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 221 }
      name  = "JDS Mineyuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 222 }
    location = 1184
    base     = 1184
    name     = "4th Destroyer Division"
    division =
    { id    = { type = 13200 id = 223 }
      name  = "JDS Ikazuchi"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 224 }
      name  = "JDS Isoyuki"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 13200 id = 225 }
      name  = "JDS Harayuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 226 }
    location = 1184
    base     = 1184
    name     = "5th Destroyer Division"
    division =
    { id    = { type = 13200 id = 227 }
      name  = "JDS Yuugiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 228 }
      name  = "JDS Amagiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 229 }
      name  = "JDS Umigiri"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 13200 id = 230 }
    location = 1184
    base     = 1184
    name     = "6th Destroyer Division"
    division =
    { id    = { type = 13200 id = 231 }
      name  = "JDS Asagiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 232 }
      name  = "JDS Yamagiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 233 }
      name  = "JDS Sawagiri"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 13200 id = 234 }
    location = 1184
    base     = 1184
    name     = "7th Destroyer Division"
    division =
    { id    = { type = 13200 id = 235 }
      name  = "JDS Akebono"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 13200 id = 236 }
      name  = "JDS Setoyuki"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 13200 id = 237 }
      name  = "JDS Asayuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 238 }
    location = 1184
    base     = 1184
    name     = "8th Destroyer Division"
    division =
    { id    = { type = 13200 id = 239 }
      name  = "JDS Hamagiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 240 }
      name  = "JDS Setogiri"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 13200 id = 241 }
      name  = "JDS Sawayuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 242 }
    location = 1184
    base     = 1184
    name     = "21st Destroyer Division"
    division =
    { id    = { type = 13200 id = 243 }
      name  = "JDS Hatsuyuki"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 13200 id = 244 }
      name  = "JDS Shirayuki"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 265 }
    location = 1184
    base     = 1184
    name     = "1st Destroyer Division"
    division =
    { id    = { type = 13200 id = 266 }
      name  = "JDS Kirishima"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 13200 id = 267 }
      name  = "JDS Hatakaze"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 268 }
    location = 1184
    base     = 1184
    name     = "62nd Destroyer Division"
    division =
    { id    = { type = 13200 id = 269 }
      name  = "JDS Kongo"
      type  = light_cruiser
      model = 2
    }
  }
  navalunit =
  { id       = { type = 13200 id = 271 }
    location = 1184
    base     = 1184
    name     = "63rd Destroyer Division"
    division =
    { id    = { type = 13200 id = 272 }
      name  = "JDS Myoko"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 13200 id = 273 }
      name  = "JDS Shimakaze"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 274 }
    location = 1184
    base     = 1184
    name     = "64th Destroyer Division"
    division =
    { id    = { type = 13200 id = 275 }
      name  = "JDS Chokai"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 13200 id = 276 }
      name  = "JDS Tachikaze"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 13200 id = 277 }
      name  = "JDS Asakaze"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 13200 id = 278 }
    location = 1190
    base     = 1190
    name     = "1st Submarine Division"
    division =
    { id    = { type = 13200 id = 279 }
      name  = "JDS Michishio"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 13200 id = 280 }
      name  = "JDS Uzushio"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 13200 id = 281 }
      name  = "JDS Makishio"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 13200 id = 283 }
    location = 1190
    base     = 1190
    name     = "2nd Submarine Division"
    division =
    { id    = { type = 13200 id = 284 }
      name  = "JDS Isoshio"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 13200 id = 285 }
      name  = "JDS Narushio"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 13200 id = 288 }
    location = 1190
    base     = 1190
    name     = "3rd Submarine Division"
    division =
    { id    = { type = 13200 id = 289 }
      name  = "JDS Hayashio"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 13200 id = 290 }
      name  = "JDS Arashio"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 13200 id = 291 }
      name  = "JDS Fuyushio"
      type  = submarine
      model = 3
    }
  }
  navalunit =
  { id       = { type = 13200 id = 296 }
    location = 1190
    base     = 1190
    name     = "5th Submarine Division"
    division =
    { id    = { type = 13200 id = 297 }
      name  = "JDS Harushio"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 13200 id = 298 }
      name  = "JDS Natsushio"
      type  = submarine
      model = 3
    }
  }
  navalunit =
  { id       = { type = 13200 id = 300 }
    location = 1190
    base     = 1190
    name     = "6th Submarine Division"
    division =
    { id    = { type = 13200 id = 301 }
      name  = "JDS Oyashio"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 13200 id = 302 }
      name  = "JDS Wakashio"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 13200 id = 303 }
      name  = "JDS Asashio"
      type  = submarine
      model = 3
    }
  }
  navalunit =
  { id       = { type = 13200 id = 304 }
    location = 1184
    base     = 1184
    name     = "1st Amphibious Flotilla"
    division =
    { id    = { type = 13200 id = 305 }
      name  = "JDS 1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 13200 id = 306 }
      name  = "JDS 2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 13200 id = 307 }
      name  = "JDS 3rd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 13200 id = 101 }
    location = 1180
    base     = 1180
    name     = "Northern Air Defense Force"
    division =
    { id       = { type = 13200 id = 102 }
      name     = "2nd Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 103 }
      name     = "3rd Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 104 }
      name     = "4th Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 13200 id = 105 }
    location = 1180
    base     = 1180
    name     = "Central Air Defense Force"
    division =
    { id       = { type = 13200 id = 106 }
      name     = "5th Air Squadron"
      type     = interceptor
      strength = 65
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 107 }
      name     = "6th Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 108 }
      name     = "22nd Ground Strike Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 13200 id = 109 }
    location = 1180
    base     = 1180
    name     = "Tactical Airlift Command "
    division =
    { id       = { type = 13200 id = 110 }
      name     = "2nd Tactical Airlift Group"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 13200 id = 111 }
    location = 1190
    base     = 1190
    name     = "Central Naval Air Force"
    division =
    { id       = { type = 13200 id = 112 }
      name     = "4th Naval Squadron"
      type     = naval_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 13200 id = 113 }
      name     = "5th Naval Squadron"
      type     = naval_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 13200 id = 114 }
      name     = "2nd Naval Squadron"
      type     = naval_bomber
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 13200 id = 115 }
    location = 1190
    base     = 1190
    name     = "Western Air Defense Force"
    division =
    { id       = { type = 13200 id = 116 }
      name     = "27th Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 117 }
      name     = "25th Air Squadron"
      type     = interceptor
      strength = 65
      model    = 3
    }
    division =
    { id       = { type = 13200 id = 118 }
      name     = "23rd Air Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 13200 id = 119 }
    location = 1190
    base     = 1190
    name     = "5th Air Wing"
    division =
    { id       = { type = 13200 id = 120 }
      name     = "17th Air Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 13200 id = 121 }
      name     = "11th Air Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 13200 id = 122 }
      name     = "83rd Air Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 13200 id = 400 }
    name  = "JDS Takanami"
    type  = destroyer
    model = 3
    cost  = 5
    date  = { day = 4 month = october year = 2003 }
  }
  division_development =
  { id    = { type = 13200 id = 401 }
    name  = "JDS Onami"
    type  = destroyer
    model = 3
    cost  = 5
    date  = { day = 29 month = december year = 2003 }
  }
  division_development =
  { id    = { type = 13200 id = 402 }
    name  = "JDS Kuroshio"
    type  = submarine
    model = 4
    cost  = 5
    date  = { day = 14 month = april year = 2004 }
  }
  division_development =
  { id    = { type = 13200 id = 403 }
    name  = "JDS Takashio"
    type  = submarine
    model = 4
    cost  = 5
    date  = { day = 3 month = june year = 2005 }
  }
  division_development =
  { id    = { type = 13200 id = 404 }
    name  = "JDS Yaeshio"
    type  = submarine
    model = 4
    cost  = 5
    date  = { day = 20 month = march year = 2006 }
  }
  division_development =
  { id    = { type = 13200 id = 405 }
    name  = "JDS Setoshio"
    type  = submarine
    model = 4
    cost  = 5
    date  = { day = 21 month = august year = 2007 }
  }
}
