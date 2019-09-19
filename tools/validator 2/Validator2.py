#!/usr/bin/env python3
import sys
import time
from ModAnalyzer import Mod


startTime = time.time()

__version__ = 1.0





def main():

    thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
