
##############################
# Country definition for RUS #
##############################

province =
{ id         = 133
  naval_base = { size = 10 current_size = 10 }
  air_base   = { size = 10 current_size = 10 }
}              # Murmansk
province =
{ id       = 175
  air_base = { size = 10 current_size = 10 }
  rocket_test = { size = 3 current_size = 3 }
}            # Moscow
province =
{ id       = 181
  air_base = { size = 10 current_size = 10 }
}            # Kaluga
province =
{ id         = 187
  naval_base = { size = 4 current_size = 4 }
  air_base   = { size = 10 current_size = 10 }
}              # St. Petersburg
province =
{ id         = 258
  naval_base = { size = 4 current_size = 4 }
}              # Rostov
province =
{ id         = 510
  naval_base = { size = 10 current_size = 10 }
}              # Kaliningrad
province =
{ id       = 1371
  air_base = { size = 10 current_size = 10 }
}            # Tetyukhe
province =
{ id         = 1372
  naval_base = { size = 8 current_size = 8 }
}              # Vladivostok
province =
{ id       = 1547
  air_base = { size = 8 current_size = 8 }
}            # Barnaul
province =
{ id       = 1572
  air_base = { size = 10 current_size = 10 }
}            # Yekaterinburg
province = { id = 1828 nuclear_reactor = 9 } # Samara
province =
{ id       = 1843
  air_base = { size = 10 current_size = 10 }
}            # Armavil

#####################
# Country main data #
#####################

country =
{ tag                 = RUS
  capital             = 175
  # Resource Reserves
  nuke                = 200
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 800
  supplies            = 25000
  money               = 150
  manpower            = 300
  transports          = 400
  escorts             = 50
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 2
    free_market       = 6
    freedom           = 7
    professional_army = 4
    defense_lobby     = 5
    interventionism   = 8
  }
  SpyInfo             = { country = "ENG" NumberOfSpies = 5 }
  SpyInfo             = { country = "FRA" NumberOfSpies = 3 }
  SpyInfo             = { country = "USA" NumberOfSpies = 5 }
  SpyInfo             = { country = "CAN" NumberOfSpies = 3 }
  SpyInfo             = { country = "U09" NumberOfSpies = 2 }
  SpyInfo             = { country = "U06" NumberOfSpies = 3 }
  SpyInfo             = { country = "CHC" NumberOfSpies = 3 }
  SpyInfo             = { country = "KAZ" NumberOfSpies = 4 }
  SpyInfo             = { country = "UKR" NumberOfSpies = 5 }
  SpyInfo             = { country = "POL" NumberOfSpies = 4 }
  SpyInfo             = { country = "IND" NumberOfSpies = 3 }
  SpyInfo             = { country = "FIN" NumberOfSpies = 3 }
  SpyInfo             = { country = "NOR" NumberOfSpies = 4 }
  SpyInfo             = { country = "GER" NumberOfSpies = 1 }
  SpyInfo             = { country = "GEO" NumberOfSpies = 3 }
  SpyInfo             = { country = "AZB" NumberOfSpies = 3 }
  SpyInfo             = { country = "EGY" NumberOfSpies = 3 }
  SpyInfo             = { country = "PAK" NumberOfSpies = 1 }
  SpyInfo             = { country = "PER" NumberOfSpies = 3 }
  SpyInfo             = { country = "EST" NumberOfSpies = 4 }
  SpyInfo             = { country = "SER" NumberOfSpies = 3 }
  SpyInfo             = { country = "LAT" NumberOfSpies = 2 }
  SpyInfo             = { country = "LBY" NumberOfSpies = 1 }
  SpyInfo             = { country = "LIT" NumberOfSpies = 3 }
  SpyInfo             = { country = "KYG" NumberOfSpies = 3 }
  SpyInfo             = { country = "BRA" NumberOfSpies = 1 }
  SpyInfo             = { country = "VEN" NumberOfSpies = 1 }
  SpyInfo             = { country = "SYR" NumberOfSpies = 4 }
  SpyInfo             = { country = "TAJ" NumberOfSpies = 3 }
  SpyInfo             = { country = "TUR" NumberOfSpies = 2 }
  SpyInfo             = { country = "MON" NumberOfSpies = 1 }
  SpyInfo             = { country = "SWE" NumberOfSpies = 2 }
  SpyInfo             = { country = "SPA" NumberOfSpies = 1 }
  SpyInfo             = { country = "AST" NumberOfSpies = 1 }
  nationalprovinces   = { 1372 2603 2604 1373 1371 1370 1369 1367 1366 1527 1529 1528 1526 1523 1410 1525 1524 1409 1164 1165 1166 1167 1170 1171 1172 1405 1175
                          1522 1521 1384 1383 1520 1416 1415 1414 1413 1162 1412 1411 1163 1159 1160 1158 1417 1558 1557 1549 1547 1546 1559 1561 1560
                          1562 1563 1532 1537 1538 1545 1544 1548 1543 1540 1539 1536 1535 1533 1534 1157 1531 1156 1155 1154 1565 1564 1571 1597 1598
                          1552 1594 1596 1573 1593 1575 1574 1572 1566 1567 1570 1577 1150 1151 1152 1153 1773 1772 1771 154  1840 1841 165  153  151 
                          152  150  135  134  133  1838 1857 1849 1844 1846 1843 255  256  257  270  1842 1837 271  164  1833 1834 1836 1839 1827
                          1828 1835 1829 1832 1831 1830 1777 1778 1776 1775 1780 1781 1782 1783 1774 163  162  161  160  159  157  156  158  155  169 
                          168  167  179  180  166  178  177  170  171  172  173  174  175  176  181  182  183  184  190  191  189  185  186  187  188 
                          192  200  201  273  274  275  276  277  278  279  280  281  282  283  284  258  259   247  243  262  261  269  268  267 
                          266  265  264  263  94   215  216  219  285  286  287  288  289  1149 1161 1368 1541 1542 1176 146  145  132  1418 1174 1177
                          510 
                        }
  ownedprovinces      = { 1372 2603 2604 1373 1371 1370 1369 1367 1366 1527 1529 1528 1526 1523 1410 1525 1524 1409 1164 1165 1166 1167 1170 1171 1172 1405 1175
                          1522 1521 1384 1383 1520 1416 1415 1414 1413 1162 1412 1411 1163 1159 1160 1158 1417 1558 1557 1549 1547 1546 1559 1561 1560
                          1562 1563 1532 1537 1538 1545 1544 1548 1543 1540 1539 1536 1535 1533 1534 1157 1531 1156 1155 1154 1565 1564 1571 1597 1598
                          1552 1594 1596 1573 1593 1575 1574 1572 1566 1567 1570 1577 1150 1151 1152 1153 1773 1772 1771 154  1840 1841 165  153  151 
                          152  150  135  134  133  1838 1857 1849 1844 1846 1843 255  256  257  270  1842 1837 271  164  1833 1834 1836 1839 1827
                          1828 1835 1829 1832 1831 1830 1777 1778 1776 1775 1780 1781 1782 1783 1774 163  162  161  160  159  157  156  158  155  169 
                          168  167  179  180  166  178  177  170  171  172  173  174  175  176  181  182  183  184  190  191  189  185  186  187  188 
                          192  200  201  273  274  275  276  277  278  279  280  281  282  283  284  258  259   247  243  262  261  269  268  267 
                          266  265  264  263  94   215  216  219  285  286  287  288  289  1149 1161 1368 1541 1542 1176 146  145  132  1418 1174 1177
                          510 
                        }
  controlledprovinces = { 1372 2603 2604 1373 1371 1370 1369 1367 1366 1527 1529 1528 1526 1523 1410 1525 1524 1409 1164 1165 1166 1167 1170 1171 1172 1405 1175
                          1522 1521 1384 1383 1520 1416 1415 1414 1413 1162 1412 1411 1163 1159 1160 1158 1417 1558 1557 1549 1547 1546 1559 1561 1560
                          1562 1563 1532 1537 1538 1545 1544 1548 1543 1540 1539 1536 1535 1533 1534 1157 1531 1156 1155 1154 1565 1564 1571 1597 1598
                          1552 1594 1596 1573 1593 1575 1574 1572 1566 1567 1570 1577 1150 1151 1152 1153 1773 1772 1771 154  1840 1841 165  153  151 
                          152  150  135  134  133  1838 1857 1849 1844 1846 1843 255  256  257  270  1842 1837 271  164  1833 1834 1836 1839 1827
                          1828 1835 1829 1832 1831 1830 1777 1778 1776 1775 1780 1781 1782 1783 1774 163  162  161  160  159  157  156  158  155  169 
                          168  167  179  180  166  178  177  170  171  172  173  174  175  176  181  182  183  184  190  191  189  185  186  187  188 
                          192  200  201  273  274  275  276  277  278  279  280  281  282  283  284  258  259   247  243  262  261  269  268  267 
                          266  265  264  263  94   215  216  219  285  286  287  288  289  1149 1161 1368 1541 1542 1176 146  145  132  1418 1174 1177
                          510 
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					2000 2010
					2050 2060 2070
					2110 2120
					2150
					#Army Org
					1990 1960
					1260 1270
					1900 1910 1920 1930
					1700 1710 1720
					1800 1810 1820
					1600 1650
					1610 1660
					1500 1510 1520 1530
					1400 1410 1420 1430
					1300 1310 1320 1330
					1200 1210 1220 1230
					1000 1010
					1050 1060 1070
					1110 1120
					1150
					#Aircraft
					4640 4650 4660 4670
					4900 4910
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4600 4610
					4570
					4550 4560
					4000 4010 4020 4030
					4100 4110 4120 4130
					4400 4410 4420
					4500 4510 4520
					4200 4210 4220
					4300 4310 4320
					#Land Docs
					6910 6920
					6010 6030 6050 6060
					6600 6630
					6700 6730
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9080 9090 9100 9110 9120
					9130 9140 9150 9160 9170 9180 9190 9200
					9450 9460
					#Secret Weapons
					7010
					7020 7030 7040 7050
					7060 7070
					7100 7110 7120
					7180 7190 7200 7210
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020
                                        3100 3110 3120
                                        3200 3210
                                        32220
                                        3500 3510 3520
                                        3590 3600
                                        3700 37700 3710 37710 3720 37720
                                        3800 3810 38810 3820 38820 3830
                                        3850 3860 3870 3880
                                        3900 3910 3920
                                        #Navy Doctrines
                                        8900 8910 8920 8930
                                        8950 8960 8970
                                        8400 8410 8420 8430
                                        8000 8010 8020 8030
                                        8500 8510 8520 8530
                                        8100 8110 8120
                                        8600 8610 8620
                                        8200 8210 8220 8230
                                        8700 8710 8720 8730
                                        8300 8310 8320
                                        8800 8810 8820
                        }
  diplomacy =
  { relation = { tag = NOR value = 50 }
    relation = { tag = SWE value = 50 }
    relation = { tag = DEN value = 50 }
    relation = { tag = HOL value = 50 }
    relation = { tag = BEL value = 50 }
    relation = { tag = IRE value = 50 }
    relation = { tag = ENG value = 50 }
    relation = { tag = FRA value = 50 }
    relation = { tag = SPA value = 50 }
    relation = { tag = POR value = 50 }
    relation = { tag = ITA value = 50 }
    relation = { tag = GER value = 150 }
    relation = { tag = EST value = -100 }
    relation = { tag = LAT value = -100 }
    relation = { tag = LIT value = -100 }
    relation =
    { tag        = BLR
      value      = 200
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = ALS
      value      = 200
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = PRI
      value      = 200
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = SER
      value      = 200
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = UKR
      value      = 150
      access     = yes
    }
    relation =
    { tag        = U03
      value      = 200
      access     = yes
    }
    relation = { tag = POL value = -50 }
    relation = { tag = CZE value = -50 }
    relation = { tag = SLO value = -50 }
    relation = { tag = HUN value = -50 }
    relation = { tag = ROM value = -50 }
    relation = { tag = BUL value = -50 }
    relation = { tag = GEO value = 130 access = yes }
    relation = { tag = AZB value = 50 access = yes }
    relation = { tag = ARM value = 150 access = yes }
    relation =
    { tag        = KAZ
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = UZB
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = TRK
      value      = 100
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = KYG
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = TAJ
      value      = 100
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = MON
      value      = 100
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation = { tag = PER value = 150 }
    relation =
    { tag        = IND
      value      = 150
    }
    relation = { tag = SYR value = 150 access = yes }
    relation = { tag = ISR value = -50 }
    relation = { tag = SOM value = 50 }
    relation = { tag = BRA value = 50 }
    relation = { tag = CHC value = 150 access = yes }
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 18700 id = 1 }
    location = 510
    name     = "Kaliningrad Military District"
    division =
    { id       = { type = 18700 id = 2 }
      name     = "18th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 3 }
      name     = "7th Separate Motor Rifle Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 4 }
    location = 187
    name     = "Leningrad Military District"
    division =
    { id            = { type = 18700 id = 5 }
      name          = "Leningrad MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 6 }
      name     = "138th Guards Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 7 }
      name     = "200th Guards Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 8 }
      name          = "2nd Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 9 }
      name       = "104th Guards Airborne Regiment"
      strength   = 100
      type       = militia
      model      = 3
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 10 }
      name       = "234th Guards Airborne Regiment"
      strength   = 100
      type       = militia
      model      = 3
    }
  }
  landunit =
  { id       = { type = 18700 id = 11 }
    location = 175
    name     = "Moscow Military District"
    division =
    { id            = { type = 18700 id = 12 }
      name          = "Moscow MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 13 }
      name       = "51st Guards Airborne Regiment"
      strength   = 100
      type       = paratrooper
      model      = 15
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 14 }
      name       = "137th Guards Airborne Regiment"
      strength   = 100
      type       = paratrooper
      model      = 15
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 15 }
      name       = "217th Guards Airborne Regiment"
      strength   = 100
      type       = paratrooper
      model      = 15
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 16 }
      name       = "331st Guards Airborne Regiment"
      strength   = 100
      type       = paratrooper
      model      = 15
    }
    division =
    { id            = { type = 18700 id = 17 }
      name          = "2nd Guards Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 18 }
      name     = "27th Motor Rifle Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 19 }
      name     = "8th Motor Rifle Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 20 }
      name          = "16th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18700 id = 21 }
    location = 1520
    name     = "29th Combined Arms Army"
    division =
    { id            = { type = 18700 id = 22 }
      name          = "5th Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 19
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 23 }
    location = 1383
    name     = "36th Combined Arms Army"
    division =
    { id            = { type = 18700 id = 24 }
      name          = "131st Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 25 }
      name     = "168th Motor Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 18700 id = 26 }
    location = 283
    name     = "20th Army"
    division =
    { id            = { type = 18700 id = 27 }
      name          = "4th Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 12
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 18700 id = 28 }
      name          = "10th Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 13
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 29 }
    location = 166
    name     = "22nd Combined Arms Army"
    division =
    { id            = { type = 18700 id = 30 }
      name          = "3rd Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 31 }
    location = 258
    name     = "North Caucasus Military District"
    division =
    { id            = { type = 18700 id = 32 }
      name          = "North Caucasus MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 18700 id = 33 }
      name          = "19th Guards Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 34 }
      name     = "42nd Guards Motor Rifle Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 35 }
      name     = "131st Motor Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 36 }
      name          = "22nd Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 37 }
      name          = "10th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18700 id = 38 }
    location = 510
    name     = "58th Army"
    division =
    { id       = { type = 18700 id = 39 }
      name     = "20th Motor Rifle Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 40 }
      name     = "205th Motor Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 41 }
      name     = "136th Separate Motor Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 42 }
      name     = "135th Separate Motor Rifle Regiment"
      strength = 100
      type     = cavalry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 43 }
    location = 1849
    name     = "Trans-Caucasus Military District"
    division =
    { experience = 5
      id         = { type = 18700 id = 44 }
      name       = "108th Guards Airborne Regiment"
      strength   = 100
      type       = militia
      model      = 2
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 45 }
      name       = "247th Guards Airborne Regiment"
      strength   = 100
      type       = militia
      model      = 2
    }
    division =
    { id       = { type = 18700 id = 46 }
      name     = "12th Military Base"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 47 }
      name     = "62nd Military Base"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 48 }
      name     = "102nd Military Base"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 49 }
      name     = "137th Military Base"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 18700 id = 50 }
    location = 1849
    name     = "Independent Caucasus Group"
    division =
    { id            = { type = 18700 id = 51 }
      name          = "127th Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 52 }
    location = 1572
    name     = "Volga-Urals Military District"
    division =
    { id            = { type = 18700 id = 53 }
      name          = "Volga-Urals MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 18700 id = 54 }
      name          = "15th Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 15
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 88 }
      name     = "16th Tank Division"
      strength = 50
      type     = armor
      model    = 11
    }
    division =
    { id       = { type = 18700 id = 89 }
      name     = "90th Tank Division"
      strength = 50
      type     = armor
      model    = 11
    }
    division =
    { id       = { type = 18700 id = 55 }
      name     = "201st Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 56 }
      name     = "34th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id            = { type = 18700 id = 57 }
      name          = "27th Guards Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 58 }
      name          = "12th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 59 }
      name          = "3rd Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18700 id = 60 }
    location = 1163
    name     = "Siberian-Transbaikal Military District"
    division =
    { id            = { type = 18700 id = 61 }
      name          = "Siberian-Transbaikal MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 62 }
      name       = "11th Air Assault Brigade"
      strength   = 100
      type       = paratrooper
      model      = 15
    }
    division =
    { id            = { type = 18700 id = 63 }
      name          = "2nd Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 64 }
      name          = "24th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 65 }
      name          = "67th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18700 id = 66 }
    location = 1548
    name     = "41st Combined Arms Army"
    division =
    { id            = { type = 18700 id = 67 }
      name          = "85th Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 68 }
      name     = "74th Motor Rifle Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 69 }
    location = 1372
    name     = "Far East Military District"
    division =
    { id            = { type = 18700 id = 70 }
      name          = "Far East MD"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { experience = 5
      id         = { type = 18700 id = 71 }
      name       = "83rd Separate Airborne Brigade"
      strength   = 100
      type       = militia
      model      = 3
    }
    division =
    { experience    = 15
      id            = { type = 18700 id = 72 }
      name          = "14th Spetsnaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18700 id = 73 }
    location = 1372
    name     = "5th Army"
    division =
    { id            = { type = 18700 id = 74 }
      name          = "81st Guards Motor Rifle Division"
      strength      = 100
      type          = infantry
      model         = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 75 }
      name     = "121st Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 76 }
      name     = "29th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 77 }
    location = 1528
    name     = "35th Combined Arms Army"
    division =
    { id            = { type = 18700 id = 78 }
      name          = "21st Guards Tank Division"
      strength      = 100
      type          = armor
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 18700 id = 79 }
      name     = "194th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 80 }
      name     = "265th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 81 }
      name     = "270th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 82 }
    location = 1176
    name     = "68th Combined Arms Army"
    division =
    { id       = { type = 18700 id = 83 }
      name     = "79th Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 84 }
      name     = "33rd Motor Rifle Division"
      strength = 100
      type     = motorized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18700 id = 85 }
    location = 1372
    name     = "Marine Forces"
    division =
    { id       = { type = 18700 id = 86 }
      name     = "55th Marine Brigade"
      strength = 100
      type     = marine
      model    = 11
    }
  }
  ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 18700 id = 200 }
    location = 133
    base     = 133
    name     = "11th Squadron"
    division =
    { id    = { type = 18700 id = 201 }
      name  = "Tambov"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 202 }
      name  = "Danyl Moskovsky"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 203 }
      name  = "Polyarnie Zori"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 204 }
      name  = "Sosnovy Bor"
      type  = submarine
      model = 13
    }
  }
  navalunit =
  { id       = { type = 18700 id = 205 }
    location = 133
    base     = 133
    name     = "12th Squadron"
    division =
    { id    = { type = 18700 id = 206 }
      name  = "Leopard"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 207 }
      name  = "Volk"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 208 }
      name  = "Vepr"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 209 }
      name  = "Gepard"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 210 }
      name  = "Tigr"
      type  = submarine
      model = 15
    }
  }
  navalunit =
  { id       = { type = 18700 id = 211 }
    location = 133
    base     = 133
    name     = "7th Operational Squadron"
    division =
    { id            = { type = 18700 id = 212 }
      name          = "Admiral Kuznetsov"
      type          = escort_carrier
      model         = 7
    }
    division =
    { id    = { type = 18700 id = 213 }
      name  = "Admiral Nakhimov"
      type  = battleship
      model = 0
    }
    division =
    { id    = { type = 18700 id = 214 }
      name  = "Pyotr Veliky"
      type  = battleship
      model = 0
    }
    division =
    { id    = { type = 18700 id = 215 }
      name  = "Marshal Ustinov"
      type  = battlecruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 216 }
      name  = "Bezuprechny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 217 }
      name  = "Gremyashchy"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 218 }
      name  = "Bezuderzhny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 219 }
      name  = "Besstrashny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 220 }
      name  = "Sovremenny II"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 221 }
      name  = "Sovremenny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 222 }
      name  = "Marshal Vasilyevsky"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 223 }
      name  = "Admiral Levchenko"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 224 }
      name  = "Admiral Chabanenko"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 225 }
      name  = "Admiral Kharlamov"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 226 }
      name  = "Severomorsk"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 227 }
    location = 133
    base     = 133
    name     = "15th Small ASW Brigade"
    division =
    { id    = { type = 18700 id = 228 }
      name  = "Tatarstan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 229 }
      name  = "Kedrov"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 230 }
      name  = "Zharki"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 231 }
      name  = "Legkiy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 232 }
      name  = "Dzerzhinsky"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 233 }
      name  = "Rezvyy"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 234 }
    location = 133
    base     = 133
    name     = "161st Submarine Brigade"
    division =
    { id    = { type = 18700 id = 235 }
      name  = "Vologda"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 236 }
      name  = "Vladikavkaz"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 237 }
      name  = "Magnitogorsk"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 238 }
      name  = "Kaluga"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 239 }
      name  = "Alrosa"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 240 }
      name  = "Novosibirsk"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 241 }
      name  = "B-404"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 242 }
      name  = "Tumenskyy Komsomolets"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 243 }
      name  = "B-425"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 244 }
      name  = "B-439"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 245 }
      name  = "B-445"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 246 }
      name  = "B-806"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 247 }
      name  = "B-515"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 18700 id = 248 }
      name  = "B-519"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 18700 id = 249 }
      name  = "B-546"
      type  = submarine
      model = 3
    }
  }
  navalunit =
  { id       = { type = 18700 id = 250 }
    location = 133
    base     = 133
    name     = "121st Landing Ship Brigade"
    division =
    { id    = { type = 18700 id = 251 }
      name  = "Mitrofan Moskalenko"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 18700 id = 252 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18700 id = 253 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 18700 id = 254 }
    location = 133
    base     = 133
    name     = "Northern Reserve Fleet"
    division =
    { id    = { type = 18700 id = 255 }
      name  = "Admiral Ushakov"
      strength = 1
      type  = battleship
      model = 0
    }
    division =
    { id    = { type = 18700 id = 256 }
      name  = "Bars"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 257 }
      name  = "Pantera"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 258 }
      name  = "Karp"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 259 }
      name  = "Pskov"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 260 }
      name  = "Kostroma"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 261 }
      name  = "Nizhny Novgorod"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 262 }
      name  = "Volgograd"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 263 }
      name  = "Perm"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 264 }
      name  = "K-69"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 265 }
      name  = "K-147"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 266 }
      name  = "K-255"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 267 }
      name  = "K-298"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 268 }
      name  = "K-299"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 269 }
      name  = "K-306"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 270 }
      name  = "K-314"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 271 }
      name  = "K-323"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 272 }
      name  = "K-324"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 273 }
      name  = "K-358"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 274 }
      name  = "K-367"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 275 }
      name  = "K-370"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 276 }
      name  = "K-371"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 277 }
      name  = "K-387"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 278 }
      name  = "K-438"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 279 }
      name  = "K-462"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 280 }
      name  = "K-469"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 281 }
      name  = "K-476"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 282 }
      name  = "K-495"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 283 }
      name  = "K-513"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 284 }
      name  = "K-517"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 285 }
      name  = "K-524"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 286 }
      name  = "K-527"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 287 }
      name  = "B-187"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 288 }
      name  = "B-190"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 289 }
      name  = "B-260"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 290 }
      name  = "B-345"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 291 }
      name  = "B-354"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 292 }
      name  = "B-394"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 18700 id = 293 }
    location = 510
    base     = 510
    name     = "12th Surface Ship Division"
    division =
    { id    = { type = 18700 id = 294 }
      name  = "Bespokoiny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 295 }
      name  = "Nastoychivy"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 296 }
      name  = "Vice-Admiral Kulakov"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 297 }
      name  = "Neustrashimyy"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 18700 id = 298 }
      name  = "Neukrotimy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 299 }
      name  = "Anadyr"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 300 }
      name  = "Pylkiy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 301 }
      name  = "Druzhnyy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 302 }
      name  = "Ladorny"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 303 }
    location = 510
    base     = 510
    name     = "71th Landing Ship Brigade"
    division =
    { id    = { type = 18700 id = 304 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18700 id = 305 }
      name  = "4th Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 18700 id = 306 }
    location = 187
    base     = 187
    name     = "25th Submarine Brigade"
    division =
    { id    = { type = 18700 id = 307 }
      name  = "B-880"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 308 }
      name  = "BN-529"
      type  = submarine
      model = 5
    }
  }
  navalunit =
  { id       = { type = 18700 id = 309 }
    location = 510
    base     = 510
    name     = "Baltic Reserve Fleet"
    division =
    { id    = { type = 18700 id = 310 }
      name  = "B-248"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 311 }
      name  = "Lipetsk"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 18700 id = 312 }
    location = 258
    base     = 258
    name     = "30th Surface Ship Division"
    division =
    { id    = { type = 18700 id = 313 }
      name  = "Moskva"
      type  = battlecruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 314 }
      name  = "Kerch"
      type  = battlecruiser
      model = 0
    }
    division =
    { id    = { type = 18700 id = 315 }
      name  = "Ochakov"
      type  = battlecruiser
      model = 0
    }
    division =
    { id    = { type = 18700 id = 316 }
      name  = "Smetlivyy"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 18700 id = 317 }
      name  = "Vorovsky"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 318 }
      name  = "Pytlivy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 319 }
      name  = "Ladny"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 320 }
      name  = "5th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18700 id = 321 }
      name  = "6th Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 18700 id = 322 }
    location = 258
    base     = 258
    name     = "Black Sea Reserve Fleet"
    division =
    { id    = { type = 18700 id = 323 }
      name  = "B-227"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 18700 id = 324 }
    location = 1372
    base     = 1372
    name     = "36th Missile Ship Division"
    division =
    { id       = { type = 18700 id = 325 }
      name     = "Admiral Lazarev"
      strength = 15
      type     = battleship
      model    = 0
    }
  }
  navalunit =
  { id       = { type = 18700 id = 326 }
    location = 1372
    base     = 1372
    name     = "16th Nuclear Submarine Squadron"
    division =
    { id    = { type = 18700 id = 327 }
      name  = "Delfin"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 328 }
      name  = "Kit"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 329 }
      name  = "Narval"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 330 }
      name  = "Morzh"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 331 }
      name  = "Drakon"
      type  = submarine
      model = 15
    }
    division =
    { id    = { type = 18700 id = 332 }
      name  = "Kashalot"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 18700 id = 333 }
      name  = "K-412"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 334 }
      name  = "K-454"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 335 }
      name  = "K-507"
      type  = submarine
      model = 13
    }
  }
  navalunit =
  { id       = { type = 18700 id = 336 }
    location = 1372
    base     = 1372
    name     = "19th Submarine Brigade"
    division =
    { id    = { type = 18700 id = 337 }
      name  = "B-464"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 338 }
      name  = "B-468"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 339 }
      name  = "B-470"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 340 }
      name  = "B-494"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 341 }
      name  = "B-807"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18700 id = 342 }
      name  = "B-213"
      type  = submarine
      model = 4
    }
  }
  navalunit =
  { id       = { type = 18700 id = 343 }
    location = 1372
    base     = 1372
    name     = "44th ASW Brigade"
    division =
    { id    = { type = 18700 id = 344 }
      name  = "Osmotritelny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 345 }
      name  = "Boyevoy"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 346 }
      name  = "Burny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 347 }
      name  = "Bystry"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 348 }
      name  = "Bezboyaznenny"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 349 }
      name  = "Admiral Spiridonov"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 350 }
      name  = "Marshal Shaposhnikov"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 351 }
      name  = "Admiral Vinogradov"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 352 }
      name  = "Admiral Panteleyev"
      type  = light_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 353 }
    location = 1372
    base     = 1372
    name     = "65th Surface Ship Brigade"
    division =
    { id    = { type = 18700 id = 354 }
      name  = "Varyag"
      strength = 35
      type  = battlecruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 355 }
      name  = "Letuchky"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 356 }
      name  = "Revnostnyy"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 357 }
      name  = "Menzhinsky"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18700 id = 358 }
      name  = "Storozhevoi"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 359 }
    location = 1372
    base     = 1372
    name     = "100th Landing Ship Brigade"
    division =
    { id    = { type = 18700 id = 360 }
      name  = "7th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 18700 id = 361 }
      name  = "8th Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 18700 id = 362 }
    location = 1372
    base     = 1372
    name     = "Pacific Submarine Fleet"
    division =
    { id    = { type = 18700 id = 363 }
      name  = "K-53"
      type  = submarine
      model = 12
    }
    division =
    { id    = { type = 18700 id = 364 }
      name  = "K-218"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 365 }
      name  = "K-242"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 366 }
      name  = "K-244"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 367 }
      name  = "K-247"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 368 }
      name  = "K-251"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 369 }
      name  = "K-254"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 370 }
      name  = "K-264"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 371 }
      name  = "K-305"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 372 }
      name  = "K-355"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 373 }
      name  = "K-360"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 374 }
      name  = "K-492"
      type  = submarine
      model = 13
    }
    division =
    { id    = { type = 18700 id = 375 }
      name  = "K-229"
      type  = submarine
      model = 13
    }
  }
  navalunit =
  { id       = { type = 18700 id = 376 }
    location = 133
    base     = 133
    name     = "Northern SSGN Fleet"
    division =
    { id    = { type = 18700 id = 377 }
      name  = "Krasnodar"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 378 }
      name  = "Voronezh"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 379 }
      name  = "Smolensk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 380 }
      name  = "Orel"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 381 }
      name  = "Verkhoturie"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 382 }
      name  = "Ekaterinburg"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 383 }
      name  = "Tula"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 384 }
      name  = "Bryansk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 385 }
      name  = "Karelia"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 386 }
      name  = "Novomoskovsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 387 }
      name  = "Arkhangelsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 388 }
      name  = "Severstal"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 389 }
      name  = "Dmitry Donskoy"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 390 }
      name  = "Vladimir"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 391 }
      name  = "K-129"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 392 }
      name  = "Borisoglebsk"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 393 }
      name  = "K-487"
      type  = heavy_cruiser
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18700 id = 394 }
    location = 1372
    base     = 1372
    name     = "Pacific SSGN Fleet"
    division =
    { id    = { type = 18700 id = 395 }
      name  = "Petropavlovsk-Kamchatskiy"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 396 }
      name  = "Podolsk"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 397 }
      name  = "K-180"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 398 }
      name  = "Svyatoy Georgiy Pobedonosets"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 399 }
      name  = "Zelenograd"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 400 }
      name  = "Ryazan"
      type  = heavy_cruiser
      model = 1
    }
    division =
    { id    = { type = 18700 id = 401 }
      name  = "Irkutsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 402 }
      name  = "Chelyabinsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 403 }
      name  = "Krasnoyarsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 404 }
      name  = "Viluchinsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 405 }
      name  = "Tomsk"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 18700 id = 406 }
      name  = "Omsk"
      type  = heavy_cruiser
      model = 2
    }
  }
  # ##########################################################
  # ##########################################################
  # AIR FORCE
  # #########################################################
  # ###########################################################
  airunit =
  { id       = { type = 18700 id = 100 }
    location = 175
    base     = 175
    name     = "22nd Heavy Bomber Air Division"
    division =
    { id       = { type = 18700 id = 101 }
      name     = "52nd Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 102 }
      name     = "184th Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 103 }
      name     = "840th Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 104 }
      name     = "121st Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 105 }
      name     = "U/I Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18700 id = 106 }
    location = 181
    base     = 181
    name     = "326th Heavy Bomber Air Division"
    division =
    { id       = { type = 18700 id = 107 }
      name     = "182nd Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 108 }
      name     = "79th Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 109 }
      name     = "200th Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 110 }
      name     = "444th Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 111 }
      name     = "U/I Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 112 }
      name     = "U/I Heavy Bomber Air Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18700 id = 113 }
    location = 175
    base     = 175
    name     = "12th Military Transport Air Division"
    division =
    { id       = { type = 18700 id = 114 }
      name     = "196th Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 115 }
      name     = "566th Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 116 }
      name     = "103rd Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 117 }
      name     = "110th Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 118 }
      name     = "117th Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 119 }
      name     = "334th Military Transport Air Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18700 id = 120 }
    location = 181
    base     = 181
    name     = "31st Moskva Air Defense Corps"
    division =
    { id       = { type = 18700 id = 121 }
      name     = "136th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 122 }
      name     = "138th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 123 }
      name     = "137th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 124 }
    location = 181
    base     = 181
    name     = "21st Moskva Air Defense Corps"
    division =
    { id       = { type = 18700 id = 125 }
      name     = "143rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 126 }
      name     = "144th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 127 }
      name     = "145th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 128 }
    location = 1843
    base     = 1843
    name     = "1st Composite Air Division"
    division =
    { id       = { type = 18700 id = 129 }
      name     = "559th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 130 }
      name     = "959th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 131 }
      name     = "368th Assault Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 132 }
      name     = "461st Assault Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 133 }
      name     = "960th Assault Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 134 }
    location = 1843
    base     = 1843
    name     = "535th Independent Composite Air Regiment"
    division =
    { id       = { type = 18700 id = 135 }
      name     = "535th Independent Composite Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 136 }
    location = 1843
    base     = 1843
    name     = "51st Air Defense Corps"
    division =
    { id       = { type = 18700 id = 137 }
      name     = "3rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 138 }
      name     = "19th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 139 }
      name     = "31st Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 140 }
    location = 187
    base     = 187
    name     = "21st Air Defense Corps"
    division =
    { id       = { type = 18700 id = 141 }
      name     = "9th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 142 }
      name     = "458th Interceptor Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 143 }
      name     = "10th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 144 }
    location = 187
    base     = 187
    name     = "54th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 145 }
      name     = "177th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 146 }
      name     = "159th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 147 }
      name     = "160th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 148 }
      name     = "161st Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 149 }
    location = 187
    base     = 187
    name     = "3rd Composite Air Division"
    division =
    { id       = { type = 18700 id = 150 }
      name     = "67th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 151 }
      name     = "722nd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 152 }
      name     = "723rd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 153 }
    location = 187
    base     = 187
    name     = "Baltic Sea Naval Aviation Division"
    division =
    { id       = { type = 18700 id = 154 }
      name     = "98th Guards Recon. Aviation Regiment"
      type     = naval_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 155 }
      name     = "99th Guards Recon. Aviation Regiment"
      type     = naval_bomber
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 156 }
    location = 1572
    base     = 1572
    name     = "28th Composite Air Division"
    division =
    { id       = { type = 18700 id = 157 }
      name     = "128th Independent Composite Air Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 158 }
      name     = "724th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 159 }
      name     = "999th Air Base Bomber Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 160 }
    location = 1547
    base     = 1547
    name     = "21st Composite Air Division"
    division =
    { id       = { type = 18700 id = 161 }
      name     = "2nd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 162 }
      name     = "266th Shturmovik Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 163 }
      name     = "267th Shturmovik Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 164 }
      name     = "313th Reconnaissance Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 165 }
      name     = "137th Composite Aviation Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 166 }
    location = 1572
    base     = 1572
    name     = "14th PVO Air Division"
    division =
    { id       = { type = 18700 id = 167 }
      name     = "120th Guards Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 168 }
      name     = "122nd Guards Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 169 }
      name     = "712th Interceptor Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 170 }
    location = 1371
    base     = 1371
    name     = "23rd PVO Air Corps"
    division =
    { id       = { type = 18700 id = 171 }
      name     = "22nd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 172 }
      name     = "530th Interceptor Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 173 }
      name     = "23rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 174 }
    location = 1371
    base     = 1371
    name     = "25th PVO Air Division"
    division =
    { id       = { type = 18700 id = 175 }
      name     = "23rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 176 }
      name     = "799th Reconnaissance Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 177 }
      name     = "800th Reconnaissance Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 178 }
    location = 1371
    base     = 1371
    name     = "303rd Composite Aviation Division"
    division =
    { id       = { type = 18700 id = 179 }
      name     = "277th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 180 }
      name     = "302nd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 181 }
      name     = "18th Shturmovik (Assault) Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 182 }
      name     = "187th Shturmovik Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 183 }
      name     = "257th Independent Composite Air Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 184 }
    location = 1371
    base     = 1371
    name     = "Pacific Fleet Air Forces"
    division =
    { id       = { type = 18700 id = 185 }
      name     = "866th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 186 }
      name     = "865th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 187 }
      name     = "867th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 188 }
      name     = "535th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 189 }
    location = 133
    base     = 133
    name     = "5th Naval Aviation Division"
    division =
    { id       = { type = 18700 id = 190 }
      name     = "574th Naval Aviation Regiment"
      type     = naval_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18700 id = 191 }
      name     = "976th Naval Aviation Regiment"
      type     = naval_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18700 id = 192 }
    location = 133
    base     = 133
    name     = "67th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 193 }
      name     = "231st Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 194 }
      name     = "232nd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 195 }
      name     = "233rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 196 }
    location = 133
    base     = 133
    name     = "68th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 197 }
      name     = "234th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 198 }
      name     = "235th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 199 }
      name     = "236th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 500 }
    location = 1572
    base     = 1572
    name     = "73rd Composite Aviation Division"
    division =
    { id       = { type = 18700 id = 501 }
      name     = "77th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 502 }
      name     = "852nd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 503 }
      name     = "853rd Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 504 }
      name     = "854th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 505 }
    location = 1572
    base     = 1572
    name     = "101st Composite Aviation Division"
    division =
    { id       = { type = 18700 id = 506 }
      name     = "855th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 507 }
      name     = "856th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 18700 id = 508 }
      name     = "857th Bomber Aviation Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 18700 id = 509 }
    location = 1572
    base     = 1572
    name     = "41st Air Defense Corps"
    division =
    { id       = { type = 18700 id = 510 }
      name     = "404th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 511 }
      name     = "431st Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 512 }
      name     = "473rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 513 }
    location = 1843
    base     = 1843
    name     = "56th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 514 }
      name     = "281st Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 515 }
      name     = "637th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 516 }
      name     = "621st Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 517 }
    location = 1843
    base     = 1843
    name     = "37th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 518 }
      name     = "333rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 519 }
      name     = "373rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 520 }
      name     = "377th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 521 }
    location = 1843
    base     = 1843
    name     = "88th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 522 }
      name     = "583rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 523 }
      name     = "839th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 524 }
      name     = "909th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 525 }
    location = 1371
    base     = 1371
    name     = "451st Air Defense Corps"
    division =
    { id       = { type = 18700 id = 526 }
      name     = "861st Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 527 }
      name     = "663rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 528 }
      name     = "584th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 529 }
    location = 1371
    base     = 1371
    name     = "169th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 530 }
      name     = "621st Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 531 }
      name     = "693rd Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 532 }
      name     = "474th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 533 }
    location = 181
    base     = 181
    name     = "68th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 534 }
      name     = "43rd Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 535 }
      name     = "126th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 536 }
      name     = "956th Fighter Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18700 id = 537 }
    location = 181
    base     = 181
    name     = "18th Air Defense Corps"
    division =
    { id       = { type = 18700 id = 538 }
      name     = "43rd Interceptor Aviation Regiment"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18700 id = 539 }
      name     = "496th Fighter Aviation Regiment"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
}
