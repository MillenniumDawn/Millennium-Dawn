
##############################
# Country definition for IRQ #
##############################

province =
{ id         = 1823
  naval_base = { size = 4 current_size = 4 }
}              # Basrah

province =
{ id         = 1866
  air_base = { size = 6 current_size = 6 }
}              # Bagdadh

country =
{ tag                 = IRQ
  # Resource Reserves
  energy              = 500
  metal               = 300
  rare_materials      = 200
  oil                 = 1000
  supplies            = 1500
  manpower            = 49
  money               = 10
  capital             = 1866
  diplomacy           = { }
  nationalprovinces   = { 1860 1864 1865 1866 1790 1824 1823 1806 1791 1825 938 935 934 459 915 913 }
  ownedprovinces      = { 1860 1864 1865 1866 1790 1824 1823 1806 1791 938 935 934 459 915 913 }
  controlledprovinces = { 1860 1864 1865 1866 1790 1824 1823 1806 1791 938 935 934 459 915 913 }
  techapps            = {
                                        #Industry:
                                        5010
                                        5020
                                        5030
                                        5040
                                        5050
                                        5060
                                        5070
                                        5080
                                        5090
                                        #Army Equipment:
                                        2400
                                        2200
                                        2500
                                        2600
                                        2700
                                        2800
                                        #Army Organisation:
                                        1300
                                        1400
                                        1900
                                        1260
                                        1970
                                        #Army Doctrines:
                                        6100
                                        6110
                                        6160
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 1
    political_left    = 4
    free_market       = 3
    freedom           = 1
    professional_army = 4
    defense_lobby     = 10
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12600 id = 1 }
    location = 1866
    name     = "Special Republican Guard"
    division =
    { id       = { type = 12600 id = 2 }
      name     = "4th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 3
    }
    division =
    { id       = { type = 12600 id = 3 }
      name     = "1st Rep. Guard Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 12600 id = 4 }
      name     = "2nd Rep. Guard Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { id       = { type = 12600 id = 5 }
      name     = "3rd Rep. Guard Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  landunit =
  { id       = { type = 12600 id = 6 }
    location = 1864
    name     = "Republican Guard Northern Corps"
    division =
    { id       = { type = 12600 id = 7 }
      name     = "2nd Armored Division"
      strength = 100
      type     = armor
      model    = 8
    }
    division =
    { id       = { type = 12600 id = 8 }
      name     = "7th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 9 }
      name     = "5th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12600 id = 10 }
      name     = "'Alabed' Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12600 id = 11 }
    location = 1823
    name     = "Republican Guard Southern Corps"
    division =
    { id       = { type = 12600 id = 12 }
      name     = "'Al-Nedaa' Armored Division"
      strength = 100
      type     = armor
      model    = 11
    }
    division =
    { id       = { type = 12600 id = 13 }
      name     = "1st Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 12600 id = 14 }
      name     = "6th Motorized Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12600 id = 15 }
    location = 1860
    name     = "1st Corps"
    division =
    { id       = { type = 12600 id = 16 }
      name     = "5th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 17 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 18 }
      name     = "8th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 19 }
      name     = "38th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12600 id = 20 }
    location = 1866
    name     = "2nd Corps"
    division =
    { id       = { type = 12600 id = 21 }
      name     = "3rd Armored Division"
      strength = 100
      type     = armor
      model    = 7
    }
    division =
    { id       = { type = 12600 id = 22 }
      name     = "15th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 23 }
      name     = "34th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12600 id = 24 }
    location = 1824
    name     = "3rd Corps"
    division =
    { id       = { type = 12600 id = 25 }
      name     = "6th Armored Division"
      strength = 100
      type     = armor
      model    = 7
    }
    division =
    { id       = { type = 12600 id = 26 }
      name     = "51st Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 27 }
      name     = "11th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12600 id = 28 }
    location = 1824
    name     = "4th Corps"
    division =
    { id       = { type = 12600 id = 29 }
      name     = "10th Armored Division"
      strength = 100
      type     = armor
      model    = 8
    }
    division =
    { id       = { type = 12600 id = 30 }
      name     = "14th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 31 }
      name     = "18th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12600 id = 32 }
    location = 1864
    name     = "5th Corps"
    division =
    { id       = { type = 12600 id = 33 }
      name     = "1st Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 34 }
      name     = "4th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 35 }
      name     = "7th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12600 id = 36 }
      name     = "16th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
}
