#!/usr/bin/env python3
import sys
import time
from ModAnalyzer import Mod
from LogAnalyzer import Logs

startTime = time.time()

__version__ = 1.0





def main():

    #oldLogs = Logs('C:/Users/Boss/Documents/GitHub/Millennium_Dawn/tools/validator 2/Old Logs/')
    #newLogs = Logs('C:/Users/Boss/Documents/GitHub/Millennium_Dawn/tools/validator 2/New logs/')

    oldLogs = Logs('C:/Users/Michael/Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium_Dawn/tools/validator 2/Old logs/')
    newLogs = Logs('C:/Users/Michael/Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium_Dawn/tools/validator 2/New Logs/')

    oldLogs.CompareLogs(newLogs.highPriority, newLogs.mediumPriority, newLogs.lowPriority)

    #thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
