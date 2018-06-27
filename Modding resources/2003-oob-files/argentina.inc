
##############################
# Country definition for ARG #
##############################

province =
{ id         = 667
  naval_base = { size = 8 current_size = 8 }
    air_base = { size = 4 current_size = 4 }
}              # Buenos Aires

province =
{ id       = 857
  air_base = { size = 2 current_size = 2 }
}            # Puerto Madryn

country =
{ tag                 = ARG
  manpower            = 53
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 40
  capital             = 667
  transports          = 80
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 667 853 852 843 844 845 851 854 855 857 858 859 862 863 865 850 866 }
  ownedprovinces      = { 667 853 852 843 844 845 851 854 855 857 858 859 862 863 865 850 }
  controlledprovinces = { 667 853 852 843 844 845 851 854 855 857 858 859 862 863 865 850 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090 # Early CW Industry
					5110 5120 5130 5140 5150 5160 5170 5180 5190 # Late CW Industry
					#Army Equip
					2000 2010
					2300 2310 2320
					2400 2410 
					2200 2210 2220
					2500 2510 2520
					2600 2610 2620
					2700 2710 2720
					2800 2810 2820
					#Army Org
					1000 1010
					1500 1200
					1510 1210
					1980 1960
					1300 1400
					1310 1410
					1800
					1260
					1900 1910
                                                  1600
					#Aircraft
					4570
					4750 4760
					4800 4810
                                        4700 4710
					4600
					4550
                                        4100 4110
                                        4900 4910
					#Land Docs
					6910 6010 6030 6040
  					6600 6610
					6100 6200 6110 6210 6120 6220 6140 6160
                                        6130 6230
					#Air Docs
					9010 9510
					9050 9060 9070 9090 9110
					9450
					#Secret Weapons
					7010 7060
                                        7330
                                        #Navy Techs
                                        3000 3010
                                        3100 3110
                                        3590
                                        3700 3710 37710 3720
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8000 8010
                                        8500 8510
                                        8400 8410
                                        8100 8110
                                        8600 8610
										
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 8
    free_market       = 6
    freedom           = 7
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 5500 id = 1 }
    location = 845
    name     = "Third Army Corps"
    division =
    { id       = { type = 5500 id = 2 }
      name     = "8th Mountain Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 5500 id = 3 }
      name     = "4th Paratroop Brigade"
      strength = 100
      type     = paratrooper
      model    = 14
    }
    division =
    { id       = { type = 5500 id = 4 }
      name     = "6th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 5500 id = 5 }
    location = 667
    name     = "Second Army Corps"
    division =
    { id       = { type = 5500 id = 6 }
      name     = "2nd Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
    division =
    { id       = { type = 5500 id = 7 }
      name     = "12th Jungle Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  landunit =
  { id       = { type = 5500 id = 8 }
    location = 857
    name     = "Fifth Army Corps"
    division =
    { id       = { type = 5500 id = 9 }
      name     = "Argentinan Army HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 5500 id = 10 }
      name     = "1st Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
    division =
    { id       = { type = 5500 id = 11 }
      name     = "6th Mountain Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 5500 id = 12 }
      name     = "9th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 5500 id = 13 }
      name     = "10th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 5500 id = 14 }
      name     = "11th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 5500 id = 15 }
    location = 667
    name     = "Second Army Corps"
    division =
    { experience    = 5
      id       = { type = 5500 id = 16 }
      name     = "1st Special Forces Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 5500 id = 18 }
      name     = "1st Marine Brigade"
      strength = 100
      type     = marine
      model    = 11
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 5500 id = 200 }
    location = 667
    base     = 667
    name     = "1st Fleet"
    division =
    { id    = { type = 5500 id = 201 }
      name  = "ARA Santisima Trinidad"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 5500 id = 202 }
      name  = "ARA Almirante Brown"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 5500 id = 203 }
      name  = "ARA La Argentina"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 5500 id = 204 }
      name  = "ARA Heriona"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 5500 id = 205 }
      name  = "ARA Sarandi"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 5500 id = 206 }
      name  = "ARA Espora"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5500 id = 207 }
      name  = "ARA Rosales"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5500 id = 208 }
      name  = "ARA Spiro"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5500 id = 209 }
      name  = "ARA Parker"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5500 id = 210 }
      name  = "ARA Robinson"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5500 id = 211 }
      name  = "ARA Gomez Roca"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 5500 id = 212 }
    location = 667
    base     = 667
    name     = "1st Amphibious Fleet"
    division =
    { id    = { type = 5500 id = 213 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 5500 id = 214 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 5500 id = 215 }
      name  = "3rd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 5500 id = 220 }
    location = 667
    base     = 667
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 5500 id = 221 }
      name  = "ARA Santa Cruz"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5500 id = 222 }
      name  = "ARA San Juan"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5500 id = 223 }
      name  = "ARA Salta"
      type  = submarine
      model = 2
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 5500 id = 100 }
    location = 667
    base     = 667
    name     = "3rd Air Brigade"
    division =
    { id       = { type = 5500 id = 101 }
      name     = "3rd Air Attack Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 5500 id = 102 }
      name     = "5th Air Hunter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 5500 id = 103 }
      name     = "6th Air Hunter Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 5500 id = 104 }
    location = 667
    base     = 667
    name     = "Air Transport Brigade"
    division =
    { id       = { type = 5500 id = 105 }
      name     = "1st Air Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
