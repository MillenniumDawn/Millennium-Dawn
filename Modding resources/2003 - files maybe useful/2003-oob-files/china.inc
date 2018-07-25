
##############################
# Country definition for CHC #
##############################

province =
{ id         = 1214
  naval_base = { size = 5 current_size = 5 }
}              # Yantai
province =
{ id         = 1239
  naval_base = { size = 10 current_size = 10 }
  air_base   = { size = 10 current_size = 10 }
}              # Ningbo

province =
{ id            = 1276
nuclear_reactor = { size = 7 current_size = 7 }
}               # Lanzhou

province =
{ id       = 1279
  air_base = { size = 10 current_size = 10 }
}            # Nanchong

province =
{ id         = 1321
  naval_base = { size = 10 current_size = 10 }
  air_base   = { size = 10 current_size = 10 }
}              # Hainan

province =
{ id       = 1380
  air_base = { size = 10 current_size = 10 }
}            # Qiqihar

province =
{ id          = 1205
  rocket_test = { size = 2 current_size = 2 }
}             # Beijing

province =
{ id       = 1433
  air_base = { size = 10 current_size = 10 }
}            # Urumqi

province =
{ id       = 1453
  air_base = { size = 8 current_size = 8 }
}            # Lhasa

#####################
# Country main data #
#####################

country =
{ tag                 = CHC
  # Resource Reserves
  nuke                = 40
  energy              = 8000
  metal               = 4000
  rare_materials      = 2000
  oil                 = 2000
  supplies            = 5000
  money               = 2000
  manpower            = 1260
  transports          = 600
  escorts             = 20
  capital             = 1205
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 9
    free_market       = 6
    freedom           = 4
    professional_army = 8
    defense_lobby     = 3
    interventionism   = 6
  }
  SpyInfo             = { country = "ENG" NumberOfSpies = 6 }
  SpyInfo             = { country = "FRA" NumberOfSpies = 5 }
  SpyInfo             = { country = "GER" NumberOfSpies = 5 }
  SpyInfo             = { country = "USA" NumberOfSpies = 8 }
  SpyInfo             = { country = "CAN" NumberOfSpies = 5 }
  SpyInfo             = { country = "U09" NumberOfSpies = 3 }
  SpyInfo             = { country = "RUS" NumberOfSpies = 3 }
  SpyInfo             = { country = "PER" NumberOfSpies = 2 }
  SpyInfo             = { country = "JAP" NumberOfSpies = 8 }
  SpyInfo             = { country = "SYR" NumberOfSpies = 1 }
  SpyInfo             = { country = "UKR" NumberOfSpies = 3 }
  SpyInfo             = { country = "ITA" NumberOfSpies = 4 }
  SpyInfo             = { country = "PAK" NumberOfSpies = 2 }
  SpyInfo             = { country = "IND" NumberOfSpies = 6 }
  SpyInfo             = { country = "TRA" NumberOfSpies = 7 }
  SpyInfo             = { country = "WLL" NumberOfSpies = 4 }
  SpyInfo             = { country = "ISR" NumberOfSpies = 3 }
  SpyInfo             = { country = "AST" NumberOfSpies = 6 }
  nationalprovinces   = { 1305 1293 1282 1281 1327 1307 1308 1309 1325 1320 1321 1319 1310 1318 1312 1311 1313 1317 1314 1360 1361 1362 1363 1364 1365
                          1277 1275 1269 1268 1267 1266 1279 1280 1265 1264 1263 1262 1261 1260 1259 1258 1257 1256 1255 1254 1253 1252 1251 1250 1249
                          1248 1247 1246 1245 1244 1243 1242 1241 1240 1239 1238 1237 1236 1235 1234 1233 1232 1231 1230 1229 1228 1227 1226 1225 1224
                          1223 1222 1221 1220 1219 1218 1217 1216 1215 1214 1213 1212 1211 1210 1209 1208 1207 1206 1205 1270 1271 1273 1203 1204 1316
                          1394 1395 1396 1397 1389 1390 1377 1378 1375 1374 1379 1530 1380 1387 1382 1381 1398 1386 1388 1202 1439 1440 1441 1442 1443
                          1444 1448 1450 1451 1452 1453 1283 1421 1433 1432 1435 1445 1447 1446 1431 1430 1274 1276 1294 1315 1272 1278 1878 1877 1474
                          1385 1322 1323 1324 1681
                        }
  ownedprovinces      = { 1305 1293 1282 1281 1327 1307 1308 1309 1325 1320 1321 1319 1310 1318 1312 1311 1313 1317 1314 1360 1361 1362 1363 1364 1365
                          1277 1275 1269 1268 1267 1266 1279 1280 1265 1264 1263 1262 1261 1260 1259 1258 1257 1256 1255 1254 1253 1252 1251 1250 1249
                          1248 1247 1246 1245 1244 1243 1242 1241 1240 1239 1238 1237 1236 1235 1234 1233 1232 1231 1230 1229 1228 1227 1226 1225 1224
                          1223 1222 1221 1220 1219 1218 1217 1216 1215 1214 1213 1212 1211 1210 1209 1208 1207 1206 1205 1270 1271 1273 1203 1204 1316
                          1394 1395 1396 1397 1389 1390 1377 1378 1375 1374 1379 1530 1380 1387 1382 1381 1398 1386 1388 1202 1439 1440 1441 1442 1443
                          1444 1448 1450 1451 1452 1453 1283 1421 1433 1432 1435 1445 1447 1446 1431 1430 1274 1276 1294 1315 1272 1278
                        }
  controlledprovinces = { 1305 1293 1282 1281 1327 1307 1308 1309 1325 1320 1321 1319 1310 1318 1312 1311 1313 1317 1314 1360 1361 1362 1363 1364 1365
                          1277 1275 1269 1268 1267 1266 1279 1280 1265 1264 1263 1262 1261 1260 1259 1258 1257 1256 1255 1254 1253 1252 1251 1250 1249
                          1248 1247 1246 1245 1244 1243 1242 1241 1240 1239 1238 1237 1236 1235 1234 1233 1232 1231 1230 1229 1228 1227 1226 1225 1224
                          1223 1222 1221 1220 1219 1218 1217 1216 1215 1214 1213 1212 1211 1210 1209 1208 1207 1206 1205 1270 1271 1273 1203 1204 1316
                          1394 1395 1396 1397 1389 1390 1377 1378 1375 1374 1379 1530 1380 1387 1382 1381 1398 1386 1388 1202 1439 1440 1441 1442 1443
                          1444 1448 1450 1451 1452 1453 1283 1421 1433 1432 1435 1445 1447 1446 1431 1430 1274 1276 1294 1315 1272 1278
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2000 2010 
					2050 2060 2070
					2110 2120
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1970 1960 1980 1990
					1000 1010
					1050 1060 1070
					1110 1120
					1900 1910 1920
					1260 1270
					1600
					1800 1810
					1700
					1300 1400
					1310 1410 
					1320 1420
					1500 1200
					1510 1210
					1520 1220
					#Aircraft
					4000 4010 4020
					4100 4110 4120 4130
					4200 4210
                                        4500
					4510 4520
					4400 4410
					4300 4310
					4640 4650
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910
					4550
					#Land Docs
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6010 6030 6040
					6930
					6600 6620
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9080 9090 9100 9110 9120
					9130 9140 9150 9160 9170 9180 9190 9200
					#Secret Weapons
					7010
					7060 7070
					7020 7030 7040 7050
					7100 7110 7120
					7180 7190 7200
                                        7330 7310 7320
                                        #Navy
                                        3000 3010 3020
                                        3100 3110
                                        3500 3510 3520
                                        3590
                                        3700 37700 3710 37710 3720 37720
                                        3800 3810 38810 3820
                                        3850 3860 3870
                                        3900 3910 3920
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                                        8300 8310
                                        8800
                        }
  blueprints          = { 3030 }
  diplomacy =
  { relation = { tag = NOR value = 50 }
    relation = { tag = SWE value = 50 }
    relation = { tag = FIN value = 50 }
    relation = { tag = DEN value = 50 }
    relation = { tag = IRE value = 50 }
    relation = { tag = ENG value = 50 }
    relation = { tag = GER value = 50 }
    relation = { tag = HOL value = 50 }
    relation = { tag = BEL value = 50 }
    relation = { tag = FRA value = 50 }
    relation = { tag = SPA value = 50 }
    relation = { tag = POR value = 50 }
    relation = { tag = ITA value = 50 }
    relation = { tag = BLR value = 150 }
    relation = { tag = MON value = 100 }
    relation = { tag = TRK value = 100 }
    relation = { tag = BRA value = 50 }
    relation = { tag = CHL value = 100 }
    relation = { tag = ARG value = 100 }
    relation = { tag = USA value = 50 }
    relation = { tag = KOR value = -50 }
    relation = { tag = JAP value = -100 }
    relation = { tag = CAL value = 150 access = yes }
    relation = { tag = SIA value = 150 }
    relation = { tag = SYR value = 100 }
    relation = { tag = LBY value = 100 }
    relation = { tag = CUB value = 150 }
    relation = { tag = IND value = 100 }
    relation =
    { tag        = RUS
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
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
    { tag        = KYG
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = TAJ
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = PER
      value      = 150
    }
    relation =
    { tag        = PAK
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = U09
      value      = 100
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = VEN
      value      = 150
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation =
    { tag        = BUR
      value      = 130
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation = { tag = ANG value = 150 access = yes }
    relation = { tag = SUD value = 150 access = yes }
    relation = { tag = EUS value = 150 access = yes }
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8300 id = 1 }
    location = 1389
    name     = "Shenyang Military Region"
    division =
    { id            = { type = 8300 id = 2 }
      name          = "Shenyang MR"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 3 }
    location = 1378
    name     = "16th Group Army"
    division =
    { id       = { type = 8300 id = 4 }
      name     = "46th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id            = { type = 8300 id = 5 }
      name          = "4th Armored Division"
      strength      = 100
      type          = armor
      model         = 12
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 6 }
      name     = "U/I Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 7 }
    location = 1382
    name     = "23rd Group Army"
    division =
    { id       = { type = 8300 id = 8 }
      name     = "69th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 9 }
      name     = "67th Mechanized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 10 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 11 }
      name     = "69th Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 12 }
    location = 1394
    name     = "39th Mechanized Group Army"
    division =
    { id            = { type = 8300 id = 13 }
      name          = "39th Group Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 14 }
      name     = "115th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 15 }
      name     = "116th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 16 }
      name     = "190th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 17 }
      name     = "3rd Armored Division"
      strength = 100
      type     = armor
      model    = 13
    }
  }
  landunit =
  { id       = { type = 8300 id = 18 }
    location = 1219
    name     = "40th Group Army"
    division =
    { id       = { type = 8300 id = 19 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 20 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 21 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 22 }
      name     = "U/I Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 23 }
    location = 1395
    name     = "Liaoning Military District"
    division =
    { id       = { type = 8300 id = 24 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 30 }
    location = 1309
    name     = "24th Group Army"
    division =
    { id       = { type = 8300 id = 31 }
      name     = "70th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 32 }
      name     = "71st Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 33 }
      name     = "1st Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
  }
  landunit =
  { id       = { type = 8300 id = 34 }
    location = 1394
    name     = "27th Group Army"
    division =
    { id       = { type = 8300 id = 36 }
      name     = "135th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id            = { type = 8300 id = 37 }
      name          = "7th Army Helicopter Regiment"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id       = { type = 8300 id = 38 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 5
    }
  }
  landunit =
  { id       = { type = 8300 id = 39 }
    location = 1394
    name     = "38th Mechanized Group Army"
    division =
    { id            = { type = 8300 id = 40 }
      name          = "38th Group Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 41 }
      name     = "6th Armored Division"
      strength = 100
      type     = armor
      model    = 13
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 42 }
      name     = "112th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 43 }
      name     = "113th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 44 }
      name     = "114th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 45 }
    location = 1225
    name     = "63rd Group Army"
    division =
    { id            = { type = 8300 id = 46 }
      name          = "63rd Group Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 48 }
      name     = "188th Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 49 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 50 }
      name     = "U/I Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 51 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 4
    }
  }
  landunit =
  { id       = { type = 8300 id = 52 }
    location = 1206
    name     = "65th Group Army"
    division =
    { id       = { type = 8300 id = 53 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 4
    }
    division =
    { id       = { type = 8300 id = 54 }
      name     = "U/I Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 55 }
      name     = "207th Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 56 }
      name     = "193rd Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 63 }
    location = 1294
    name     = "21st Group Army"
    division =
    { id       = { type = 8300 id = 64 }
      name     = "12th Armored Division"
      strength = 100
      type     = armor
      model    = 12
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 65 }
      name     = "U/I Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 66 }
      name     = "U/I Motorized Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 67 }
    location = 1430
    name     = "47th Group Army"
    division =
    { id       = { type = 8300 id = 68 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 69 }
      name     = "U/I Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 70 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 71 }
    location = 1433
    name     = "Xinjiang Military District"
    division =
    { id       = { type = 8300 id = 72 }
      name     = "U/I Highland Mot. Inf. Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 73 }
      name     = "8th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 74 }
      name     = "U/I Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
    division =
    { id            = { type = 8300 id = 75 }
      name          = "3rd Army Helicopter Regiment"
      strength      = 100
      type          = militia
      model         = 2
    }
    division =
    { id       = { type = 8300 id = 79 }
      name     = "76th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 80 }
    location = 1216
    name     = "Jinan Military Region"
    division =
    { id            = { type = 8300 id = 81 }
      name          = "Jinan MR"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 3
    }
  }
  landunit =
  { id       = { type = 8300 id = 82 }
    location = 1208
    name     = "20th Group Army"
    division =
    { id       = { type = 8300 id = 83 }
      name     = "U/I Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
    division =
    { id       = { type = 8300 id = 84 }
      name     = "58th Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 85 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 86 }
    location = 1214
    name     = "26th Group Army"
    division =
    { id            = { type = 8300 id = 87 }
      name          = "26th Army Group HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 88 }
      name     = "8th Armored Division"
      strength = 100
      type     = armor
      model    = 13
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 89 }
      name     = "138th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 90 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 91 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 93 }
    location = 1325
    name     = "54th Group Army"
    division =
    { id       = { type = 8300 id = 94 }
      name     = "127th Lt. Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 95 }
      name     = "162nd Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 96 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 97 }
      name     = "33rd Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 5
    }
  }
  landunit =
  { id       = { type = 8300 id = 98 }
    location = 1216
    name     = "Shandong Military District"
    division =
    { id       = { type = 8300 id = 99 }
      name     = "76th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 100 }
      name     = "136th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 101 }
    location = 1235
    name     = "Nanjing Military Region"
    division =
    { id            = { type = 8300 id = 102 }
      name          = "Nanjing MR"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 3
    }
  }
  landunit =
  { id       = { type = 8300 id = 103 }
    location = 1241
    name     = "1st Group Army"
    division =
    { id            = { type = 8300 id = 104 }
      name          = "1st Amph. Mechanized Infantry Division"
      strength      = 100
      type          = marine
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 105 }
      name     = "U/I Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
    division =
    { id       = { type = 8300 id = 106 }
      name     = "U/I Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 107 }
    location = 1236
    name     = "12th Group Army"
    division =
    { id       = { type = 8300 id = 108 }
      name     = "2nd Armored Division"
      strength = 100
      type     = armor
      model    = 13
    }
    division =
    { id       = { type = 8300 id = 109 }
      name     = "179th Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 110 }
      name     = "34th Motorized Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 111 }
      name     = "36th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 112 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 113 }
    location = 1247
    name     = "31st Group Army"
    division =
    { id       = { type = 8300 id = 114 }
      name     = "91st Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 115 }
      name     = "86th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 116 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 121 }
    location = 1313
    name     = "Guangzhou Military Region"
    division =
    { id            = { type = 8300 id = 122 }
      name          = "Guangzhou MR"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 123 }
    location = 1310
    name     = "41st Group Army"
    division =
    { id       = { type = 8300 id = 124 }
      name     = "123rd Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 125 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 5
    }
    division =
    { id            = { type = 8300 id = 126 }
      name          = "126th Amph. Mechanized Division"
      strength      = 100
      type          = marine
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 127 }
    location = 1325
    name     = "42nd Group Army"
    division =
    { id            = { type = 8300 id = 128 }
      name          = "124th Amph. Mechanized Division"
      strength      = 100
      type          = marine
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 8300 id = 129 }
      name          = "144th Amph. Mechanized Division"
      strength      = 100
      type          = marine
      model         = 16
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 8300 id = 130 }
      name     = "U/I Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 5
    }
  }
  landunit =
  { id       = { type = 8300 id = 139 }
    location = 1360
    name     = "Chengdu Military Region"
    division =
    { id            = { type = 8300 id = 140 }
      name          = "Chengdu MR"
      strength      = 100
      type          = hq
      model         = 1
      extra         = sp_rct_artillery
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 141 }
    location = 1307
    name     = "13th Group Army Chongqing"
    division =
    { id       = { type = 8300 id = 142 }
      name     = "37th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 143 }
      name     = "149th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 144 }
      name     = "U/I Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
  }
  landunit =
  { id       = { type = 8300 id = 145 }
    location = 1307
    name     = "14th Group Army"
    division =
    { id       = { type = 8300 id = 146 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 147 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 148 }
      name     = "U/I Armored Division"
      strength = 100
      type     = armor
      model    = 8
    }
  }
  landunit =
  { id       = { type = 8300 id = 149 }
    location = 1453
    name     = "Xizang Military District"
    division =
    { id       = { type = 8300 id = 150 }
      name     = "52nd Mountain Infantry Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 8300 id = 151 }
      name     = "53rd Mountain Infantry Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id            = { type = 8300 id = 154 }
      name          = "2nd Army Helicopter Regiment"
      strength      = 100
      type          = militia
      model         = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 152 }
    location = 1364
    name     = "Sichuan Military District"
    division =
    { id       = { type = 8300 id = 156 }
      name     = "121st Infantry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8300 id = 157 }
    location = 1321
    name     = "PLA Marine Corps"
    division =
    { id       = { type = 8300 id = 158 }
      name     = "1st Marine Brigade"
      strength = 100
      type     = marine
      model    = 12
    }
    division =
    { id       = { type = 8300 id = 159 }
      name     = "2nd Marine Brigade"
      strength = 100
      type     = marine
      model    = 12
    }
  }
  landunit =
  { id       = { type = 8300 id = 160 }
    location = 1321
    name     = "15th Airborne Corps"
    division =
    { id       = { type = 8300 id = 161 }
      name     = "127th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 162 }
      name     = "128th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 163 }
      name     = "129th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 164 }
      name     = "130th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 165 }
      name     = "131st Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 167 }
      name     = "132nd Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 168 }
      name     = "133rd Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 169 }
      name     = "134th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 8300 id = 170 }
      name     = "135th Parachute Regiment"
      strength = 100
      type     = paratrooper
      model    = 15
    }
  }
  landunit =
  { id       = { type = 8300 id = 171 }
    location = 1430
    name     = "Xinjiang Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 172 }
      name          = "'Brave Tigers' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 173 }
    location = 1235
    name     = "Nanjing Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 174 }
      name          = "'Flying Dragons' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 175 }
    location = 1205
    name     = "Beijing Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 176 }
      name          = "'Divine Sword' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 177 }
    location = 1390
    name     = "Shenyang Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 178 }
      name          = "'Tigers of Northeast' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 179 }
    location = 1276
    name     = "Lanzhou Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 180 }
      name          = "'Tigers of the Night' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 181 }
    location = 1216
    name     = "Jinan Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 182 }
      name          = "'Eagle' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 183 }
    location = 1313
    name     = "Guangzhou Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 184 }
      name          = "'Sharp Sword' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 8300 id = 185 }
      name          = "6th Army Helicopter Regiment"
      strength      = 100
      type          = militia
      model         = 2
    }
  }
  landunit =
  { id       = { type = 8300 id = 186 }
    location = 1360
    name     = "Chengdu Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 187 }
      name          = "'Falcons of Southwest' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8300 id = 188 }
    location = 1305
    name     = "Yunnan Special Operations Group"
    division =
    { experience    = 10
      id            = { type = 8300 id = 189 }
      name          = "'Hunting Leopard' Spec. Op. Unit"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 8300 id = 400 }
    location = 1321
    base     = 1321
    name     = "South Sea Fleet"
    division =
    { id    = { type = 8300 id = 401 }
      name  = "Shenzhen"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 8300 id = 402 }
      name  = "Zhuhai"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 403 }
      name  = "Changsha"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 404 }
      name  = "Nanning"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 405 }
      name  = "Nanchang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 406 }
      name  = "Guilin"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 407 }
      name  = "Zhanjiang"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 408 }
      name  = "Anshun"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 409 }
      name  = "Zhaodong"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 410 }
      name  = "Jishou"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 411 }
      name  = "Xiangtan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 412 }
      name  = "Kangding"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 413 }
      name  = "Dongwan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 414 }
      name  = "Shantou"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 415 }
      name  = "Jiangmen"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 416 }
      name  = "Foshan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 417 }
      name  = "Yichang"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 418 }
      name  = "Yulin"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 419 }
      name  = "Yuxi"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 420 }
      name  = "Xiangfan"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 421 }
      name  = "SSK-358"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 422 }
      name  = "SSK-359"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 423 }
      name  = "SSK-360"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 424 }
      name  = "SSK-361"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 425 }
      name  = "SSK-362"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 426 }
      name  = "SSK-363"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 427 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 428 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 429 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 430 }
      name  = "4th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 431 }
      name  = "5th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 432 }
      name  = "6th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 520 }
      name  = "7th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 521 }
      name  = "8th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 522 }
      name  = "9th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 523 }
      name  = "10th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 524 }
      name  = "11th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 525 }
      name  = "12th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 526 }
      name  = "13th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 527 }
      name  = "14th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 528 }
      name  = "15th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 529 }
      name  = "16th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 530 }
      name  = "17th Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8300 id = 531 }
      name  = "18th Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 8300 id = 433 }
    location = 1214
    base     = 1214
    name     = "North Sea Fleet"
    division =
    { id    = { type = 8300 id = 434 }
      name  = "Jinan"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 435 }
      name  = "Xi'an"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 436 }
      name  = "Yinchuan"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 437 }
      name  = "Xining"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 438 }
      name  = "Xining"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 439 }
      name  = "Kaifeng"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 440 }
      name  = "Dalian"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 441 }
      name  = "Harbin"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 8300 id = 442 }
      name  = "Qingdao"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 8300 id = 443 }
      name  = "Changzhi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 444 }
      name  = "Linfen"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 445 }
      name  = "Siping"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 446 }
      name  = "Dandong"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 447 }
      name  = "Maoming"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 448 }
      name  = "Yibing"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 449 }
      name  = "SSN-401"
      type  = submarine
      model = 11
    }
    division =
    { id    = { type = 8300 id = 450 }
      name  = "SSN-402"
      type  = submarine
      model = 11
    }
    division =
    { id    = { type = 8300 id = 451 }
      name  = "SSN-403"
      type  = submarine
      model = 11
    }
    division =
    { id    = { type = 8300 id = 452 }
      name  = "SSN-404"
      type  = submarine
      model = 11
    }
    division =
    { id    = { type = 8300 id = 453 }
      name  = "SSN-405"
      type  = submarine
      model = 11
    }
    division =
    { id    = { type = 8300 id = 454 }
      name  = "SSN-407"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 8300 id = 455 }
      name  = "SSGN-406"
      type  = heavy_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 456 }
      name  = "SSK-213"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 457 }
      name  = "SSK-214"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 458 }
      name  = "SSK-342"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 459 }
      name  = "SSK-352"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 460 }
      name  = "SSK-353"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 461 }
      name  = "SSK-354"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 462 }
      name  = "SSK-356"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 8300 id = 463 }
      name  = "SSK-351"
      type  = submarine
      model = 1
    }
  }
  navalunit =
  { id       = { type = 8300 id = 464 }
    location = 1239
    base     = 1239
    name     = "East Sea Fleet"
    division =
    { id    = { type = 8300 id = 465 }
      name  = "Nanjing"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 467 }
      name  = "Hefei"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 468 }
      name  = "Chongqing"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 469 }
      name  = "Zunyi"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8300 id = 470 }
      name  = "Hangzhou"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 8300 id = 471 }
      name  = "Fuzhou"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 8300 id = 472 }
      name  = "Shaoxing"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 473 }
      name  = "Nantong"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 474 }
      name  = "Wuxi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 475 }
      name  = "Huaiyin"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 476 }
      name  = "Zhenjiang"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 477 }
      name  = "Xiamen"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 478 }
      name  = "Jiujiang"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 479 }
      name  = "Nanping"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 480 }
      name  = "Ji'an"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 481 }
      name  = "Jiaxing"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 482 }
      name  = "Lianyungang"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 483 }
      name  = "Sanming"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 484 }
      name  = "Putian"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 485 }
      name  = "Luoyang"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 486 }
      name  = "Mianyang"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 487 }
      name  = "Ningbo"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 488 }
      name  = "Jinhua"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 489 }
      name  = "Huangshi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 490 }
      name  = "Wuhu"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 491 }
      name  = "Cangzhou"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8300 id = 492 }
      name  = "Anqing"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 493 }
      name  = "Huainan"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 494 }
      name  = "Huaibei"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 495 }
      name  = "Tongling"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 8300 id = 496 }
      name  = "SSK-364"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 8300 id = 497 }
      name  = "SSK-365"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 8300 id = 498 }
      name  = "SSK-366"
      type  = submarine
      model = 5
    }
    division =
    { id    = { type = 8300 id = 499 }
      name  = "SSK-367"
      type  = submarine
      model = 5
    }
    division =
    { id    = { type = 8300 id = 500 }
      name  = "SSK-320"
      type  = submarine
      model = 2
  }
    division =
    { id    = { type = 8300 id = 501 }
      name  = "SSK-321"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 8300 id = 502 }
      name  = "SSK-322"
      type  = submarine
      model = 3
    }
}
navalunit =
  { id       = { type = 8300 id = 503 }
    location = 1239
    base     = 1239
    name     = "Submarine Reserve Fleet"
    division =
    { id    = { type = 8300 id = 504 }
      name  = "SSK-250"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 505 }
      name  = "SSK-251"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 506 }
      name  = "SSK-252"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 507 }
      name  = "SSK-253"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 508 }
      name  = "SSK-254"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 509 }
      name  = "SSK-255"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 510 }
      name  = "SSK-256"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 511 }
      name  = "SSK-257"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 512 }
      name  = "SSK-258"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 8300 id = 513 }
      name  = "SSK-259"
      type  = submarine
      model = 0
    }
}
  navalunit =
  { id       = { type = 8300 id = 514 }
    location = 1214
    base     = 1214
    name     = "Varyag Strike Group"
    division =
    { id            = { type = 8300 id = 515 }
      name          = "Varyag"
      strength      = 5
      type          = escort_carrier
      model         = 7
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 8300 id = 200 }
    location = 1453
    base     = 1453
    name     = "1st Fighter Wing"
    division =
    { id       = { type = 8300 id = 201 }
      name     = "1st Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 202 }
      name     = "2nd Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 203 }
      name     = "3rd Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 204 }
    location = 1453
    base     = 1453
    name     = "2nd Fighter Wing"
    division =
    { id       = { type = 8300 id = 205 }
      name     = "4th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 206 }
      name     = "5th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 207 }
      name     = "6th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 208 }
    location = 1321
    base     = 1321
    name     = "30th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 209 }
      name     = "34th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 210 }
      name     = "22nd Ground Attack Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 211 }
      name     = "35th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 8300 id = 212 }
    location = 1239
    base     = 1239
    name     = "3rd Fighter Wing"
    division =
    { id       = { type = 8300 id = 213 }
      name     = "7th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 214 }
      name     = "8th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 215 }
      name     = "9th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 216 }
    location = 1239
    base     = 1239
    name     = "4th Fighter Wing"
    division =
    { id       = { type = 8300 id = 217 }
      name     = "10th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 218 }
      name     = "11th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 219 }
      name     = "12th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 220 }
    location = 1239
    base     = 1239
    name     = "5th Fighter Wing"
    division =
    { id       = { type = 8300 id = 221 }
      name     = "13th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 222 }
      name     = "14th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 223 }
      name     = "15th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 8300 id = 224 }
    location = 1433
    base     = 1433
    name     = "6th Fighter Wing"
    division =
    { id       = { type = 8300 id = 225 }
      name     = "16th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 226 }
      name     = "17th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 227 }
      name     = "18th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 228 }
    location = 1279
    base     = 1279
    name     = "7th Fighter Wing"
    division =
    { id       = { type = 8300 id = 229 }
      name     = "19th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 230 }
      name     = "20th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 231 }
      name     = "21st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 232 }
    location = 1279
    base     = 1279
    name     = "8th Fighter Wing"
    division =
    { id       = { type = 8300 id = 233 }
      name     = "22nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 234 }
      name     = "23rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 235 }
      name     = "24th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 236 }
    location = 1279
    base     = 1279
    name     = "9th Fighter Wing"
    division =
    { id       = { type = 8300 id = 237 }
      name     = "25th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 238 }
      name     = "26th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 239 }
      name     = "27th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 240 }
    location = 1279
    base     = 1279
    name     = "10th Fighter Wing"
    division =
    { id       = { type = 8300 id = 241 }
      name     = "28th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 242 }
      name     = "29th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 243 }
      name     = "30th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 244 }
    location = 1279
    base     = 1279
    name     = "11th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 245 }
      name     = "31st Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 246 }
      name     = "32nd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 247 }
      name     = "33rd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 248 }
    location = 1321
    base     = 1321
    name     = "44th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 249 }
      name     = "12th Ground Attack Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 250 }
      name     = "36th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 251 }
      name     = "37th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 8300 id = 252 }
    location = 1321
    base     = 1321
    name     = "6th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 253 }
      name     = "13th Ground Attack Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 254 }
      name     = "38th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 8300 id = 255 }
      name     = "39th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 8300 id = 256 }
    location = 1239
    base     = 1239
    name     = "12th Fighter Wing"
    division =
    { id       = { type = 8300 id = 257 }
      name     = "40th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 8300 id = 258 }
      name     = "41st Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 8300 id = 259 }
      name     = "42nd Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 8300 id = 260 }
    location = 1321
    base     = 1321
    name     = "13th Fighter Wing"
    division =
    { id       = { type = 8300 id = 261 }
      name     = "43rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 262 }
      name     = "44th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 263 }
      name     = "45th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 264 }
    location = 1453
    base     = 1453
    name     = "10th Bomber Wing"
    division =
    { id       = { type = 8300 id = 265 }
      name     = "28th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 266 }
      name     = "29th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 267 }
      name     = "30th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 268 }
    location = 1321
    base     = 1321
    name     = "14th Fighter Wing"
    division =
    { id       = { type = 8300 id = 269 }
      name     = "46th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 270 }
      name     = "47th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 271 }
      name     = "48th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 272 }
    location = 1380
    base     = 1380
    name     = "28th Figther Wing"
    division =
    { id       = { type = 8300 id = 273 }
      name     = "49th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 274 }
      name     = "50th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 275 }
      name     = "51st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 276 }
    location = 1380
    base     = 1380
    name     = "26th Fighter Wing"
    division =
    { id       = { type = 8300 id = 277 }
      name     = "52nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 278 }
      name     = "53rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 279 }
      name     = "54th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 280 }
    location = 1453
    base     = 1453
    name     = "44th Fighter Wing"
    division =
    { id       = { type = 8300 id = 281 }
      name     = "55th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 282 }
      name     = "56th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 283 }
      name     = "57th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 284 }
    location = 1239
    base     = 1239
    name     = "36th Bomber Wing"
    division =
    { id       = { type = 8300 id = 285 }
      name     = "106th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 286 }
      name     = "107th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 312 }
      name     = "108th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 313 }
      name     = "109th Bomber Regiment"
      type     = strategic_bomber
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 287 }
    location = 1433
    base     = 1433
    name     = "46th Air Wing"
    division =
    { id       = { type = 8300 id = 288 }
      name     = "58th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 289 }
      name     = "59th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 8300 id = 290 }
      name     = "60th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 291 }
    location = 1239
    base     = 1239
    name     = "PLA Air Transport Command"
    division =
    { id       = { type = 8300 id = 292 }
      name     = "1st Air Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 293 }
      name     = "2nd Air Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 294 }
      name     = "3rd Air Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 295 }
      name     = "4th Air Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 8300 id = 296 }
    location = 1453
    base     = 1453
    name     = "19th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 297 }
      name     = "181st Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 298 }
      name     = "322nd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 299 }
      name     = "75th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 300 }
      name     = "75th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 301 }
    location = 1433
    base     = 1433
    name     = "18th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 302 }
      name     = "99th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 303 }
      name     = "49th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 304 }
      name     = "101st Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 305 }
      name     = "86th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 8300 id = 306 }
    location = 1433
    base     = 1433
    name     = "17th Ground Attack Wing"
    division =
    { id       = { type = 8300 id = 307 }
      name     = "182nd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 308 }
      name     = "327th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 309 }
      name     = "275th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 310 }
      name     = "175th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8300 id = 311 }
      name     = "78th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 8300 id = 550 }
    name  = "Ma'anshan"
    type  = destroyer
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 551 }
    name  = "Wenzhou"
    type  = destroyer
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 552 }
    name  = "SSK-323"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 553 }
    name  = "SSK-324"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 554 }
    name  = "SSK-325"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 555 }
    name  = "SSK-326"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 556 }
    name  = "SSK-313"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 557 }
    name  = "SSK-314"
    type  = submarine
    model = 3
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 558 }
    name  = "SSK-368"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 559 }
    name  = "SSK-369"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 560 }
    name  = "SSK-370"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 561 }
    name  = "SSK-371"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 562 }
    name  = "SSK-372"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 563 }
    name  = "SSK-373"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 564 }
    name  = "SSK-374"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 565 }
    name  = "SSK-375"
    type  = submarine
    model = 5
    cost  = 5
    date  = { day = 2 month = september year = 2003 }
  }
  division_development =
  { id    = { type = 8300 id = 566 }
    name  = "SSK-330"
    type  = submarine
    model = 6
    cost  = 5
    date  = { day = 2 month = april year = 2004 }
  }
}