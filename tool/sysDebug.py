# Debug function that create a log file as well as write in the console.
# Logg messages are activated if makeLogEntry parameter 3 is set to 1.
# 
# Include:
#   from sysDebug import makeLogEntry
#
# Functions:
#   makeLogEntry("Text","Text",Number)
#    0: <STRING>  Tag
#    1: <STRING>  Message
#    2: <BOOL>    Print in console (1 or 0)
#
# Exsample
# makeLogEntry("INFO","This is a message",1)
#
import os
import time

# Make Log File
logDate = time.strftime("%Y-%m-%d")
logOutput = "Log/{0}.log".format(logDate)
os.makedirs(os.path.dirname(logOutput), exist_ok=True)
logFile = open(logOutput, 'w')

# Write Log Entry
def makeLogEntry(type,text,log):
    longLogTime = time.strftime("%Y-%m-%d %H:%M:%S")
    shortLogTime = time.strftime("%H:%M:%S")
    logFile.writelines(" {2} [{0}] {1}\n".format(type,text,longLogTime))
    if log == 1:
        print ("  {2} [{0}] {1}".format(type,text,shortLogTime))