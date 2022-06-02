#!/user/bin/python
import os
from select import select

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
inputpath = ""

def main():
	inputpath = input(f"{bcolors.WARNING}\nPlease Input a Path to the goals or event picture folder:\n{bcolors.RESET}")
	modfolder = input(f"{bcolors.WARNING}Please Enter the Mod Folder Name with a \. If your mod folder is Millennium_Dawn, then you need to input it as \'Millennium_Dawn\\\':\n{bcolors.RESET}")

	# Retrieve files
	getfiles(inputpath)

	print(f"{bcolors.OK}There are {bcolors.RESET}" + str(len(ddslist)) + f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n")

	selection = int(input("Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\nPlease enter the number of the option you'd like: "))

	# Variable Init
	x = "" # X == the file name. It is only used to parse out the path
	y = "" # Y == becomes the path that is implemented texturefile
	z = "" # Z == is used to "sort" for a file
	w = "" # W == is the file name or texture name
	# While Loop Input Section
	while selection != 0:
		if selection == 1:
			gfxbool = int(input("Would you like me to append \"GFX_\" to the front of the icon?\n1 for yes, 0 for no.\n"))

			print("Generating goals.gfx...\n")
			with open("goals.gfx","w") as ffile:
				ffile.write('spriteTypes = {\n')
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
			print("Generation of goals_shine.gfx is complete.")
			print("\ngoals.gfx and goals_shine.gfx have been generated for " + str(len(ddslist)) + " icons.\n\nThe files have been outputted in " + str(os.getcwd()) )
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

					ffile.write('\tspriteType = {\n\t\tname = \"GFX_' + w + '\"\n\t\ttexturefile = \"' + y + '\"\n\t}\n')
				ffile.write('}')
			print("Generation of event_pictures.gfx is complete.")
			print("\neventpictures.gfx has been generated for " + str(len(ddslist)) + " event pictures.\n\nThe files have been outputted in " + str(os.getcwd()) )
			return
		else:
			print(f"{bcolors.FAIL}1 or 2 dumbfuck {bcolors.RESET}" + str(selection) + f"{bcolors.FAIL} isn't a fucking option.\n{bcolors.RESET}")
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
			elif '.tga' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
		else:
			getfiles(f)

if __name__ == "__main__":
	main()