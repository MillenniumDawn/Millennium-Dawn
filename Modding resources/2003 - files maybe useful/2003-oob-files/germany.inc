
##############################
# Country definition for GER #
##############################

province =
{ id         = 90
  naval_base = { size = 10 current_size = 10 }
    air_base = { size = 4 current_size = 4 }
}              # Kiel

province =
{ id         = 74
  air_base = { size = 10 current_size = 10 }
}              # Saarbrücken/Rammstein

province =
{ id         = 300
 rocket_test = { size = 2 current_size = 2 }
}              # Berlin

country =
{ tag                 = GER
  regular_id          = U06
  capital             = 300
  manpower            = 60
  transports          = 142
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 300
  # NATO
  diplomacy =
  { relation = { tag = BEL value = 200 access = yes }
    relation = { tag = BUL value = 200 access = yes }
    relation = { tag = CAN value = 200 access = yes }
    relation = { tag = CZE value = 200 access = yes }
    relation = { tag = DEN value = 200 access = yes }
    relation = { tag = EST value = 200 access = yes }
    relation = { tag = FRA value = 200 access = yes }
    relation = { tag = USA value = 200 access = yes }
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
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 66 67 74 75 76 80 81 82 83 84 85 86 87 88 89 90 296 297 298 299 300 301 309 310 311 312 313 314 315 374 375 376 }
  ownedprovinces      = { 66 67 74 75 76 80 81 82 83 84 85 86 87 88 89 90 296 297 298 299 300 301 309 310 311 312 313 314 315 374 375 376 }
  controlledprovinces = { 66 67 74 75 76 80 81 82 83 84 85 86 87 88 89 90 296 297 298 299 300 301 309 310 311 312 313 314 315 374 375 376 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1260 1270
					1900 1910 1920 1930
					1500 1510 1520 1530
					1200 1210 1220 1230
					1300 1310 1320 1330
					1400 1410 1420 1430
					1700 1710 1720
					1800 1810 1820
					1000 1010
					1050 1060 1070
					1110 1120
					#Aircraft
                                        4100 4110 4120 4130
					4640 4650 4660 4670
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4500 4510 4520
                                        4570
					4400 4410 4420
					4900 4910 4920					
					#Land Docs
					6010 6030 6040
					6930
					6600 6610
					6700 6710
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					6300 6310 6320 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9120
					9130 9140 9150 9170 9200
					9210 9220 9230 9250 9280
					#Secret Weapons
					7010 7060 7070 7080
					7180 7190 7200
					7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020
                                        3100 3110 3120
                                        3590
                                        3700 37700 3710 37710 3720 3730
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 7
    free_market       = 8
    freedom           = 10
    professional_army = 2
    defense_lobby     = 2
    interventionism   = 4
  }
# #####################################
# ARMY
# #####################################

landunit =
{ id = { type = 11100 id = 1 }
location = 86
name = "II. Korps"
division =
{ id = { type = 11100 id = 2 }
name = "11. Panzergrenadier-Division"
strength = 100
type = infantry
model = 3
}
division =
{ id = { type = 11100 id = 3 }
name = "7. Panzer-Division"
strength = 100
type = armor
model = 15
}
}
landunit =
{ id = { type = 11100 id = 4 }
location = 75
name = "I. Korps"
division =
{ id = { type = 11100 id = 5 }
name = "1. Panzer-Division"
strength = 100
type = armor
model = 16
extra = heavy_armor
brigade_model = 1
}
division =
{ id = { type = 11100 id = 6 }
name = "3. Panzer-Division"
strength = 100
type = armor
model = 16
}
}
landunit =
{ id = { type = 11100 id = 7 }
location = 374
name = "V. Korps"
division =
{ id = { type = 11100 id = 8 }
name = "Gebirgsjäger-Brigade 23"
strength = 100
type = bergsjaeger
model = 14
}
}
landunit =
{ id = { type = 11100 id = 10 }
location = 310
name = "III. Korps"
division =
{ id = { type = 11100 id = 11 }
name = "4. Panzergrenadier-Division"
strength = 100
type = infantry
model = 3
}
division =
{ id = { type = 11100 id = 12 }
name = "Jäger-Brigade 37"
strength = 100
type = mechanized
model = 3
}
division =
{ id = { type = 11100 id = 14 }
name = "12. Panzer-Division"
strength = 100
type = armor
model = 16
}
}
landunit =
{ id = { type = 11100 id = 15 }
location = 301
name = "IV. Korps"
division =
{ id = { type = 11100 id = 16 }
name = "5. Panzer-Division"
strength = 100
type = armor
model = 16
}
division =
{ id = { type = 11100 id = 17 }
name = "2. Panzergrenadier-Division"
strength = 100
type = infantry
model = 3
extra = heavy_armor
brigade_model = 1
}
division =
{ id = { type = 11100 id = 18 }
name = "6. Panzergrenadier-Division"
strength = 100
type = infantry
model = 3
}
}
landunit =
{ id = { type = 11100 id = 19 }
location = 375
name = "Division Spezielle Operationen"
division =
    { experience    = 15
            id = { type = 11100 id = 20 }
          name = "Kommando Spezialkräfte"
      strength = 100
          type = bergsjaeger
         model = 14
         extra = engineer
 brigade_model = 0
}
division =
{ id = { type = 11100 id = 21 }
name = "Luftlande-Brigade 26"
strength = 100
type = paratrooper
model = 16
}
division =
{ id = { type = 11100 id = 22 }
name = "Luftlande-Brigade 31"
strength = 100
type = paratrooper
model = 16
}
}
landunit =
{ id = { type = 11100 id = 23 }
location = 86
name = "Division Luftbewegliche Operationen"
division =
{ id = { type = 11100 id = 24 }
name = "Luftmechanisierte-Brigade 1"
strength = 100
type = militia
model = 3
}
division =
{ id = { type = 11100 id = 25 }
name = "Heerestruppen-Brigade"
strength = 100
type = militia
model = 3
}
}
# #####################################
# NAVY
# #####################################
navalunit =
{ id = { type = 11100 id = 200 }
location = 90
base = 90
name = "1. Fregatten-Geschwader"
division =
{ id = { type = 11100 id = 201 }
name = "FGS Lütjens"
type = light_cruiser
model = 0
}
division =
{ id = { type = 11100 id = 202 }
name = "FGS Mölders"
type = light_cruiser
model = 0
}
}
navalunit =
{ id = { type = 11100 id = 203 }
location = 90
base = 90
name = "6. Fregatten-Geschwader"
division =
{ id = { type = 11100 id = 204 }
name = "FGS Brandenburg"
type = destroyer
model = 2
}
division =
{ id = { type = 11100 id = 205 }
name = "FGS Schleswig-Holstein"
type = destroyer
model = 2
}
division =
{ id = { type = 11100 id = 206 }
name = "FGS Bayern"
type = destroyer
model = 2
}
division =
{ id = { type = 11100 id = 207 }
name = "FGS Mecklenburg-Vorpommern"
type = destroyer
model = 2
}
}
navalunit =
{ id = { type = 11100 id = 208 }
location = 90
base = 90
name = "2. Fregatten-Geschwader"
division =
{ id = { type = 11100 id = 209 }
name = "FGS Bremen"
type = destroyer
model = 1
}
division =
{ id = { type = 11100 id = 210 }
name = "FGS Niedersachsen"
type = destroyer
model = 1
}
division =
{ id = { type = 11100 id = 211 }
name = "FGS Rheinland-Pfalz"
type = destroyer
model = 1
}
division =
{ id = { type = 11100 id = 212 }
name = "FGS Emden"
type = destroyer
model = 1
}
}
navalunit =
{ id = { type = 11100 id = 213 }
location = 90
base = 90
name = "4. Fregatten-Geschwader"
division =
{ id = { type = 11100 id = 214 }
name = "FGS Köln"
type = destroyer
model = 0
}
division =
{ id = { type = 11100 id = 215 }
name = "FGS Karlsruhe"
type = destroyer
model = 0
}
division =
{ id = { type = 11100 id = 216 }
name = "FGS Augsburg"
type = destroyer
model = 0
}
division =
{ id = { type = 11100 id = 217 }
name = "FGS Lübeck"
type = destroyer
model = 0
}
}
navalunit =
{ id = { type = 11100 id = 218 }
location = 90
base = 90
name = "1. Uboot-Geschwader"
division =
{ id = { type = 11100 id = 219 }
name = "FGS U23"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 220 }
name = "FGS U25"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 221 }
name = "FGS U28"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 222 }
name = "FGS U33"
type = submarine
model = 3
}
}
navalunit =
{ id = { type = 11100 id = 223 }
location = 90
base = 90
name = "3. Uboot-Geschwader"
division =
{ id = { type = 11100 id = 224 }
name = "FGS U15"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 225 }
name = "FGS U16"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 226 }
name = "FGS U24"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 227 }
name = "FGS U26"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 228 }
name = "FGS U27"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 229 }
name = "FGS U28"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 230 }
name = "FGS U29"
type = submarine
model = 3
}
division =
{ id = { type = 11100 id = 231 }
name = "FGS U30"
type = submarine
model = 3
}
}
# #####################################
# AIR FORCE
# #####################################
airunit =
{ id = { type = 11100 id = 100 }
location = 74
base = 74
name = "1. Luftwaffendivision"
division =
{ id = { type = 11100 id = 101 }
name = "Jagdbombergeschwader 32"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 102 }
name = "Jagdbombergeschwader 34"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 103 }
name = "Jagdgeschwader 74"
type = multi_role
strength = 100
model = 1
}
}
airunit =
{ id = { type = 11100 id = 104 }
location = 90
base = 90
name = "2. Luftwaffendivision"
division =
{ id = { type = 11100 id = 105 }
name = "Jagdbombergeschwader 33"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 106 }
name = "Jagdbombergeschwader 35"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 107 }
name = "Jagdgeschwader 31 'Boelcke'"
type = multi_role
strength = 100
model = 1
}
}
airunit =
{ id = { type = 11100 id = 108 }
location = 90
base = 90
name = "3. Luftwaffendivision"
division =
{ id = { type = 11100 id = 109 }
name = "Jagdgeschwader 73 'Steinhoff'"
type = multi_role
strength = 100
model = 1
}
division =
{ id = { type = 11100 id = 110 }
name = "Jagdgeschwader 79"
type = multi_role
strength = 100
model = 1
}
}
airunit =
{ id = { type = 11100 id = 111 }
location = 74
base = 74
name = "4. Luftwaffendivision"
division =
{ id = { type = 11100 id = 112 }
name = "Jagdbombergeschwader 38"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 113 }
name = "Jagdbombergeschwader 37"
type = tactical_bomber
strength = 100
model = 3
}
division =
{ id = { type = 11100 id = 114 }
name = "Jagdgeschwader 71 'Richthofen'"
type = multi_role
strength = 100
model = 1
}
}
airunit =
{ id = { type = 11100 id = 115 }
location = 74
base = 74
name = "Luftransport Kommando"
division =
{ id = { type = 11100 id = 116 }
name = "Lufttransportgeschwader 61"
type = transport_plane
strength = 100
model = 1
}
division =
{ id = { type = 11100 id = 117 }
name = "Lufttransportgeschwader 62"
type = transport_plane
strength = 100
model = 1
}
}
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 11100 id = 300 }
    name  = "FGS Sachsen"
    type  = light_cruiser
    model = 2
    cost  = 4
    date  = { day = 9 month = august year = 2003 }
  }
  division_development =
  { id    = { type = 11100 id = 301 }
    name  = "FGS U31"
    type  = submarine
    model = 6
    cost  = 7
    date  = { day = 28 month = november year = 2003 }
  }
  division_development =
  { id    = { type = 11100 id = 302 }
    name  = "FGS Hamburg"
    type  = light_cruiser
    model = 2
    cost  = 4
    date  = { day = 14 month = march year = 2004 }
  }
  division_development =
  { id    = { type = 11100 id = 303 }
    name  = "FGS U32"
    type  = submarine
    model = 6
    cost  = 7
    date  = { day = 13 month = june year = 2004 }
  }
  division_development =
  { id    = { type = 11100 id = 304 }
    name  = "FGS Hessen"
    type  = light_cruiser
    model = 2
    cost  = 4
    date  = { day = 19 month = june year = 2005 }
  }
  division_development =
  { id    = { type = 11100 id = 305 }
    name  = "FGS U33"
    type  = submarine
    model = 6
    cost  = 7
    date  = { day = 4 month = september year = 2005 }
  }
  division_development =
  { id    = { type = 11100 id = 306 }
    name  = "FGS U34"
    type  = submarine
    model = 6
    cost  = 7
    date  = { day = 17 month = may year = 2006 }
  }
}
