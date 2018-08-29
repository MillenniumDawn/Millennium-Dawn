
##############################
# Country definition for AFG #
##############################

province =
{ id       = 1486
  air_base = { size = 4 current_size = 4 }
}            # Kabul

country =
{ tag                 = AFG
  puppet              = USA
  control             = USA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 26
  dissent             = 10
  capital             = 1486
  diplomacy =
  { relation = { tag = USA value = 200 access = yes }
  }
  nationalprovinces   = { 1486 1493 1492 1484 }
  ownedprovinces      = { 1486 1493 1492 1484 }
  controlledprovinces = { 1486 1493 1492 1484 }
  techapps            = {  }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 5
    free_market       = 5
    freedom           = 3
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 2
  }
}
