#TAG_LIST = {"TAJ","TRK","UZB","SSU","SOM","SPR","SRI","SSU","SUD","TNZ",
#            "AFG","AGL","ALG","ARG","AST","BAN","BOL","BOT","BRA","BRM","CAM","CAN","CAR","CBD","CDI","CHA","CHI","CHL","CNG","COL",
#            "DRC","ECU","EGU","EGY","ERI","ETH","GAB","GAH","IND","IRQ","ISR","JAP","KAZ","KEN","KOR","KYR","LAO","LAT",
#            "LBA","LEB","LIB","MAD","MAL","MAU","MAY","MEX","MLW","MOR","MOZ","NAM","NEP","NGR","NIG","NKO","PAK","PER","PHI","PRU","RAJ","SAF","SAU",
#            "SIA","SOV","SYR","USA","MON","SIE","VIE",
#            "ALB","ARM","AUS","AZE","BEL","BLR","BOS","BUL","CRO","CZE","DEN","ENG","EST","FIN","FRA","FYR","GEO","GER","GRE",
#            "HOL","HUN","IRE","ITA","LAT","LIT","MLV","NOR","POL","POR","ROM","SER","SWE","SWI","UKR","TUR"}

#FLAG_TYPES = {"reset","Autocracy","Special","More_Special","Rebel","Special_Rebel"}


TAG_LIST = {"USoE", "SOV_USSR","JAM","LUX","MNT"}
FLAG_TYPES = {"reset","Autocracy","Special","More_Special"}

for TAG in TAG_LIST:
    for TYPE in FLAG_TYPES:
        print(' '+TAG+'_'+TYPE+'_flag: "Change Flag"')
        print(' '+TAG+'_'+TYPE+'_flag_desc: "Today we have the ability to change our flag..."')
