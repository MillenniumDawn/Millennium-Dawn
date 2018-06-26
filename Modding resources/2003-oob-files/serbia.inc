
##############################
# Country definition for SER #
##############################

province =
{ id       = 453
  air_base = { size = 4 current_size = 4 }
}            # Beograd

country =
{ tag                 = SER
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 19
  capital             = 453
  transports          = 25
  escorts             = 0
  diplomacy           = {
	relation = { tag = MTN value = 150 access = yes }
	relation = { tag = ALB value = -75 }
	relation = { tag = ANG value = 75 }
	relation = { tag = BLR value = 50 }
	relation = { tag = CHC value = 75 }
	relation = { tag = CUB value = 75 }
	relation = { tag = EGY value = 75 }
	relation = { tag = GRE value = 75 }
	relation = { tag = PER value = 50 }
	relation = { tag = IRQ value = 50 }
	relation = { tag = CYN value = -150 }
	relation = { tag = LBY value = 50 }
	relation = { tag = U09 value = 25 }
	relation = { tag = ROM value = 50 }
	relation = { tag = SLV value = 75 }
	relation = { tag = SUD value = 25 }
	relation = { tag = SYR value = 25 }
	relation = { tag = USA value = -50 }
	relation = { tag = VEN value = 50 }
	relation = { tag = EUS value = 50 }
  }
  nationalprovinces   = { 493 494 418 453 452 451 1057 1168 }
  ownedprovinces      = { 493 494 418 453 452 451 1057 1168 }
  controlledprovinces = { 493 494 418 453 452 451 1057 1168 }
  techapps            = {
                                      	#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        5210 5220
                                        #Army Equip
					2200 2210 2220
					2300 2310 2320
					2400 2410 2420
					2500 2510 2520
					2600 2610 2620
					2700 2710 2720
					2800 2810 2820
                                        2000 2050
                                        2010 2060
                                             2070
					#Army Org
					1960
					1260 1270
					1900 1910 1920
					1700
					1800 1810
                                        1000 1050
                                        1010 1060
					1500 1510 1520
					1400 1410 1420
					1300 1310 1320
					1200 1210 1220
					#Aircraft
					4800 4700 4750
					4900
					4000 4010
					4100
					4550
					4640
					4570
					#Land Docs
					6910 6920
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9090 9120
					#Secret Weapons
					7010 7060 7070
                                        7330 7310 
					#Navy Techs
                                        3000 3010
                                        3700 37700
                                        3590
                                        3850 3860
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
    political_left    = 7
    free_market       = 5
    freedom           = 8
    professional_army = 3
    defense_lobby     = 4
    interventionism   = 5
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 19100 id = 1 }
    location = 453
    name     = "1. Srpska Armija"
    division =
    { id            = { type = 19100 id = 2 }
      name          = "Specijalna Brigada"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 19100 id = 3 }
      name          = "Serbian Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 19100 id = 4 }
      name     = "2. brigada kopnene vojske"
      strength = 100
      type     = cavalry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 19100 id = 5 }
    location = 389
    name     = "2. Srpska Armija"
    division =
    { id            = { type = 19100 id = 6 }
      name          = "3. Brigada Kopnene Vojske"
      strength      = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 19100 id = 7 }
      name     = "1. Brigada Kopnene Vojske"
      strength = 100
      type     = cavalry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 19100 id = 8 }
    location = 418
    name     = "3. Srpska Armija"
    division =
    { id            = { type = 19100 id = 9 }
      name          = "4. Brigada Kopnene Vojske"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 19100 id = 10 }
      name          = "Mesovita Artiljerijska Brigada"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 19100 id = 200 }
    location = 389
    base     = 389
    name     = "1. Srpska Flotila"
    division =
    { id    = { type = 19100 id = 201 }
      name  = "Kotor"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 19100 id = 202 }
      name  = "Novi Sad"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 19100 id = 203 }
      name  = "Beograd"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 19100 id = 204 }
      name  = "Podgorica"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 19100 id = 205 }
      name  = "Sava"
      type  = submarine
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 19100 id = 100 }
    location = 453
    base     = 453
    name     = "204. Avio Baza"
    division =
    { id       = { type = 19100 id = 101 }
      name     = "101. Squadron 'Vitezovi'"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 19100 id = 102 }
      name     = "252. Squadron 'Kurjaci sa Usca'"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 19100 id = 103 }
      name     = "138. Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 19100 id = 104 }
    location = 453
    base     = 453
    name     = "98. Avio Baza"
      division =
    { id       = { type = 19100 id = 105 }
      name     = "241. Squadron 'Tigrovi'"
      type     = cas
      strength = 100
      model    = 0
    }
  }
 }