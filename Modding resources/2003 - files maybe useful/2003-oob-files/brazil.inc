
##############################
# Country definition for BRA #
##############################

province =
{ id       = 877
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 2 current_size = 2 }
}            # Marajó

province =
{ id       = 885
  naval_base = { size = 8 current_size = 8 }
    air_base = { size = 4 current_size = 4 }
}            # Rio de Janeiro

country =
{ tag                 = BRA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  manpower            = 331
  transports          = 170
  escorts             = 0
  capital             = 883
  diplomacy           = { }
  nationalprovinces   = { 848 847 835 834 825 823 822 820 872 824 826 878 876 877 879 883 887 886 885 884 882 880 881 }
  ownedprovinces      = { 848 847 835 834 825 823 822 820 872 824 826 878 876 877 879 883 887 886 885 884 882 880 881 }
  controlledprovinces = { 848 847 835 834 825 823 822 820 872 824 826 878 876 877 879 883 887 886 885 884 882 880 881 }
  techapps            = { 
                                        #Industry:
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060 5160
                                        5070 5170
                                        5080 5180
                                        5090 5190
					#Army Equip
                                        2000 2050
                                        2010 2060
                                             2070
                                        2300 2310
					2200 2210
					2500 2510
					2600 2610
					2700 2710
					2800 2810
					2400 2410
					#Army Org
                                        1000 1050
                                        1010 1060
                                             1070
					1300 1310
                                        1500 1510
                                        1200 1210
					1400 1410
					1800
					1900 1910
					1980
					1260
					1700
					#Aircraft
					4570
					4400 4410
                                        4000 4010
                                        4100 4110 4120
					4300
                                        4640 4650
                                        4700 4710
					4750 4760
					4800 4810
					#Land Docs
					6100 6110 6120 6130 6140 6150 6160 6170
					6600 6610
					6910
					6010 6030 6040 6200
					#Air Docs
					9010 9510
					9050 9060 9070 9090 9100 9110 9120 9450
					#Secret Weapons
					7010 7060 7070
					7180
                                        7330 7310
                                        #Navy Techs
                                        3000 3010
                                        3400
                                        3590
                                        3700 37700 3710 37710
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                                        8300
                                        8800
				
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 8
    free_market       = 6
    freedom           = 7
    professional_army = 4
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 7100 id = 1 }
    location = 879
    name     = "8th Military Region"
    division =
    { id       = { type = 7100 id = 2 }
      name     = "23rd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 3 }
    location = 824
    name     = "12th Military Region"
    division =
    { id       = { type = 7100 id = 4 }
      name     = "16th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 5 }
    location = 835
    name     = "9th Military Region"
    division =
    { id            = { type = 7100 id = 6 }
      name          = "13th Motorized Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 7100 id = 7 }
      name          = "4th Mechanized Cavalry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 8 }
    location = 883
    name     = "11th Military Region"
    division =
    { id            = { type = 7100 id = 9 }
      name          = "3rd Motorized Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 10 }
    location = 881
    name     = "7th Military Region"
    division =
    { id            = { type = 7100 id = 11 }
      name          = "10th Motorized Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 12 }
    location = 884
    name     = "4th Military Region"
    division =
    { id            = { type = 7100 id = 13 }
      name          = "4th Motorized Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 14 }
    location = 886
    name     = "2nd Military Region"
    division =
    { id       = { type = 7100 id = 15 }
      name     = "12th Airborne Infantry Brigade"
      strength = 100
      type     = militia
      model    = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 16 }
    location = 848
    name     = "3rd Military Region"
    division =
    { id       = { type = 7100 id = 17 }
      name     = "6th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id            = { type = 7100 id = 18 }
      name          = "8th Motorized Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id       = { type = 7100 id = 19 }
      name     = "1st Mechanized Cavalry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 7100 id = 20 }
    location = 847
    name     = "5th Military Region"
    division =
    { id       = { type = 7100 id = 21 }
      name     = "15th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 7100 id = 22 }
      name     = "5th Armored Cavalry Brigade"
      strength = 100
      type     = light_armor
      model    = 3
    }
    division =
    { id       = { type = 7100 id = 23 }
      name     = "Brazilian Army HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 7100 id = 24 }
    location = 824
    name     = "Amazonas Jungle Forces"
    division =
    { id       = { type = 7100 id = 25 }
      name     = "1st Jungle Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 7100 id = 26 }
      name     = "2nd Jungle Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 7100 id = 200 }
    location = 885
    base     = 885
    name     = "Atlantic Fleet"
    division =
    { id            = { type = 7100 id = 201 }
      name          = "Sao Paulo"
      type          = escort_carrier
      model         = 0
    }
    division =
    { id    = { type = 7100 id = 202 }
      name  = "Greenhalgh"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 203 }
      name  = "Dodsworth"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 204 }
      name  = "Bosiso"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 205 }
      name  = "Rademaker"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 206 }
      name  = "Inhauma"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 207 }
      name  = "Jaceguay"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 208 }
      name  = "Julio de Noronha"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 209 }
      name  = "Frontin"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 210 }
      name  = "Para"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 7100 id = 211 }
      name  = "Paraiba"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 7100 id = 212 }
      name  = "Pernambuco"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 7100 id = 213 }
      name  = "Constitucao"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 214 }
      name  = "Liberal"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 215 }
      name  = "Niteroi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 216 }
      name  = "Defensora"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 217 }
      name  = "Independencia"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 7100 id = 218 }
      name  = "Uniao"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 7100 id = 219 }
    location = 877
    base     = 877
    name     = "Submarine Fleet"
    division =
    { id    = { type = 7100 id = 220 }
      name  = "Tupi"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 7100 id = 221 }
      name  = "Tamoio"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 7100 id = 222 }
      name  = "Timbira"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 7100 id = 223 }
      name  = "Tapajo"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 7100 id = 224 }
    location = 885
    base     = 885
    name     = "Amphibious Fleet"
    division =
    { id    = { type = 7100 id = 225 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 7100 id = 226 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 7100 id = 227 }
      name  = "3rd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 7100 id = 228 }
      name  = "4th Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 7100 id = 100 }
    location = 885
    base     = 885
    name     = "1st Wing"
    division =
    { id       = { type = 7100 id = 101 }
      name     = "1st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 7100 id = 102 }
      name     = "3rd Figther Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 7100 id = 103 }
      name     = "7th Figther Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 7100 id = 104 }
    location = 885
    base     = 885
    name     = "2nd Wing"
    division =
    { id       = { type = 7100 id = 105 }
      name     = "16th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 7100 id = 106 }
      name     = "10th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
  }
}
