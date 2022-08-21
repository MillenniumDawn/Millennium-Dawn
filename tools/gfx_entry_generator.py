#!/user/bin/python
import os
import shutil
from tokenize import Ignore

#############################
###
### HOI 4 GFX file generator by AngriestBird, originally for Millennium Dawn Mod
### Written in Python 3.9.2
###
### Copyright (c) 2022 Ken McCormick (AngriestBird)
### Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
### usage: python gfx_entry_generator.py
### Follow the prompts
###
### Given a path create either goals.gfx and goals_shine.gfx based on ALL icons in the directory.
###
###########################

ddslist = []
ddsdict = {}
pnglist = []
tgalist = []
inputpath = ""

def main():
	path = os.path.abspath(os.path.join(os.path.dirname('Millennium_Dawn'),'..'))
	modfolder = 'Millennium_Dawn\\'

	selection = int(input("Main Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n3. Retrieve and generate MD_ideas.gfx. This also generates defence company entries.\nPlease enter the number of the option you'd like: "))

	if selection == 1:
		path = os.path.abspath(os.path.join(os.path.dirname('Millennium_Dawn'),'..\gfx\interface\goals'))
		print(path)
		getfiles(path)
	elif selection == 2:
		path = os.path.abspath(os.path.join(os.path.dirname('Millennium_Dawn'),'..\gfx\event_pictures'))
		print(path)
		getfiles(path)
	elif selection == 3:
		path = os.path.abspath(os.path.join(os.path.dirname('Millennium_Dawn'),'..\gfx\interface\ideas'))
		print(path)
		getfiles(path)
	else:
		print(f"{bcolors.FAIL}1, 2 or 3 dumbfuck {bcolors.RESET}" + str(selection) + f"{bcolors.FAIL} isn't a fucking option.\n\nRun the script again cunt.\n{bcolors.RESET}")
		return

	print(f"{bcolors.OK}There are {bcolors.RESET}" + str(len(ddslist)) + f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n")
	print("There are " + str(len(pnglist)) + " that are PNG.\nThere are " + str(len(tgalist)) + " that are TGA.\n")

	# Variable Init
	x = "" # X == the file name. It is only used to parse out the path
	y = "" # Y == becomes the path that is implemented texturefile
	z = "" # Z == is used to "sort" for a file
	w = "" # W == is the file name or texture name
	# While Loop Input Section
	while selection != 0:
		if selection == 1:
			gfxbool = int(input("Would you like me to append \"GFX_\" to the front of the icon?\n1 for yes, 0 for no.\n"))

			print(f"{bcolors.OK}Generating goals.gfx...{bcolors.RESET}\n")
			with open("goals.gfx","w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\t#Vanilla DO NOT DELETE\n')
				ffile.write('\tspriteType = {\n\t\tname = \"GFX_goal_unknown\"\n\t\ttexturefile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\tlegacy_lazy_load = no\n\t}\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					y = y.replace("\\", "/")
					z = z.replace("gfx\\interface\\goals\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
						elif ".png" in z[i]:
							w = z[i]
						elif ".tga" in z[i]:
							w = z[i]
					if ".dds" in w:
						w = w.replace(".dds", "")
					elif ".png" in w:
						w = w.replace(".png", "")
					elif ".tga" in w:
						w = w.replace (".tga", "")

					if gfxbool == 0:
						ffile.write('\tspriteType = {\n\t\tname = \"' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')
					else:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')
				ffile.write('}')
			print("Generation of goals.gfx is complete.\n\nGenerating goals_shine.gfx...\n")
			with open("goals_shine.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				ffile.write('\t#Vanilla DO NOT DELETE \n')
				ffile.write('\tspriteType = {\n\t\tname = \"GFX__shine\"\n\t\ttexturefile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\teffectFile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = \"add\"\n\t\t\tanimationtype = \"scrolling\"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"gfx/interface/goals/goal_unknown.dds\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = \"add\"\n\t\t\tanimationtype = \"scrolling\"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					y = y.replace("\\", "/")
					z = z.replace("gfx\\interface\\goals\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
						elif ".png" in z[i]:
							w = z[i]
						elif ".tga" in z[i]:
							w = z[i]
					if ".dds" in w:
						w = w.replace(".dds", "")
					elif ".png" in w:
						w = w.replace(".png", "")
					elif ".tga" in w:
						w = w.replace (".tga", "")

					if gfxbool == 0:
						ffile.write('\tspriteType = { \n\t\tname = \"' + w + '_shine\"\n\t\ttexturefile = \"' + y + '\"\n\t\teffectfile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + y + '\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + y + '\"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
					else:
						ffile.write('\tspriteType = { \n\t\tname = \"GFX_' + w + '_shine\"\n\t\ttexturefile = \"' + y + '\"\n\t\teffectfile = \"gfx/FX/buttonstate.lua\"\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + y + '\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = \"' + y + '\"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n')
				ffile.write('}')
			print("Generation of goals_shine.gfx is complete.\n")
			shutil.copy('goals.gfx','../interface')
			shutil.copy('goals_shine.gfx','../interface')
			os.remove('goals.gfx')
			os.remove('goals_shine.gfx')
			print("Script has completed the movement of the files.\n")
			print("goals.gfx and goals_shine.gfx have been generated for " + str(len(ddslist)) + " icons.\n\nThe files have been outputted into the interface files.")
			return
		elif selection == 2:
			print("Generating event_pictures.gfx...")
			with open ("MD_eventpictures.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					y = y.replace("\\", "/")
					z = z.replace("gfx\\event_pictures\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
						elif ".png" in z[i]:
							w = z[i]
						elif ".tga" in z[i]:
							w = z[i]
					if ".dds" in w:
						w = w.replace(".dds", "")
					elif ".png" in w:
						w = w.replace(".png", "")
					elif ".tga" in w:
						w = w.replace (".tga", "")

					if "GFX_" in w:
						ffile.write('\tspriteType = {\n\t\tname = \"' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')
					else:
						ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')

				ffile.write('}')
			print("Generation of event_pictures.gfx is complete.")
			shutil.copy('MD_eventpictures.gfx','../interface')
			os.remove('MD_eventpictures.gfx')
			print("Script has completed the movement of the files.\n")
			print("\neventpictures.gfx has been generated for " + str(len(ddslist)) + " event pictures.\n\nThe files have been outputted in into the interface files.")
			return
		elif selection == 3:
			print("Generating MD_ideas.gfx...")
			with open ("MD_ideas.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					y = y.replace("\\", "/")
					z = z.replace("gfx\\interface\\ideas\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
						elif ".png" in z[i]:
							w = z[i]
						elif ".tga" in z[i]:
							w = z[i]
					if ".dds" in w:
						w = w.replace(".dds", "")
					elif ".png" in w:
						w = w.replace(".png", "")
					elif ".tga" in w:
						w = w.replace (".tga", "")

					if "idea_" in w:
						w = w.replace("idea_", "")
					if "GFX_idea_" in w:
						w = w.replace("GFX_idea_", "")

					ffile.write('\tspriteType ={\n\t\tname = \"GFX_idea_' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')
				ffile.write('}')
			print("Generation of the MD_ideas.gfx...")
			shutil.copy('MD_ideas.gfx','../interface')
			os.remove('MD_ideas.gfx')
			print("Script has completed the movement of the files.\n")
			print("\nMD_ideas.gfx has been generated for " + str(len(ddslist)) + " idea pictures.\n\nThe files have been outputted into the interface files.")
			return
		else:
			print(f"{bcolors.FAIL}1, 2 or 3 dumbfuck {bcolors.RESET}" + str(selection) + f"{bcolors.FAIL} isn't a fucking option.\n{bcolors.RESET}")
			return

class bcolors:
	OK = '\033[92m' #GREEN
	WARNING = '\033[93m' #YELLOW
	FAIL = '\033[91m' #RED
	RESET = '\033[0m' #RESET COLOR


#outputs dictionary pairing path to .dds file
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

if __name__ == "__main__":
	main()