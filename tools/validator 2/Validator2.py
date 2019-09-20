#!/usr/bin/env python3
import sys
import time
from ModAnalyzer import Mod
from LogAnalyzer import Logs

startTime = time.time()

__version__ = 1.0





def main():

    oldLogs = Logs('C:/Users/Boss/Documents/GitHub/Millennium_Dawn/tools/validator 2/new/')
    newLogs = Logs('C:/Users/Boss/Documents/GitHub/Millennium_Dawn/tools/validator 2/old/')

    oldLogs.CompareLogs(newLogs.highPriority, newLogs.mediumPriority, newLogs.lowPriority)

    #thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
