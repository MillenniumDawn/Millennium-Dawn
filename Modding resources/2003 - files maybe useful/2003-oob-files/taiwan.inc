
##############################
# Country definition for TRA #
##############################

province =
{ id       = 1323
  naval_base = { size = 10 current_size = 10 }
    air_base = { size = 8 current_size = 8 }
}            # Taipei

country =
{ tag                 = TRA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  manpower            = 60
  capital             = 1323
  transports          = 100
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1681 1322 1323 1324 }
  ownedprovinces      = { 1681 1322 1323 1324 }
  controlledprovinces = { 1681 1322 1323 1324 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2800 2810 2820 2830
					2600 2610 2620 2630
					2700 2710 2720 2730
					2400 2410 2420 2430
					2300 2310
					2000 2010
					2500 2510 2520 2530
					#Army Org
					1900 1910 1920 1930
					1260 1270
					1700
					1800 1810 1820
					1000 1010
					1500 1510
					1200 1210
					1300 1310 1320 1330
					1400 1410 1420 1430
					1600 1650
					#Aircraft
                                        4100 4110 4120
                                        4000 4010 4020
                                        4400 4410
					4640
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910 4920
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9100 9110 9120
					9130 9140 9150 9180 9190 9200
					#Secret Weapons
					7010 7060 7070 7080
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3100
                                        3700 3710
                                        3590
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 6
    free_market       = 7
    freedom           = 8
    professional_army = 5
    defense_lobby     = 4
    interventionism   = 5
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 21000 id = 1 }
    location = 1323
    name     = "Aviation and Special Forces Command"
    division =
    { experience    = 10
      id            = { type = 21000 id = 2 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 21000 id = 3 }
      name          = "1st Air Cavalry Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 4 }
      name          = "2nd Air Cavalry Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 5 }
      name          = "3rd Air Cavalry Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
 landunit =
  { id       = { type = 21000 id = 6 }
    location = 1323
    name     = "Marine Command"
    division =
    { id            = { type = 21000 id = 7 }
      name          = "66th Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
    division =
    { id            = { type = 21000 id = 8 }
      name          = "77th Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
    division =
    { id            = { type = 21000 id = 9 }
      name          = "99th Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
  }
  landunit =
  { id       = { type = 21000 id = 10 }
    location = 1323
    name     = "6th Army Corps"
    division =
    { id            = { type = 21000 id = 11 }
      name          = "Republic of China Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 21000 id = 12 }
      name          = "1st Armoured Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 13 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 14 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21000 id = 15 }
      name     = "3rd Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 21000 id = 16 }
    location = 1322
    name     = "8th Army Corps"
    division =
    { id            = { type = 21000 id = 17 }
      name          = "2nd Armored Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 18 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21000 id = 19 }
      name     = "4th Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 21000 id = 20 }
    location = 1324
    name     = "10th Army Corps"
    division =
    { id            = { type = 21000 id = 21 }
      name          = "3rd Armored Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 21000 id = 22 }
      name          = "4th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21000 id = 23 }
      name     = "5th Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 21000 id = 24 }
    location = 1681
    name     = "Hua-Tung Defense Command"
    division =
    { id       = { type = 21000 id = 25 }
      name     = "1st Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
    division =
    { id       = { type = 21000 id = 26 }
      name     = "2nd Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
  }
  landunit =
  { id       = { type = 21000 id = 27 }
    location = 1681
    name     = "Kinmen Defense Command"
    division =
    { id       = { type = 21000 id = 28 }
      name     = "3rd Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
    division =
    { id       = { type = 21000 id = 29 }
      name     = "4th Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
    division =
    { id       = { type = 21000 id = 30 }
      name     = "5th Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
    division =
    { id            = { type = 21000 id = 31 }
      name          = "5th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
      locked = yes
    }
  }
  landunit =
  { id       = { type = 21000 id = 32 }
    location = 1681
    name     = "Matzu Defense Command"
    division =
    { id       = { type = 21000 id = 33 }
      name     = "6th Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
    division =
    { id       = { type = 21000 id = 34 }
      name     = "7th Infantry Brigade"
      strength = 100
      type     = garrison
      model    = 7
      locked = yes
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 21000 id = 200 }
    location = 1323
    base     = 1323
    name     = "124th Attack Squadron"
    division =
    { id    = { type = 21000 id = 201 }
      name  = "Kang Ding"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 21000 id = 203 }
      name  = "Si Ning"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 21000 id = 204 }
      name  = "Wu Chang"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 21000 id = 205 }
      name  = "Di Hua"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 21000 id = 206 }
      name  = "Kun Ming"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 21000 id = 207 }
      name  = "Cheng Du"
      type  = destroyer
      model = 3
    }
  }
  navalunit =
  { id       = { type = 21000 id = 208 }
    location = 1323
    base     = 1323
    name     = "146th Attack Squadron"
    division =
    { id    = { type = 21000 id = 209 }
      name  = "Cheng Kung"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 210 }
      name  = "Cheng Ho"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 211 }
      name  = "Chi Kuang"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 212 }
      name  = "Yueh Fei"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 213 }
      name  = "Tzu I"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 214 }
      name  = "Pan Chao"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 215 }
      name  = "Chang Chien"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21000 id = 216 }
      name  = "Tian Dan"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 21000 id = 217 }
    location = 1323
    base     = 1323
    name     = "131st Patrol Squadron"
    division =
    { id    = { type = 21000 id = 218 }
      name  = "Chien Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 219 }
      name  = "Liao Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 220 }
      name  = "Shao Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 221 }
      name  = "Te Yang"
      type  = light_cruiser
      model = 0
    }
  }
  navalunit =
  { id       = { type = 21000 id = 234 }
    location = 1323
    base     = 1323
    name     = "168th Patrol Squadron"
    division =
    { id    = { type = 21000 id = 235 }
      name  = "Chen Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 236 }
      name  = "Shen Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 237 }
      name  = "Yun Yang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 21000 id = 238 }
      name  = "Chi Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 239 }
      name  = "Fong Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 240 }
      name  = "Fen Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 241 }
      name  = "Lan Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 242 }
      name  = "Hae Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 243 }
      name  = "Hwai Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 244 }
      name  = "Ning Yang"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21000 id = 245 }
      name  = "Yi Yang"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 21000 id = 246 }
    location = 1323
    base     = 1323
    name     = "27th Amphibious Squadron"
    division =
    { id    = { type = 21000 id = 247 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 21000 id = 251 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 21000 id = 256 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 21000 id = 100 }
    location = 1323
    base     = 1323
    name     = "401th Tactical Fighter Wing"
    division =
    { id       = { type = 21000 id = 101 }
      name     = "367th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 102 }
      name     = "345th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 103 }
      name     = "382nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 21000 id = 104 }
    location = 1323
    base     = 1323
    name     = "427th Tactical Fighter Wing"
    division =
    { id       = { type = 21000 id = 105 }
      name     = "288th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 106 }
      name     = "210th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 107 }
      name     = "233rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 21000 id = 108 }
    location = 1323
    base     = 1323
    name     = "443rd Tactical Fighter Wing"
    division =
    { id       = { type = 21000 id = 109 }
      name     = "109th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 110 }
      name     = "55th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 111 }
      name     = "173rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 21000 id = 112 }
    location = 1323
    base     = 1323
    name     = "455th Tactical Fighter Wing"
    division =
    { id       = { type = 21000 id = 113 }
      name     = "453rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 114 }
      name     = "432nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 115 }
      name     = "499th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 21000 id = 116 }
    location = 1323
    base     = 1323
    name     = "737th Tactical Fighter Wing"
    division =
    { id       = { type = 21000 id = 117 }
      name     = "444th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21000 id = 118 }
      name     = "421st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21000 id = 119 }
      name     = "427th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 21000 id = 120 }
    location = 1323
    base     = 1323
    name     = "1st Transport Wing"
    division =
    { id       = { type = 21000 id = 121 }
      name     = "1st Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
