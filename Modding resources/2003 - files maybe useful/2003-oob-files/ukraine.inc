
##############################
# Country definition for UKR #
##############################

province =
{ id       = 253
  naval_base = { size = 10 current_size = 10 }
}            # Sevastopol

province =
{ id       = 238
  air_base = { size = 4 current_size = 4 }
}            # Kiev

province =
{ id       = 254
  air_base = { size = 4 current_size = 4 }
}            # Kerch

country =
{ tag                 = UKR
  regular_id          = RUS
  manpower            = 70
  transports          = 50
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 238
  diplomacy           = { 
                         relation = { tag = RUS value = 150 } 
                        }
  nationalprovinces   = { 1888 260 227 228 229 231 232 233 234 235 236 237 238 239 242 244 245 246 248 249 250 251 252 253 254 499 500 501 502 506 435 }
  ownedprovinces      = { 1888 260 227 228 229 231 232 233 234 235 236 237 238 239 242 244 245 246 248 249 250 251 252 253 254 499 500 501 502 506 435 }
  controlledprovinces = { 1888 260 227 228 229 231 232 233 234 235 236 237 238 239 242 244 245 246 248 249 250 251 252 253 254 499 500 501 502 506 435 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220
					2300 2310 2320
					2400 2410 2420
					2500 2510 2520
					2600 2610 2620
					2700 2710 2720
					2800 2810 2820
					2000 2010
					2050 2060 2070
					2110 2120
					#Army Org
					1990
					1260 1270
					1900 1910 1920
					1800 1810
					1500 1510 1520
					1400 1410 1420
					1300 1310 1320
					1200 1210 1220
					1000 1010
					1050 1060
					1110
					#Aircraft
					4800 4810
					4700 4710
					4750 4760
					4400 4410 4420
					4900
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Air Docs
					9010 9510
					9050 9060 9070 9120
					#Secret Weapons
					7010 7060 7070
					7310 7330
                                        #Navy Techs
                                        3000 3010 3020
                                        3100 3110 3120
                                        3200 3210
                                        3590
                                        3500 3510 3520
                                        3700 37700 3710 37710
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
    democratic        = 7
    political_left    = 6
    free_market       = 5
    freedom           = 5
    professional_army = 2
    defense_lobby     = 4
    interventionism   = 5
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 22100 id = 1 }
    location = 501
    name     = "6th Army Corps"
    division =
    { id            = { type = 22100 id = 2 }
      name          = "6th Army Corps HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 22100 id = 3 }
      name          = "17th Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 22100 id = 4 }
      name          = "25th Airborne Brigade"
      strength      = 100
      type          = paratrooper
      model         = 14
    }
    division =
    { id            = { type = 22100 id = 5 }
      name          = "79th Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 6 }
      name          = "28th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 7 }
      name          = "92nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 8 }
      name          = "93rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22100 id = 9 }
    location = 233
    name     = "8th Army Corps"
    division =
    { id            = { type = 22100 id = 10 }
      name          = "8th Army Corps HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 22100 id = 11 }
      name          = "30th Tank Division"
      strength      = 100
      type          = armor
      model         = 12
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 22100 id = 12 }
      name          = "1st Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 5
    }
    division =
    { id            = { type = 22100 id = 13 }
      name          = "66th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 14 }
      name          = "72nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 15 }
      name          = "95th Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22100 id = 16 }
    location = 253
    name     = "13th Army Corps"
    division =
    { id            = { type = 22100 id = 17 }
      name          = "13th Army Corps HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 22100 id = 18 }
      name          = "24th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 19 }
      name          = "51st Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 22100 id = 20 }
      name          = "128th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 22100 id = 200 }
    location = 253
    base     = 253
    name     = "1st Fleet"
    division =
    { id    = { type = 22100 id = 201 }
      name  = "Hetman Sahayadachniy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22100 id = 202 }
      name  = "Sevastopol"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22100 id = 203 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 22100 id = 204 }
      name  = "U01 Zaporizhzhia"
      type  = submarine
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 22100 id = 100 }
    location = 254
    base     = 254
    name     = "Lviv Aviation Corps 1"
    division =
    { id       = { type = 22100 id = 101 }
      name     = "7th Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22100 id = 102 }
      name     = "8th Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22100 id = 103 }
      name     = "12th Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22100 id = 104 }
      name     = "17th Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 22100 id = 105 }
    location = 238
    base     = 238
    name     = "Kiev Aviation Corps 1"
    division =
    { id       = { type = 22100 id = 106 }
      name     = "3rd Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 107 }
      name     = "16th Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 108 }
      name     = "14th Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 22100 id = 109 }
    location = 238
    base     = 238
    name     = "Kiev Aviation Corps 2"
    division =
    { id       = { type = 22100 id = 110 }
      name     = "21st Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 111 }
      name     = "42nd Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 112 }
      name     = "19th Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 22100 id = 113 }
    location = 238
    base     = 238
    name     = "Lviv Aviation Corps 2"
    division =
    { id       = { type = 22100 id = 114 }
      name     = "1st Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22100 id = 115 }
      name     = "2nd Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22100 id = 116 }
      name     = "3rd Fighter-Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 22100 id = 117 }
    location = 238
    base     = 238
    name     = "Odessa Aviation Corps 1"
    division =
    { id       = { type = 22100 id = 118 }
      name     = "1st Fighter Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 119 }
      name     = "2nd Fighter Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 120 }
      name     = "9th Fighter Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 22100 id = 121 }
    location = 238
    base     = 238
    name     = "Odessa Aviation Corps 2"
    division =
    { id       = { type = 22100 id = 122 }
      name     = "77th Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 123 }
      name     = "22nd Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 22100 id = 124 }
      name     = "18th Fighter Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 22100 id = 125 }
    location = 254
    base     = 254
    name     = "1st Transport Air Division"
    division =
    { id       = { type = 22100 id = 126 }
      name     = "1st Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
