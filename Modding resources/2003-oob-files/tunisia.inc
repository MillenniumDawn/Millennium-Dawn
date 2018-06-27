
##############################
# Country definition for TUN #
##############################

province =
{ id       = 939
  naval_base = { size = 2 current_size = 2 }
  air_base = { size = 2 current_size = 2 }
}            # Tunis

country =
{ tag                 = TUN
  capital             = 939
  manpower            = 20
  transports          = 12
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 25
  diplomacy           = { }
  nationalprovinces   = { 936 937 939 }
  ownedprovinces      = { 936 937 939 }
  controlledprovinces = { 936 937 939 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300
                                        2400
                                        2200 2210
                                        2500
                                        2600
                                        2700
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1970
					1900
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700
                                        4750
                                        4640
                                        4570
                                        4000 4010
					#Secret Techs
                                        7330
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 5
    free_market       = 7
    freedom           = 4
    professional_army = 3
    defense_lobby     = 4
    interventionism   = 4
  }
 ##############################
 # ARMY
 ##############################
  landunit =
  { id       = { type = 12277 id = 1 }
    location = 939
    name     = "1ère Corps"
    division =
    { id            = { type = 12277 id = 2 }
      name          = "4ème Brigade Blindée"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 12277 id = 3 }
      name          = "6ème Division Mecanisée"
      strength      = 100
      type          = infantry
      model         = 1
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12277 id = 100 }
    location = 939
    base     = 939
    name     = "4ème Escadrille"
    division =
    { id       = { type = 12277 id = 101 }
      name     = "1er Escadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
  }
}