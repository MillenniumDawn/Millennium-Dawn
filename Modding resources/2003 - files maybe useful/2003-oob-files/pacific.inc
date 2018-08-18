
##############################
# Country definition for FLA #
##############################

province =
{ id       = 1752
  naval_base = { size = 2 current_size = 2 }
}            # Fiji

province =
{ id       = 1605
  naval_base = { size = 2 current_size = 2 }
}            # Majuro

country =
{ tag                 = FLA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 4
  transports          = 50
  escorts             = 0
  capital             = 1752
  diplomacy           = { }
  nationalprovinces   = { 1752 1753 1754 1755 1757 1758 1759 1760 1761 1762 1763 1767 1768 1769 1770 1600 1601 1602 1603 1605 1606 1607 1608 1611 1621
                          1756 1684 1685 1686 1688 1689 1690 1622 1683
                        }
  ownedprovinces      = { 1752 1753 1754 1755 1757 1758 1759 1760 1761 1762 1763 1767 1768 1769 1770 1600 1601 1602 1603 1605 1606 1607 1608 1611 1621
                          1756 1684 1685 1686 1688 1689 1690 1622 1683
                        }
  controlledprovinces = { 1752 1753 1754 1755 1757 1758 1759 1760 1761 1762 1763 1767 1768 1769 1770 1600 1601 1602 1603 1605 1606 1607 1608 1611 1621
                          1756 1684 1685 1686 1688 1689 1690 1622 1683
                        }
  techapps            = {
                                        #Industry:
                                        5010
                                        5020
                                        5030
                                        5040
                                        5050
                                        5070
                                        5090
                                        #Army Equip:
                                        2400
                                        2200
                                        2500
                                        2600
                                        2800
                                        #Army Org:
                                        1300
                                        1900
                                        1260
                                        1980
                                        #Army Doc:
                                        6100
                                        6110
                                        6160
                                        6010
                                        6020
                                        6600
                                        6610
                                        6910
                                        #Secret Tech:
                                        7330
                                        3590
                                        8900
                                        8950
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 6
    freedom           = 6
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 6
  }
}
