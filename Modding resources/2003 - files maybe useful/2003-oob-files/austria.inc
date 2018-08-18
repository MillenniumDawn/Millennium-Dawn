
##############################
# Country definition for AUS #
##############################

province =
{ id       = 463
  air_base = { size = 2 current_size = 2 }
}            # Vienna

country =
{ tag                 = AUS
  regular_id          = U06
  manpower            = 15
  capital             = 463
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  diplomacy           = { }
  nationalprovinces   = { 373 377 460 461 462 463 464 465 }
  ownedprovinces      = { 373 377 460 461 462 463 464 465 }
  controlledprovinces = { 373 377 460 461 462 463 464 465 }
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
					2400 2410 2420 2430
					2300 2310 2320 2330
                                        2500 2510 2520 2530
					2600 2610 2620 2630
                                        2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1960
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
					1900 1910 1920 1930
					1260 1270
					1300 1310 1320 1330
                                        1500 1510 1520 1530
					#Aircraft
					4800 4810 4820
					4750 4760 4770
					4700 4710 4720
					4900 4910
                                        4100 4110 4120 4130
                                        4000
                                        4640 4650
                                        4570
					#Land Docs
					6100 6110 6120 6160 6170
					6200 6210 6220 6260
					6300 6310 6320 6360
					6930
					6010 6020
					6600 6610 6700 6710
					#Air Docs
					9040 9540
					9050 9060 9070 9120
					9130 9140 9150 9200
					9210 9220 9230 9280
					#Secret Weapons
					7010 7060 7070 7080
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 3
    free_market       = 8
    freedom           = 9
    professional_army = 6
    defense_lobby     = 2
    interventionism   = 4
  }
######################################
# ARMY
######################################
landunit = {
         id = { type = 5800 id = 1 }
         location = 463
         name = "Austrian Army"
         division = {
                  id = { type = 5800 id = 2 }
                  name = "4. Panzergrenadierbrigade"
                  strength = 100
                  type = cavalry
                  model = 3
         }
         division = {
                  id = { type = 5800 id = 3 }
                  name = "3. Panzergrenadierbrigade"
                  strength = 100
                  type = cavalry
                  model = 3
         }
         division = {
                  id = { type = 5800 id = 4 }
                  name = "7. Grenadierbrigade"
                  strength = 100
                  type = mechanized
                  model = 2
         }
      }
landunit = {
         id = { type = 5800 id = 5 }
         location = 463
         name = "6. Jägerbrigade"
         division = {
                  id = { type = 5800 id = 6 }
                  name = "6. Jägerbrigade"
                  strength = 100
                  type = bergsjaeger
                  model = 14
         }
    }
#####################################
# AIR FORCE
#####################################
airunit = {
        id = { type = 5800 id = 200 }
        location = 463
        base = 463
        name = "Fliegerregiment 2"
        division = {
                 id = { type = 5800 id = 201 }
                 name = "Überwachungsgeschwader"
                 type = interceptor
                 strength = 100
                 model = 0
       }
   }
}
