#!/user/bin/python
import os
import shutil
from tokenize import Ignore

#############################1
###
### HOI 4 GFX file generator by AngriestBird, originally for Millennium Dawn Mod
### Written in Python 3.11.1
###
### Copyright (c) 2023 Ken McCormick (AngriestBird)
### Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
### Instructions:
### 1. PLace this file in HOI4/mod/DEV_FOLDER/tools
### 2. Update line 41 and 42 to be the name of your mod
### 3. Run script as below:
### usage: python gfx_entry_generator.py
### Follow the prompts from there. This script will not function properly if it is not sitting in the proper folder.
###
### Given an input selection number of 1 through 4 recurisvely search and save path for graphical assets.
### It then generates the requires .gfx code and ports it into readable script for the game.
###
###
###########################

# Global Init
# ddslist: List of files that are .dds
# pnglist: List of files that are .png
# tgalist: List of files that are .tga
# ddsdict: Dictionary of all file names and their paths
# country_tag_list: Country Tag List
ddslist = []
ddsdict = {}
pnglist = []
tgalist = []
country_tag_list = []

# Modfolder = the mod folder name
# mod = The mod name
modfolder = 'Millennium_Dawn\\'
mod = 'Millennium_Dawn'

def main():
	path = os.path.abspath(os.path.join(os.path.dirname(mod),'..'))
	# country_tag_list = createcountrytaglist()

	selection = int(input("Main Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n3. Retrieve and generate MD_ideas.gfx. This also generates defence company entries.\n4. Retrieve and generate MD_technologies.gfx (DO NOT USE. WIP)\n5. Retrieve and generate MD_parties_icons.gfx.\n6. Retrieve and generate intelligence agency icons\n7. Retrieve and generate MD_decisions.gfx\nPlease enter the number of the option you'd like: "))

	if selection == 1:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\interface\\goals'))
		print(path)
		getfiles(path)
	elif selection == 2:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\event_pictures'))
		print(path)
		getfiles(path)
	elif selection == 3:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\interface\\ideas'))
		print(path)
		getfiles(path)
	elif selection == 4:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\interface\\technologies'))


		print(path)
		getfiles(path)
	elif selection == 5:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\texticons\\parties_icons'))

		print(path)
		getfiles(path)
	elif selection == 6:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\interface\\operatives\\agencies'))

		print(path)
		getfiles(path)
	elif selection == 7:
		path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\\gfx\\interface\\decisions'))
		print(path)
		getfiles(path)
	else:
		print(f"{bcolors.FAIL}1 through 7 dumbfuck {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} isn't a fucking option.\n\nRun the script again cunt.\n{bcolors.RESET}")
		return

	print(f"{bcolors.OK}There are {bcolors.RESET}" + str(len(ddslist)) + f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n")
	print("There are " + str(len(pnglist)) + " that are PNG.\nThere are " + str(len(tgalist)) + " that are TGA.\n")

	# Variable Init Section
	file_location = "" # File Location: It is only used to parse out the path
	texture_path = "" # Texture Path: becomes the path that is implemented texturefile
	file_utility = "" # File Utility: Used to "sort" for a file
	texture_name = "" # Texture name: The actual name of the file for use of the texture
	tag_of_nation = "" # Tag of the Nation: Country Tag Use

	# Creation of the .gfx files
	while selection != 0:
		if selection == 1:
			gfxbool = int(input("Would you like me to append \"GFX_\" to the front of the icon?\n1 for yes, 0 for no.\n"))

			print(f"{bcolors.OK}Generating goals.gfx...{bcolors.RESET}\n")
			with open("goals.gfx","w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\t#Vanilla DO NOT DELETE\n')
				ffile.write('\tspriteType = {\n\t\tname = \"GFX_goal_unknown\"\n\t\ttexturefile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\tlegacy_lazy_load = no\n\t}\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\interface\\goals\\", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)

					if gfxbool == 0:
						ffile.write('\tspriteType = {\n\t\tname = \"' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
					else:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
				ffile.write('}')
			print("Generation of goals.gfx is complete.\n\nGenerating goals_shine.gfx...\n")
			with open("goals_shine.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\t#Vanilla DO NOT DELETE \n')
				ffile.write('\tspriteType = {\n\t\tname = \"GFX__shine\"\n\t\ttexturefile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\teffectFile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = \"add\"\n\t\t\tanimationtype = \"scrolling\"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = \"add\"\n\t\t\tanimationtype = \"scrolling\"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\interface\\goals\\", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)

					if gfxbool == 0:
						ffile.write('\tspriteType = { \n\t\tname = \"' + texture_name + '_shine\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t\teffectfile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + texture_path + '\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + texture_path + '\"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
					else:
						ffile.write('\tspriteType = { \n\t\tname = \"GFX_' + texture_name + '_shine\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t\teffectfile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + texture_path + '\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + texture_path + '\"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
				ffile.write('}')
			print("Generation of goals_shine.gfx is complete.\n")
			movefilestointerface('goals.gfx','goals_shine.gfx')
			print("goals.gfx and goals_shine.gfx have been generated for " + str(len(ddslist)) + " icons.\n\nThe files have been outputted into the interface files.")
			return
		elif selection == 2:
			print("Generating event_pictures.gfx...")
			with open ("MD_eventpictures.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\event_pictures\\", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)

					if "GFX_" in texture_name:
						ffile.write('\tspriteType = {\n\t\tname = \"' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
					else:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')

				ffile.write('}')
			print("Generation of event_pictures.gfx is complete.")
			movefilestointerface('MD_eventpictures.gfx')
			print(f"\neventpictures.gfx has been generated for {len(ddslist)} event pictures.\n\nThe file \"MD_eventpictures.gfx\" has been outputted to the interface directory.")
			return
		elif selection == 3:
			print("Generating MD_ideas.gfx...")
			with open ("MD_ideas.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\n\t## DO NOT REMOVE\n\tspriteType={\n\t\tname = \"GFX_idea_traits_strip\"\n\t\ttexturefile = \"gfx/interface/ideas/idea_traits_strip.dds\"\n\t\tnoOfFrames = 18\n\t}\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\interface\\ideas\\", "")
					file_utility = file_utility.split("\\")

					if "traits_strip" in fname:
						print('Utility Idea GFX... skipping')
					else:
						texture_name = createitemcall(file_utility, type=1)
						ffile.write('\tspriteType ={\n\t\tname = \"GFX_idea_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
				ffile.write('}')
			print("Generation of the MD_ideas.gfx...")
			movefilestointerface('MD_ideas.gfx')
			print("\nMD_ideas.gfx has been generated for " + str(len(ddslist)) + " idea pictures.\n\nThe files have been outputted into the interface files.")
			return
		elif selection == 4: # Technology Icons
			print("Generating technologies.gfx...")
			with open("technologies.gfx", "w") as ffile:
				# Overarching Clause
				count = 0
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					if "Generic" in fname:
						count += 1
					elif "modules" in fname:
						count += 1
					else:
						if any((match := substring) in fname for substring in country_tag_list):
							# DEBUG: print("Match:" + match)
							tag_of_nation = match
						file_location = fname
						file_location = file_location.split(modfolder)
						texture_path = file_location[1] # Should Retrieve the Path
						file_utility = texture_path
						texture_path = texture_path.replace("\\", "/")
						file_utility = file_utility.replace("gfx\\interface\\technologies\\", "")
						file_utility = file_utility.split("\\")

						texture_name = createitemcall(file_utility)

						# Write the spriteType
						if tag_of_nation is None:
							ffile.write('\tspriteType ={\n\t\tname = \"GFX_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
						else:
							ffile.write('\tspriteType ={\n\t\tname = \"GFX_'+ tag_of_nation + "_" + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n')
				# End Clause
				ffile.write('}')
			print(f"{bcolors.INFO} {count} files were skipped due to being generic or module files.{bcolors.RESET}")
			print("Generation of the technologies.gfx...")
			return
		elif selection == 5: # Party Icons
			print("Generating MD_parties_icons.gfx...")
			with open ("MD_parties_icons.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\texticons\\parties_icons\\", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)

					ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t\tlegacy_lazy_load = no\n\t}\n')

				ffile.write('}')
			print("Generation of MD_parties_icons is complete.")
			movefilestointerface('MD_parties_icons.gfx')
			print(f"\nMD_parties_icons.gfx has been generated for {len(ddslist)} party icons.\n\nThe file \"MD_parties_icons.gfx\" has been outputted to the interface directory.")
			return
		elif selection == 6: # Intelligence Agency
			print("Generating MD_intelligence_icons.gfx...")
			with open ("MD_intelligence_icons.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\interface\\operatives\\agencies", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)
					texture_tuple = tuple(map(str, texture_name.split('_')))

					ffile.write('\tspriteType = {\n\t\tname = \"GFX_intelligence_agency_logo_' + texture_tuple[2] + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t\tnoOfFrames = 2\n\t}\n')

				ffile.write('}')
			print("Generation of MD_intelligence_icons is complete.")
			movefilestointerface('MD_intelligence_icons.gfx')
			print(f"\nMD_intelligence_icons.gfx has been generated for {len(ddslist)} intelligence agencies.\n\nThe file \"MD_intelligence_icons.gfx\" has been outputted to the interface directory.")
			return
		elif selection == 7: # Decisions
			print("Generating MD_decisions.gfx...")
			with open ("MD_decisions.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\n\t### categories\n\n\n')
				for fname in ddsdict:
					file_location = fname
					file_location = file_location.split(modfolder)
					texture_path = file_location[1] # Should Retrieve the Path
					file_utility = texture_path
					texture_path = texture_path.replace("\\", "/")
					file_utility = file_utility.replace("gfx\\interface\\decisions\\", "")
					file_utility = file_utility.split("\\")

					texture_name = createitemcall(file_utility)

					if "decision_category_" in texture_name or "decision_" in texture_name or "decisions_" in texture_name or "decisions_category_" in texture_name:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n\n')
					else:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_decision_' + texture_name + '\"\n\t\ttexturefile = \"' + texture_path + '\"\n\t}\n\n')
				ffile.write('}')
			print("Generation of the MD_decisions.gfx...")
			movefilestointerface('MD_decisions.gfx')
			print("\nMD_decisions.gfx has been generated for " + str(len(ddslist)) + " decision pictures.\n\nThe files have been outputted into the interface files.")
			return
		else:
			print(f"{bcolors.FAIL}1 through 7 dumbfuck {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} isn't a fucking option.\n\nRun the script again cunt.\n{bcolors.RESET}")
			return

# Utilities:
# Class Name: bcolors
# Purpose: I don't think I need to be more specific here
class bcolors:
	OK = '\033[92m' #GREEN
	WARNING = '\033[93m' #YELLOW
	FAIL = '\x1b[31;1m' #RED
	RESET = '\033[0m' #RESET COLOR
	INFO = '\x1b[33;25m' #INFO COLOR

# Method: movefilestointerface
# Parameters: filename, filename2
# Purpose: Moves output files from the tools directory to the ../interface directory
def movefilestointerface(filename, filename2=""):
	print(f"Moving {filename} from tools to the interface directory")
	shutil.copy(filename,'../interface')
	os.remove(filename)
	if filename2 != "":
		shutil.copy(filename2,'../interface')
		os.remove(filename2)
		print(f"{filename} && {filename2} has been moved successfully to the interface directory.")
	else:
		print(f"{filename} has been moved sucessfully to the interface directory" )

def createitemcall(filecall, type=0):
	util = ""
	# Create the Item "Call"
	for i in range(len(filecall)):
		if ".dds" in filecall[i]:
			util = filecall[i]
		elif ".png" in filecall[i]:
			util = filecall[i]
		elif ".tga" in filecall[i]:
			util = filecall[i]
	if ".dds" in util:
		util = util.replace(".dds", "")
	elif ".png" in util:
		util = util.replace(".png", "")
	elif ".tga" in util:
		util = util.replace (".tga", "")

	if type == 1:
		if "idea_" in util:
				util = util.replace("idea_", "")
		elif "GFX_idea_" in util:
				util = util.replace("GFX_idea_", "")

	return util

def createcountrytaglist():
	temp_array = []
	# Country Tag List Array Creation
	tag_path = os.path.abspath(os.path.join(os.path.dirname(mod), '..\\common\\country_tags'))
	tag_path = str(tag_path) + "\\00_countries.txt"
	read_tags = open(tag_path, 'r')
	lines = read_tags.readlines()
	bad_line = 0
	for l in lines:
		temp_tag = l[0:3]
		if l[0] == '#':
			bad_line += 1
		elif l[0] == '\n':
			bad_line += 1
		elif l[0:3] == 'NAV':
			bad_line += 1
		else:
			temp_array.append(temp_tag)
			temp_array.sort()
	return temp_array

# Method: getfiles
# Purpose: Recursively serach and find binding path throughout the given directory and binds it to a .dds, .png, .tga
def getfiles(path):
	for filename in os.listdir(path):
		f = os.path.join(path,filename)
		if os.path.isfile(f):
			if '.dds' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
			elif '.png' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
				pnglist.append(filename)
			elif '.tga' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
				tgalist.append(filename)
		else:
			getfiles(f)

# I don't need to explain what this
if __name__ == "__main__":
	main()
