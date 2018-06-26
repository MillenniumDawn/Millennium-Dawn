
##############################
# Country definition for U11 #
##############################

province =
{ id       = 1142
  air_base = { size = 2 current_size = 2 }
}            # Kinhasa


country =
{ tag                 = U11
  # Resource Reserves
  energy              = 2000
  metal               = 2000
  rare_materials      = 2500
  oil                 = 1500
  supplies            = 1500
  money               = 50
  manpower            = 140
  capital             = 1142
  diplomacy           = { }
  nationalprovinces   = { 1095 1142 1071 1072 1073 1074 1143 1144 1127 1098
                        }
  ownedprovinces      = { 1095 1142 1071 1072 1073 1074 1143 1144 1127 1098
                        }
  controlledprovinces = { 1095 1142 1074 1143 1098
                        }
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
					1980
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
    democratic        = 2
    political_left    = 6
    free_market       = 4
    freedom           = 3
    professional_army = 1
    defense_lobby     = 6
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 9000 id = 1 }
    location = 1143
    name     = "1ère Corps"
    division =
    { id       = { type = 9000 id = 3 }
      name     = "1ère 'Kamanoyla' Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 9000 id = 4 }
    location = 1142
    name     = "Gardes Républicaines"
    division =
    { id       = { type = 9000 id = 5 }
      name     = "Gardes Républicaines"
      strength = 100
      type     = infantry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 9000 id = 6 }
    location = 1074
    name     = "3ème Corps"
    division =
    { id            = { type = 9000 id = 7 }
      name          = "4ème Division d'Infanterie"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 9000 id = 8 }
      name     = "5ème Division d'Infanterie"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 9000 id = 9 }
      name     = "6ème Division d'Infanterie"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 9000 id = 10 }
    location = 1074
    name     = "4ème Corps"
    division =
    { id            = { type = 9000 id = 11 }
      name          = "1ère Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
    division =
    { id            = { type = 9000 id = 12 }
      name          = "2ème Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
  landunit =
  { id       = { type = 9000 id = 13 }
    location = 1143
    name     = "5ème Corps"
    division =
    { id            = { type = 9000 id = 14 }
      name          = "3ème Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
    division =
    { id            = { type = 9000 id = 15 }
      name          = "4ème Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
  landunit =
  { id       = { type = 9000 id = 16 }
    location = 1098
    name     = "6ème Corps"
    division =
    { id            = { type = 9000 id = 17 }
      name          = "5ème Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
    division =
    { id            = { type = 9000 id = 18 }
      name          = "6ème Brigade de la Défense"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 9000 id = 200 }
    location = 1142
    base     = 1142
    name     = "1ère Escadrille"
    division =
    { id       = { type = 9000 id = 201 }
      name     = "1ère Escadron"
      type     = tactical_bomber
      strength = 75
      model    = 0
    }
  }
}
