from sysDebug import makeLogEntry
import os

#Parameters
tagList = ['ABK', 'AFG', 'AGL', 'ALB', 'ALG', 'AQY', 'ARG', 'ARM', 'AST', 'AUS', 'AZE', 'BAH', 'BAN', 'BAR', 'BEL', 'BEN', 'BFA', 'BHR', 'BHU', 'BLR', 'BLZ', 'BOL', 'BOS', 'BOT', 'BRA', 'BRM', 'BRU', 'BUL', 'BUR', 'CAM', 'CAN', 'CAR', 'CBD', 'CDI', 'CHA', 'CHI', 'CHL', 'CNG', 'CNR', 'COL', 'COM', 'COS', 'CRE', 'CRO', 'CUB', 'CYP', 'CZH', 'DEN', 'DJI', 'DMI', 'DOM', 'DRC', 'ECU', 'EGU', 'EGY', 'ELS', 'ENG', 'ERI', 'EST', 'ETH', 'FIJ', 'FIN', 'FRA', 'FSA', 'FYR', 'GAB', 'GAH', 'GAM', 'GEO', 'GER', 'GNA', 'GNC', 'GRA', 'GRE', 'GUA', 'GUB', 'GUI', 'GUY', 'GXC', 'HAI', 'HAM', 'HEZ', 'HKG', 'HOL', 'HON', 'HOR', 'HOU', 'HUN', 'ICE', 'IND', 'IRE', 'IRQ', 'ISI', 'ISR', 'ITA', 'JAM', 'JAP', 'JOR', 'KAZ', 'KEN', 'KOR', 'KOS', 'KUR', 'KUW', 'KYR', 'LAO', 'LAT', 'LBA', 'LEB', 'LES', 'LIB', 'LIT', 'LUX', 'MAD', 'MAL', 'MAU', 'MAY', 'MEX', 'MIC', 'MLD', 'MLT', 'MLV', 'MLW', 'MNT', 'MON', 'MOR', 'MOZ', 'MRT', 'NAM', 'NCY', 'NEP', 'NGR', 'NIC', 'NIG', 'NKO', 'NOR', 'NOV', 'NUS', 'NZL', 'OMA', 'PAK', 'PAL', 'PAN', 'PAP', 'PAR', 'PAU', 'PER', 'PHI', 'PLY', 'PMR', 'POL', 'POR', 'PRU', 'QAT', 'RAJ', 'ROJ', 'ROM', 'RWA', 'SAF', 'SAO', 'SAU', 'SCL', 'SCO', 'SEN', 'SER', 'SEY', 'SHA', 'SIA', 'SIE', 'SIN', 'SLO', 'SLV', 'SML', 'SOL', 'SOM', 'SOO', 'SOV', 'SPR', 'SRI', 'SSU', 'STH', 'STK', 'STL', 'STV', 'SUD', 'SUR', 'SWA', 'SWE', 'SWI', 'SYR', 'TAI', 'TAJ', 'TAL', 'TIB', 'TIM', 'TNZ', 'TOG', 'TRI', 'TRK', 'TTP', 'TUA', 'TUN', 'TUR', 'UAE', 'UGA', 'UKR', 'URG', 'USA', 'UZB', 'VEN', 'VER', 'VIE', 'WAS', 'YEM', 'ZAM', 'ZIM']
excludeTags = []

setPrefix = "MD4_"
setName = 'AI_NoAllienace_Global'

setTypeList  = ['antaganize','allie']
setValueList = ['150','100']

enableParam =  'OR = {\n\t\t\thas_government = democratic\n\t\t\thas_government = communism\n\t\t}\n\t\t'              # Define enable Param for each ai_strategy for each NEW line use: "\n\t\t"
abortParam  =  'not = { has_government = fachist }'    # Define enable Param for each ai_strategy for each NEW line use: "\n\t\t"

makeForTag = 'SAU'                  # Leave empty if it's for everyone.            
includeTagInStatement = 'false'     # Include original_tag for each nation new ai_strategy in the enable parameter. Is ignored if makeForTag is set.
makeTagPerTag = 'true'              # Not created yet.




###################################################################################################
#Print information Text
print ('This script will generate a file containg ai_strategy for blocks of nations.\n')
print ('Parameters:')
print ('   Tags:               {0}'.format(len(tagList)))
print ('   Output Filename:    {1}{0}.txt'.format(setName,setPrefix))

print ('   ai_strategy Types:   {0}'.format(setTypeList))
print ('   ai_strategy Values:  {0}\n'.format(setValueList))

print ('   Enable Statement:')
if (includeTagInStatement == "true") and (makeForTag == ""):
    print("\t\toriginal_tag = TAG")
if (makeForTag != ""):
    print("\t\toriginal_tag = {0}".format(makeForTag))
print ('\t\t{0}\n'.format(enableParam))
print ('   Abort Statement:')
print ('\t\t{0}'.format(abortParam))
print ('\n')

# Print Information messages
print ("Messages:")
majorIssue = 0
if (makeTagPerTag == 'true') and (makeForTag == ""):
    print ("   [ERROR]   makeTagPerTag requires a set makeForTag.")
    majorIssue = 1
if not setTypeList:
    print ("   [ERROR]   setType is not defined.")
    majorIssue = 1
if not setValueList:
    print ("   [ERROR]   setValue is not defined.")
    majorIssue = 1
if (setName == ''):
    print ("   [ERROR]   setName is not defined.")
    majorIssue = 1
if (makeForTag not in tagList) and makeForTag != "":
    print ("   [WARNING] makeForTag tag {0} is not a used tag.".format(makeForTag))
if (enableParam == '') and (includeTagInStatement != "true"):
    print ("   [WARNING] no enable statement defined. 'always = yes' will be set.".format(makeForTag))
if (abortParam == ''):
    print ("   [WARNING] no abort statement defined. 'always = no' will be set.".format(makeForTag))
if ((makeForTag != "") and (includeTagInStatement == 'true')):
    print ("   [WARNING] makeForTag have been defined {0}!\n             This will make the script to only generate ai_strategy for that given contry.".format(makeForTag))
if (majorIssue == 1):
    print ("\n All errors need to be resolved befor continuing.")
    exit()
print ("\n")

# Start the creation of the file.
input("Press Enter to start the generation...")
import msvcrt as m
def wait():
    m.getch()

print ("\n---------------")
print ("LOG:")
makeLogEntry("INFO","Starting!",1)

genOutput = "Output/{1}{0}.txt".format(setName,setPrefix)
os.makedirs(os.path.dirname(genOutput), exist_ok=True)
f = open(genOutput, 'w')
makeLogEntry("INFO","{1}{0}.txt have been created...".format(setName,setPrefix),1)

#Loop
for tagA in tagList:
    if makeForTag == "":
        f.writelines("{1}_{0}".format(setName,tagA))
        if (includeTagInStatement == "false") and (makeForTag == ''):
            makeLogEntry("INFO","Creating ai_strategy.",1)
        else:
            makeLogEntry("INFO","Creating ai_strategy for {0}.".format(tagA),1)
    else:
        if makeTagPerTag == "true":
            f.writelines("{1}_{2}_{0}".format(setName,makeForTag,tagA))
            makeLogEntry("INFO","Creating ai_strategy for {0} towards {1}.".format(makeForTag,tagA),1)
        else:
            f.writelines("{1}_{0}".format(setName,makeForTag))
            makeLogEntry("INFO","Creating ai_strategy for {0}.".format(makeForTag),1)
    f.writelines(" = {\n")

    # Generate Enable statement
    if (includeTagInStatement == "false") and (makeForTag == ''):
        makeLogEntry("INFO","Creating enable statements.",0)
    else:
        makeLogEntry("INFO","Creating enable statements for {0}.".format(tagA),0)
    f.writelines("\tenable = {\n")
    if (includeTagInStatement == "true") and (makeForTag == ""):
        f.writelines("\t\toriginal_tag = {0}\n".format(tagA))
    if (makeForTag != ""):
        f.writelines("\t\toriginal_tag = {0}\n".format(makeForTag))
    if (enableParam == '') and (includeTagInStatement != "true") and (makeForTag == ""):
        f.writelines("\t\talways = yes\n")
        makeLogEntry("INFO","No enable statements found for {0} setting fallback value.".format(tagA),0)
    f.writelines("\t\t{0}\n".format(enableParam))
    f.writelines("\t}\n\n")
    
    # Generate Abort statement
    if (includeTagInStatement == "false") and (makeForTag == ''):
        makeLogEntry("INFO","Creating abort statements.",0)
    else:
        makeLogEntry("INFO","Creating abort statements for {0}.".format(tagA),0)
        
    f.writelines("\tabort = {\n")
    if (abortParam == ''):
        f.writelines("\t\talways = no\n")
        makeLogEntry("INFO","No abort statements found for {0} setting fallback value.".format(tagA),0)
    else:
        f.writelines("\t\t{0}\n".format(abortParam))
    f.writelines("\t}\n\n")
    
    # Add ai_strategy
    if (makeTagPerTag == 'true'):
        if (makeForTag == tagA) and ( includeTagInStatement == "true"):
            makeLogEntry("INFO","{0} do not need to {1} them self. Skipping to next tag.".format(tagA,setType),0)
            continue
        if tagB in excludeTags
            makeLogEntry("INFO","{0} is set to be excluded. Skipping to next tag.".format(tagB),0)
            continue
        for setType, setValue in zip(setTypeList,setValueList):
            f.writelines ("\tai_strategy = {\n")
            f.writelines ("\t\ttype = {0}\n".format(setType))
            f.writelines ('\t\tid = "{0}"\n'.format(tagA))
            f.writelines ("\t\tvalue = {0}\n".format(setValue))
            f.writelines ("\t}\n")
    else:
        for tagB in tagList:
            if makeTagPerTag == "true":
                pass
            if (tagB == tagA) and ( includeTagInStatement == "true"):
                makeLogEntry("INFO","{0} do not need to {1} them self. Skipping to next tag.".format(tagB,setType),0)
                continue
            if tagB in excludeTags
                makeLogEntry("INFO","{0} is set to be excluded. Skipping to next tag.".format(tagB),0)
                continue
            for setType, setValue in zip(setTypeList,setValueList):
                f.writelines ("\tai_strategy = {\n")
                f.writelines ("\t\ttype = {0}\n".format(setTypeValue))
                f.writelines ('\t\tid = "{0}"\n'.format(tagB))
                f.writelines ("\t\tvalue = {0}\n".format(setTypeValue))
                f.writelines ("\t}\n")

    f.writelines("}\n")
    if (makeForTag in tagList) and (makeTagPerTag != 'true'):
        makeLogEntry("INFO","Done generating all ai_strategy for {0}.".format(makeForTag),1)
        break
    if (includeTagInStatement != "true") and (makeTagPerTag != 'true'):
        makeLogEntry("INFO","Done generating ai_strategy.".format(makeForTag),1)
        break

f.close()
makeLogEntry("INFO","Generation complete!\n",1)
