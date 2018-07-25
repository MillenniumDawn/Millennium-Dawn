
##############################
# Country definition for AST #
##############################

province =
{ id         = 1727
  naval_base = { size = 4 current_size = 4 }
}              # Sydney

province =
{ id         = 1703
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 4 current_size = 4 }
}              # Darwin

province =
{ id         = 1712
  naval_base = { size = 4 current_size = 4 }
}              # Perth

province =
{ id       = 1725
  air_base = { size = 2 current_size = 2 }
}            # Wentworth

country =
{ tag                 = AST
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 80
  manpower            = 40
  transports          = 95
  escorts             = 0
  capital             = 1728
  diplomacy           = { }
  nationalprovinces   = { 1703 1704 1705 1706 1707 1708 1709 1710 1711 1712 1713 1714 1715 1716 1717 1718 1719 1720 1721 1722 1723 1724 1725 1726 1727
                          1728 1729 1730 1731 1732 1733 1693 1694 1695 1696 1697 1698 1699 1700 1701 1702 1734
                        }
  ownedprovinces      = { 1703 1704 1705 1706 1707 1708 1709 1710 1711 1712 1713 1714 1715 1716 1717 1718 1719 1720 1721 1722 1723 1724 1725 1726 1727
                          1728 1729 1730 1731 1732 1733 1693 1694 1695 1696 1697 1698 1699 1700 1701 1702 1734
                        }
  controlledprovinces = { 1703 1704 1705 1706 1707 1708 1709 1710 1711 1712 1713 1714 1715 1716 1717 1718 1719 1720 1721 1722 1723 1724 1725 1726 1727
                          1728 1729 1730 1731 1732 1733 1693 1694 1695 1696 1697 1698 1699 1700 1701 1702 1734
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
                                        2000 2050 2110
					2400 2410 2420 2430
                                             2070
					2200 2210 2220 2230
					2600 2610 2620 2630
					2800 2810 2820 2830
                                        2300 2310
                                        2500 2510 2520 2530
                                        2700 2710 2720 2730
					#Army Org
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
					1300 1310 1320 1330
                                        1500 1510
					1260 1270
                                                  1600 1610
                                             1700 1710
                                             1800 1810
					1980 1970
					1900 1910 1920 1930
					#Aircraft
                                        4640 4650 4660
                                        4300 4310
                                        4000 4010 4020 4030
                                        4500
					4800 4810 4820
					4750 4760 4770
					4700 4710 4720
					4900 4910 4920
					#Land Docs
					6010 6030 6040
					6600 6620 6700 6720
					6930
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9110 9120
					9130 9140 9150 9170 9190 9200
					9210 9220 9230 9250 9270 9280
					#Secret Weapons
					7010 7060 7070
					7180
					7310 7320 7330
                                        #Navy Techs
                                        3000 3010 3020
                                        3590
                                        3700 3710 3720
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
			}
  blueprints          = { 3100 3110 3120 }				
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 5
    free_market       = 8
    freedom           = 9
    professional_army = 10
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 5700 id = 1 }
    location = 1728
    name     = "Special Op. Command"
    division =
    { experience    = 15
      id       = { type = 5700 id = 2 }
      name     = "Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 14
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 5700 id = 3 }
    location = 1727
    name     = "II Corps"
    division =
    { id       = { type = 5700 id = 4 }
      name     = "2nd Division"
      strength = 100
      type     = motorized
      model    = 3
    }
  }
  landunit =
  { id       = { type = 5700 id = 5 }
    location = 1727
    name     = "Deployment Force"
    division =
    { id       = { type = 5700 id = 6 }
      name     = "Australian Army HQ"
      strength = 100
      type     = hq
      model    = 1      
    }
    division =
    { id       = { type = 5700 id = 7 }
      name     = "1st Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 5700 id = 8 }
      name     = "3rd Brigade"
      strength = 100
      type     = mechanized
      model    = 3
    }
    division =
    { id       = { type = 5700 id = 9 }
      name     = "7th Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 5700 id = 200 }
    location = 1703
    base     = 1703
    name     = "1st Fleet"
    division =
    { id    = { type = 5700 id = 201 }
      name  = "HMAS Adelaide"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 202 }
      name  = "HMAS Canberra"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 203 }
      name  = "HMAS Darwin"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 204 }
      name  = "HMAS Anzac"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 5700 id = 205 }
      name  = "HMAS Arunta"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 5700 id = 206 }
      name  = "HMAS Warramunga"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 5700 id = 207 }
      name  = "HMAS Stuart"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 5700 id = 208 }
      name  = "HMAS Parramatta"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 5700 id = 209 }
      name  = "HMAS Ballarat"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 5700 id = 210 }
    location = 1727
    base     = 1727
    name     = "2nd Fleet"
    division =
    { id    = { type = 5700 id = 211 }
      name  = "HMAS Sydney"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 212 }
      name  = "HMAS Melbourne"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 213 }
      name  = "HMAS Newcastle"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 5700 id = 214 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 5700 id = 215 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 5700 id = 217 }
    location = 1727
    base     = 1727
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 5700 id = 218 }
      name  = "HMAS Collins"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5700 id = 219 }
      name  = "HMAS Farncomb"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5700 id = 220 }
      name  = "HMAS Waller"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5700 id = 221 }
      name  = "HMAS Dechaineux"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5700 id = 222 }
      name  = "HMAS Sheehan"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5700 id = 223 }
      name  = "HMAS Rankin"
      type  = submarine
      model = 4
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 5701 id = 100 }
    location = 1703
    base     = 1703
    name     = "3rd Wing"
    division =
    { id       = { type = 5701 id = 101 }
      name     = "3rd Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 5701 id = 102 }
      name     = "75th Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 5701 id = 103 }
    location = 1725
    base     = 1725
    name     = "4th Wing"
    division =
    { id       = { type = 5701 id = 104 }
      name     = "6th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 2
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 5700 id = 300 }
    name  = "HMAS Toowoomba"
    type  = destroyer
    model = 2
    cost  = 4
    date  = { day = 2 month = august year = 2003 }
  }
  division_development =
  { id    = { type = 5700 id = 301 }
    name  = "HMAS Perth"
    type  = destroyer
    model = 2
    cost  = 4
    date  = { day = 18 month = july year = 2004 }
  }
  ############################
  # Adelaide to Darwin railway
  province_development = { 
        id = { type = 4712 id = 302 } 
        name = ""
        cost = 1
        date = { day = 15 month = january year = 2004 } 
        size = 1
	location = 1719
        type = infrastructure 
        } 
  province_development = { 
        id = { type = 4712 id = 303 } 
        name = ""
        cost = 1
        date = { day = 15 month = january year = 2004 } 
        size = 1
	location = 1705
        type = infrastructure 
        } 
}
