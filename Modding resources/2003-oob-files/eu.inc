
##############################
# Country definition for U06 #
##############################
country =
{ tag                 = U06
  capital             = 1884
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 1000
  oil                 = 1000
  supplies            = 1000
  money               = 5000
  manpower            = 0
  transports          = 100
  escorts             = 0
  diplomacy           = { 
    relation = { tag = BEL value = 200 access = yes }
    relation = { tag = CYN value = 150 access = yes }
    relation = { tag = CZE value = 150 access = yes }
    relation = { tag = DEN value = 200 access = yes }
    relation = { tag = EST value = 150 access = yes }
    relation = { tag = FRA value = 200 access = yes }
    relation = { tag = GRE value = 200 access = yes }
    relation = { tag = GER value = 200 access = yes }
    relation = { tag = HUN value = 150 access = yes }
    relation = { tag = ICL value = 150 }
    relation = { tag = ITA value = 200 access = yes }
    relation = { tag = LAT value = 150 access = yes }
    relation = { tag = LIT value = 150 access = yes }
    relation = { tag = LUX value = 200 access = yes }
    relation = { tag = HOL value = 200 access = yes }
    relation = { tag = NOR value = 150 }
    relation = { tag = POL value = 150 access = yes }
    relation = { tag = POR value = 200 access = yes }
    relation = { tag = ROM value = 100 }
    relation = { tag = SLO value = 150 access = yes }
    relation = { tag = SLV value = 150 access = yes }
    relation = { tag = SWE value = 150 access = yes }
    relation = { tag = FIN value = 150 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 100 }
    relation = { tag = ENG value = 150 access = yes }
 }
SpyInfo               = { country = "RUS" NumberOfSpies = 3 }
SpyInfo               = { country = "USA" NumberOfSpies = 2 }
SpyInfo               = { country = "PER" NumberOfSpies = 1 }
SpyInfo               = { country = "CHC" NumberOfSpies = 2 }
  nationalprovinces   = { 1884
                        }
  ownedprovinces      = { 1884
                        }
  controlledprovinces = { 1884
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2000 2010
					2150
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1980 1970
					1260 1270
					1000 1010
					1150
					1500 1510 1520 1530
					1200 1210 1220 1230
					1300 1310 1320 1330
					1400 1410 1420 1430
					1700 1710 1720
					1900 1910 1920 1930
					1800 1810 1820
					1600 1610
					1650 1660
					#Aircraft
					4100 4110 4120 4130
					4000 4010
					4640 4650 4660 4670
					4600 4610
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4400 4410
					4300 4310
					4900 4910 4920
					4500 4510
					#Land Docs
					6010 6030 6050 6070 6080
					6930
					6600 6620
					6700 6720
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9110 9120
					9130 9140 9150 9170 9190 9200
					9210
					9450 9460
					#Secret Weapons
					7010
					7020 7030 7040 7050
					7060 7070 7080
					7100 7110 7120
					7180 7190 7200
					7310 7320 7330
                                        #Navy Doctrines
                                        8900 8910 8920 8930
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020 8030
                                        8500 8510 8520 8530
                                        8100 8110 8120
                                        8600 8610 8620
                                        8200
                                        8700
                                        8300 8310 8320
                                        8800 8810 8820
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3100 3110 3120
                                        3400 3410 3420
                                        3590 3600
                                        3700 37700 3710 37710 3720
                                        3800 3810 38810 3820 38820
                                        3850 3860 3870 3880
                                        3900 3910 3920
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 9
    free_market       = 8
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 8
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12233 id = 1 }
    location = 316
    name     = "Franco-German Brigade"
    division =
    { id            = { type = 12233 id = 2 }
      name          = "Franco-German Brigade"
      strength      = 100
      type          = cavalry
      model         = 3
    }
  }
  landunit =
  { id       = { type = 12233 id = 3 }
    location = 310
    name     = "10. Panzer-Division"
    division =
    { id             = { type = 12233 id = 4 }
      name           = "10. Panzer-Division"
      strength       = 100
      type           = armor
      model          = 17
  }
}
  landunit =
  { id       = { type = 12233 id = 5 }
    location = 529
    name     = "Etat-Major de Force 2"
    division =
    { id            = { type = 12233 id = 6 }
      name          = "7ème Brigade Blindée"
      strength      = 100
      type          = light_armor
      model         = 11
    }
    division =
    { id            = { type = 12233 id = 7 }
      name          = "3ème Brigade Mecanisée"
      strength      = 100
      type          = cavalry
      model         = 3
    }
  }

  landunit =
  { id       = { type = 12233 id = 8 }
    location = 51
    name     = "Operational Command Land"
    division =
    { id            = { type = 12233 id = 9 }
      name          = "1 Brigade - 8/9 Ligne"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 12233 id = 10 }
      name          = "7 Brigade - 2 Chasseurs à pied"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12233 id = 11 }
    location = 338
    name     = "1st Mechanized Army"
    division =
    { id       = { type = 12233 id = 12 }
      name     = "8th Cavalry Regiment"
      strength = 100
      type     = light_armor
      model    = 8
    }
    division =
    { id       = { type = 12233 id = 13 }
      name     = "12th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12233 id = 14 }
    location = 308
    name     = "17th Mechanized Brigade"
    division =
    { id            = { type = 12233 id = 15 }
      name          = "17 Wielkopolska BZ im. gen. broni Józefa Dowbor-Musnickiego"
      strength      = 100
      type          = cavalry
      model         = 1
    }
}
}