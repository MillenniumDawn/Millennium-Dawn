#!/user/bin/python
import os

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
	inputpath = input("Please Input a Path to the goals or event picture folder:\n")
	modfolder = input("Please Enter the Mod Folder Name with a \:\n")

	# Retrieve files
	getfiles(inputpath)

	print("There are " + str(len(ddslist)) + " .dds files available in this directory")

	selection = int(input("Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n"))

	# While Loop Input Section
	while selection != 0:
		if selection == 1:
			x = ""
			y = ""
			z = ""
			w = ""
			print("Generating goals.gfx...\n")
			with open("goals.gfx","w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					z = z.replace("gfx\\event_pictures\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
					y = y.replace("\\", "/")
					w = w.replace(".dds", "")
					ffile.write('	spriteType = {\n		name = \"' + w + '\"\n		texturefile = \"' + y + '\"\n	}\n')
				ffile.write('}')
			print("Generation of goals.gfx is complete.\n\nGenerating goals_shine.gfx...\n")
			with open("goals_shine.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					z = z.replace("gfx\\event_pictures\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
					y = y.replace("\\", "/")
					w = w.replace(".dds", "")
					ffile.write('	spriteType = { \n		name = \"' + w + '_shine\"\n		texturefile = \"' + y + '\"\n		effectfile = \"gfx/FX/buttonstate.lua\"\n		animation = {\n			animationmaskfile = \"' + y + '\"\n			animationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n			animationrotation = -90.0\n			animationlooping = no\n			animationtime = 0.75\n			animationdelay = 0\n			animationblendmode = "add"\n			animationtype = "scrolling"\n			animationrotationoffset = { x = 0.0 y = 0.0 }\n			animationtexturescale = { x = 1.0 y = 1.0 }\n		}\n		animation = {\n			animationmaskfile = \"' + y + '\"\n			animationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n			animationrotation = 90.0\n			animationlooping = no\n			animationtime = 0.75\n			animationdelay = 0\n			animationblendmode = "add"\n			\n			animationtype = "scrolling"\n			animationrotationoffset = { x = 0.0 y = 0.0 }\n			animationtexturescale = { x = 1.0 y = 1.0 }\n		}\n		legacy_lazy_load = no\n	}\n')
				ffile.write('}')
			print("Generation of goals_shine.gfx is complete.")
			print("\ngoals.gfx and goals_shine.gfx have been generated for " + str(len(ddslist)) + " icons.\n\nThe files have been outputted in " + str(os.getcwd()) )
			return
		elif selection == 2:
			x = ""
			y = ""
			z = ""
			w = ""
			print("Generating event_pictures.gfx...")
			with open ("MD_eventpictures.gfx", "w") as ffile:
				ffile.write('spriteTypes = {\n')
				for fname in ddsdict:
					x = fname
					x = x.split(modfolder)
					y = x[1] # Should Retrieve the Path
					z = y
					z = z.replace("gfx\\event_pictures\\", "")
					z = z.split("\\")
					for i in range(len(z)):
						if ".dds" in z[i]:
							w = z[i]
					y = y.replace("\\", "/")
					w = w.replace(".dds", "")
					ffile.write('	spriteType = {\n		name = \"GFX_' + w + '\"\n		texturefile = \"' + y + '\"\n	}\n')
				ffile.write('}')
			print("Generation of event_pictures.gfx is complete.")
			print("\neventpictures.gfx has been generated for " + str(len(ddslist)) + " event pictures.\n\nThe files have been outputted in " + str(os.getcwd()) )
			return
		else:
			print("Invalid Option. Please reboot program.")
			return



#outputs dictionary pairing path to .dds file
def getfiles(path):
	for filename in os.listdir(path):
		f = os.path.join(path,filename)
		if os.path.isfile(f):
			if '.dds' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
		else:
			getfiles(f)

if __name__ == "__main__":
	main()