**How to use gfx_entry_generator.py for goals**
For whoever on gfx-input branch using this script:
    1) Open powershell
    2) Go into Millennium_Dawn/tools folder
    3) Run command 'python3 gfx_entry_generator.py'
    4) Give the complete path to the gfx entry. Which means you need to jump out of the tools folder and the Millennium_Dawn folder when giving the path.
        With this in midn, the path you give should look like this: '..\..\Millennium_Dawn\gfx\interface\goals'
    5) You will be asked to enter the mod folder name. Typically you would want to enter: 'Millennium_Dawn\' 
    6) Enter '1' to generate goals.gfx
    7) Next, enter '0'. (We dont append 'GFX' in front of the goals icons)
    8) New goals.gfx and goals_shine.gfx should now be generated
Extra:
    9) To view if the files changed run git command: git status
    10) Check what changes are made with git command: git differ
    11) Everything looks good? Now commit and push :)
