
##############################
# Country definition for TUR #
##############################

province =
{ id       = 1811
  naval_base = { size = 10 current_size = 10 }
}            # Izmir

province =
{ id       = 439
  naval_base = { size = 10 current_size = 10 }
}            # Izmit

province =
{ id         = 1854
  air_base = { size = 6 current_size = 6 }
}              # Diryabakir


province =
{ id         = 408
  air_base = { size = 10 current_size = 10 }
}              # Bursa

country =
{ tag                 = TUR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  capital             = 1623
  manpower            = 85
  transports          = 120
  escorts             = 0
  # NATO
  diplomacy =
  { relation = { tag = BEL value = 200 access = yes }
    relation = { tag = BUL value = 200 access = yes }
    relation = { tag = CAN value = 200 access = yes }
    relation = { tag = CZE value = 200 access = yes }
    relation = { tag = DEN value = 200 access = yes }
    relation = { tag = EST value = 200 access = yes }
    relation = { tag = FRA value = 200 access = yes }
    relation = { tag = GER value = 200 access = yes }
    relation = { tag = GRE value = 200 access = yes }
    relation = { tag = HUN value = 200 access = yes }
    relation = { tag = ICL value = 200 access = yes }
    relation = { tag = ITA value = 200 access = yes }
    relation = { tag = LAT value = 200 access = yes }
    relation = { tag = LIT value = 200 access = yes }
    relation = { tag = LUX value = 200 access = yes }
    relation = { tag = HOL value = 200 access = yes }
    relation = { tag = NOR value = 200 access = yes }
    relation = { tag = POL value = 200 access = yes }
    relation = { tag = POR value = 200 access = yes }
    relation = { tag = ROM value = 200 access = yes }
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = USA value = 100 }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 1810 1811 1779 1623 409 408 437 438 439 441 442 443 448 440 449 447 446 445 450 1851 1852 1853 1854 1855 444 }
  ownedprovinces      = { 1810 1811 1779 1623 409 408 437 438 439 441 442 443 448 440 449 447 446 445 450 1851 1852 1853 1854 1855 }
  controlledprovinces = { 1810 1811 1779 1623 409 408 437 438 439 441 442 443 448 440 449 447 446 445 450 1851 1852 1853 1854 1855 }
  techapps            = {
                                        #Industry:
                                        5010 5110 5210
                                        5020 5120 5220
                                        5030 5130 5230
                                        5040 5140 5240
                                        5050 5150
                                        5060 5160
                                        5070 5170 5270
                                        5080 5180 5280
                                        5090 5190 5290
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
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6120 6220
                                        6130
                                        6140
                                        6160 6260
                                        6170 6270
                                        6010 6030
                                        6040
                                        6910 6920 6930
                                        6600
                                        6620
                                        #Air Force:
                                        4100 4110
                                        4000 4010 4020 4030
                                        4400
                                        4640 4650
                                        4700 4710 4720
                                        4750 4760 4770
                                        #Air Force Doctrines:
                                        9050 9130
                                        9060 9140
                                        9070 9150
                                        9090
                                        9110 9190
                                        9120 9200
                                        9020
                                        9510 9520
                                        #Navy Techs
                                        3000 3010 3020
                                        3100
                                        3700 3710 37710
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110
                                        8600 8610
                                        #Secret Techs
                                        7330 7310

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 7
    political_left    = 3
    free_market       = 6
    freedom           = 5
    professional_army = 8
    defense_lobby     = 5
    interventionism   = 6
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 21800 id = 1 }
    location = 409
    name     = "First Army"
    division =
    { id            = { type = 21800 id = 2 }
      name          = "1st Army HQ"
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 21800 id = 3 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 21800 id = 4 }
      name          = "5th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 3
    }
    division =
    { id       = { type = 21800 id = 5 }
      name     = "3rd Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 6 }
      name     = "4th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 7 }
      name     = "5th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 8 }
      name     = "7th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 9 }
      name     = "8th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 10 }
      name     = "9th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 21800 id = 11 }
    location = 1854
    name     = "Second Army"
    division =
    { id            = { type = 21800 id = 12 }
      name          = "8th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 3
    }
    division =
    { id            = { type = 21800 id = 13 }
      name          = "9th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 7
    }
    division =
    { id       = { type = 21800 id = 14 }
      name     = "10th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 15 }
      name     = "11th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 16 }
      name     = "12th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 17 }
      name     = "14th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 18 }
      name     = "7th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 19 }
      name     = "8th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 21800 id = 20 }
    location = 1851
    name     = "Third Army"
    division =
    { id            = { type = 21800 id = 21 }
      name          = "3rd Army HQ"
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 21800 id = 22 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 21800 id = 23 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 21800 id = 24 }
      name          = "4th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21800 id = 25 }
      name     = "15th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 21800 id = 26 }
      name     = "16th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id            = { type = 21800 id = 27 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 21800 id = 28 }
      name     = "6th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 21800 id = 29 }
    location = 437
    name     = "Aegean Army"
    division =
    { id            = { type = 21800 id = 30 }
      name          = "Aegean Army HQ"
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 21800 id = 31 }
      name     = "2nd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 32 }
      name     = "3rd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 33 }
      name     = "4th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 34 }
      name     = "5th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id            = { type = 21800 id = 35 }
      name          = "6th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 21800 id = 36 }
      name          = "7th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21800 id = 37 }
      name     = "1st Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id            = { type = 21800 id = 38 }
      name          = "2nd Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 21800 id = 39 }
    location = 940
    name     = "Cyprus Turkish Peace Force"
    division =
    { id       = { type = 21800 id = 40 }
      name     = "28th Infantry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 41 }
      name     = "39th Infantry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 21800 id = 42 }
    location = 1779
    name     = "1st Commando Corps"
    division =
    { id       = { type = 21800 id = 43 }
      name     = "1st Para-Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 21800 id = 44 }
      name     = "2nd Para-Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 21800 id = 45 }
      name     = "3rd Para-Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 21800 id = 46 }
      name     = "4th Para-Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 21800 id = 47 }
      name     = "5th Para-Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 21800 id = 200 }
    location = 439
    base     = 439
    name     = "Northern Area Surface Command"
    division =
    { id    = { type = 21800 id = 201 }
      name  = "TCG Barbados"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21800 id = 202 }
      name  = "TCG Orucreis"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21800 id = 203 }
      name  = "TCG Gaziantep"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 204 }
      name  = "TCG Giresun"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 205 }
      name  = "TCG Gemlik"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 206 }
      name  = "TCG Geliboli"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 207 }
      name  = "TCG Gokceada"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 208 }
      name  = "TCG Gediz"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 209 }
      name  = "TCG Muavenet"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21800 id = 210 }
      name  = "TCG Zafer"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21800 id = 214 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 1
    }
    division =
    { id    = { type = 21800 id = 215 }
      name  = "4th Transport Fleet"
      type  = transport
      model = 1
    }
  }
  navalunit =
  { id       = { type = 21800 id = 217 }
    location = 439
    base     = 439
    name     = "Northern Area Submarine Command"
    division =
    { id    = { type = 21800 id = 218 }
      name  = "TCG Atilay"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 219 }
      name  = "TCG Saldiray"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 220 }
      name  = "TCG Batiray"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 221 }
      name  = "TCG Yildiray"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 222 }
      name  = "TCG Doganay"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 223 }
      name  = "TCG Dolunay"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 21800 id = 224 }
      name  = "TCG Preveze"
      type  = submarine
      model = 3
    }
  }
  navalunit =
  { id       = { type = 21800 id = 225 }
    location = 1811
    base     = 1811
    name     = "Southern Surface Command"
    division =
    { id    = { type = 21800 id = 226 }
      name  = "TCG Salihreis"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21800 id = 227 }
      name  = "TCG Kemalreis"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 21800 id = 228 }
      name  = "TCG Gokova"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 229 }
      name  = "TCG Goksu"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 230 }
      name  = "TCG Yavuz"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 231 }
      name  = "TCG Turgutreis"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 232 }
      name  = "TCG Fatih"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 233 }
      name  = "TCG Yildirim"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21800 id = 234 }
      name  = "TCG Karadeniz"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21800 id = 235 }
      name  = "TCG Ege"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21800 id = 239 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 21800 id = 242 }
    location = 1811
    base     = 1811
    name     = "Southern Area Submarine Command"
    division =
    { id    = { type = 21800 id = 243 }
      name  = "TCG Sakarya"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 244 }
      name  = "TCG 18 Mart"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 245 }
      name  = "TCG Anafartalar"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 246 }
      name  = "TCG Gur"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 247 }
      name  = "TCG Canakkale"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 248 }
      name  = "TCG Burakreis"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 21800 id = 249 }
      name  = "TCG Birinci Inonu"
      type  = submarine
      model = 3
    }
  }
  # ################################################
  # AIR FORCE
  # ####################################################
  # ##########
  airunit =
  { id       = { type = 21800 id = 100 }
    location = 1854
    base     = 1854
    name     = "Ankara AFB"
    division =
    { id       = { type = 21800 id = 101 }
      name     = "4nci AJU"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 102 }
      name     = "12nci AJU"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 103 }
      name     = "7nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 21800 id = 104 }
    location = 408
    base     = 408
    name     = "Balikesir AFB"
    division =
    { id       = { type = 21800 id = 105 }
      name     = "9nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 21800 id = 106 }
      name     = "6nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 21800 id = 107 }
      name     = "8nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 21800 id = 108 }
    location = 408
    base     = 408
    name     = "Istanbul AFB"
    division =
    { id       = { type = 21800 id = 109 }
      name     = "5nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 21800 id = 110 }
      name     = "10nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 21800 id = 111 }
      name     = "11nci AJU"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 21800 id = 112 }
    location = 1854
    base     = 1854
    name     = "Konya AFB"
    division =
    { id       = { type = 21800 id = 113 }
      name     = "18nci AEJU"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 114 }
      name     = "16nci AJU"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 115 }
      name     = "17nci AJU"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 21800 id = 116 }
    location = 408
    base     = 408
    name     = "Izmir AFB"
    division =
    { id       = { type = 21800 id = 117 }
      name     = "19nci AJU"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21800 id = 118 }
      name     = "13nci AJU"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
}
