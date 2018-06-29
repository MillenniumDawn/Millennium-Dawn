
##############################
# Country definition for EAF #
##############################

province =
{ id       = 1035
  naval_base = { size = 2 current_size = 2 }
}            # 
country =
{ tag                 = EAF
  regular_id          = SOM
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 1035
  manpower            = 12
  transports          = 20
  escorts             = 0
  diplomacy           = { 
}
  nationalprovinces   = { 1035 1036 }
  ownedprovinces      = { 1035 1036 }
  controlledprovinces = { 1035 1036 }
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
                                        #Land Docs
					6010 6020 
					6910
					6100 6110 6120
                                        6160
					6600 6610
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1980
					1900
                                        #Secret Tech:
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 7
    free_market       = 5
    freedom           = 7
    professional_army = 3
    defense_lobby     = 8
    interventionism   = 8
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12282 id = 1 }
    location = 1036
    name     = "I. Corps al-Somaliland"
    division =
    { id            = { type = 12282 id = 2 }
      name          = "1st mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
    division =
    { id            = { type = 12282 id = 3 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12282 id = 4 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12282 id = 5 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
}