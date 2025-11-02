This is a tool to generate focus tree skeletons using Diagram.net[CrocsFocusTreeTool.zip](uploads/0ed2e142187ecaae5dcb6fc437e89e5f/CrocsFocusTreeTool.zip)

ver 0.2:[CrocsFocusTreeTool.zip](uploads/f34d4789a59758200cc582bf3e2d9635/CrocsFocusTreeTool.zip)

Unpack the archive.
It might require .NET 6.0 runtime to run
https://dotnet.microsoft.com/en-us/download/dotnet/6.0

How to use
- make your diagram in diagram.net
- use simple rectangles for focuses
- use simple arrows for connection
- make sure all lines are FROM and TO focuses, it might not work correctly otherwise
- to make focus require ANY OF parents, set line style to DASHED
- to make mutually exclusive focuses, make ONE line, set it to LINK connection type
- when naming focuses, you can freely use spaces, but no new lines are recommended (forced shift+enter type)
- when ready go to file -> export as -> XML -> UNTICK the 'Compressed' -> download the xml to DEVICE

In tool
- enter path to your xml file
- enter path to file you want to generate (you can set it to folder/your_non_existing_file_yet.txt)
- enter tag you want to use for your focus tree, use custom parameters if needed

Tool should generate you a file, just close it when you are done!
Examples:
mutually exclusive line
![exclusive](uploads/331c3736294f8f7eab3b4757bf1ba58b/exclusive.png)
[example1](uploads/e52796ef088f55f121c83ef11eaf048d/example1.jpg)

Be aware that some complex line collisions are stored weirdly in document, and app may process them incorrectly
use x-del and y-del to make your tree better spaced out
