
##############################
# Country definition for INO #
##############################

province =
{ id         = 1628
  naval_base = { size = 6 current_size = 6 }
    air_base = { size = 4 current_size = 4 }
}              # Batavia

province =
{ id         = 1662
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 2 current_size = 2 }
}              # Kokonau

country =
{ tag                 = INO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 377
  transports          = 200
  escorts             = 0
  capital             = 1628
  diplomacy           = { }
  nationalprovinces   = { 1354 1355 1356 1357 1358 1359 1635 1636 1637 1638 1639 1640 1641 1642 1643 1645 1648 1649 1650 1651 1652 1653 1654 1655 1656
                          1657 1659 1660 1661 1662 1663 1664 1665 1673 1674 1628 1629 1630 1631 1632 1633 1634
                        }
  ownedprovinces      = { 1354 1355 1356 1357 1358 1359 1635 1636 1637 1638 1639 1640 1641 1642 1643 1645 1648 1649 1650 1651 1652 1653 1654 1655 1656
                          1657 1659 1660 1661 1662 1663 1664 1665 1673 1674 1628 1629 1630 1631 1632 1633 1634
                        }
  controlledprovinces = { 1354 1355 1356 1357 1358 1359 1635 1636 1637 1638 1639 1640 1641 1642 1643 1645 1648 1649 1650 1651 1652 1653 1654 1655 1656
                          1657 1659 1660 1661 1662 1663 1664 1665 1673 1674 1628 1629 1630 1631 1632 1633 1634
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equipment
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
					1980
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                             1700
                                             1800
                                        1900 1910
                                        1260
					#Aircraft
					4800
                                        4700 4710
                                        4750 4760
					4900
                                        4000 4010 4020
                                        4400
					#Land Docs
					6010 6030 6040
					6910 6920
					6600 6610
					6100 6110 6120 6130 6140 6150 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
                                        9110
					#Secret Weapons
					7010
					7060 7070
					7180
					7310 7330
                                        #Navy Techs
                                        3000
                                        3590
                                        3700 3710 3720
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
    democratic        = 8
    political_left    = 5
    free_market       = 6
    freedom           = 5
    professional_army = 4
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12400 id = 1 }
    location = 1356
    name     = "I Corps"
    division =
    { id            = { type = 12400 id = 2 }
      name          = "8th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 3 }
      name     = "9th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 4 }
    location = 1358
    name     = "II Corps"
    division =
    { id            = { type = 12400 id = 5 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 6 }
      name     = "7th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 7 }
    location = 1628
    name     = "III Corps"
    division =
    { id            = { type = 12400 id = 8 }
      name          = "2nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
      extra         = heavy_armor
      brigade_model = 0
    }
    division =
    { id       = { type = 12400 id = 9 }
      name     = "3rd Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 10 }
      name     = "4th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 11 }
    location = 1630
    name     = "IV Corps"
    division =
    { id            = { type = 12400 id = 12 }
      name          = "3rd Motorized Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 13 }
      name     = "5th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 14 }
    location = 1632
    name     = "V Corps"
    division =
    { id            = { type = 12400 id = 15 }
      name          = "10th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 16 }
      name     = "11th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 17 }
    location = 1642
    name     = "VI Corps"
    division =
    { id            = { type = 12400 id = 18 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 19 }
      name     = "13th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 20 }
    location = 1640
    name     = "VII Corps"
    division =
    { id            = { type = 12400 id = 21 }
      name          = "14th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 22 }
      name     = "15th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 23 }
    location = 1665
    name     = "VIII Corps"
    division =
    { id            = { type = 12400 id = 24 }
      name          = "16th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 25 }
      name     = "17th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 26 }
    location = 1635
    name     = "IX Corps"
    division =
    { id            = { type = 12400 id = 27 }
      name          = "18th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 28 }
      name     = "19th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12400 id = 29 }
    location = 1628
    name     = "Jakarta Corps"
    division =
    { id            = { type = 12400 id = 30 }
      name          = "1st Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 12400 id = 31 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12400 id = 32 }
      name     = "2nd Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 12400 id = 300 }
    location = 1628
    base     = 1628
    name     = "Western Fleet"
    division =
    { id    = { type = 12400 id = 301 }
      name  = "KRI Ahmad Yani"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 302 }
      name  = "KRI Slamet Riyadi"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 303 }
      name  = "KRI Yos Sudarso"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 304 }
      name  = "KRI Oswald Sihaan"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 305 }
      name  = "KRI Abdul Halim Perdanakasuma"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 306 }
      name  = "KRI Martha Kristina Tiyahahu"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 307 }
      name  = "KRI Hasanaddun"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 308 }
      name  = "KRI Samadikum"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 317 }
      name  = "KRI Cakra"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 12400 id = 318 }
    location = 1628
    base     = 1628
    name     = "Western Fleet Transports"
    division =
    { id    = { type = 12400 id = 319 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 320 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 321 }
      name  = "3rd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 322 }
      name  = "4th Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 323 }
      name  = "5th Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 12400 id = 333 }
    location = 1662
    base     = 1662
    name     = "Eastern Fleet"
    division =
    { id    = { type = 12400 id = 334 }
      name  = "KRI Karel Satsuitubun"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 335 }
      name  = "KRI Fatahilah"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 336 }
      name  = "KRI Malahayati"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 337 }
      name  = "KRI Nala"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 338 }
      name  = "KRI Martadinata"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 339 }
      name  = "KRI Mongisidi"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 340 }
      name  = "KRI Ngurah"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12400 id = 349 }
      name  = "KRI Nanggala"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 12400 id = 350 }
    location = 1662
    base     = 1662
    name     = "Eastern Fleet Transports"
    division =
    { id    = { type = 12400 id = 351 }
      name  = "6th Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 352 }
      name  = "7th Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12400 id = 353 }
      name  = "8th Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12400 id = 200 }
    location = 1628
    base     = 1628
    name     = "1st Air Force"
    division =
    { id       = { type = 12400 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12400 id = 202 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
}
