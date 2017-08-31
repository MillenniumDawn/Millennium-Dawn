#!/usr/bin/python

def GetTags(FilePath):
	TagList = [] #This dictionary will store every tag
	Success = True


	try:
		with open(FilePath, "r") as File:
			print("File successfully opened.")
			for Line in File:
				if not "#" in Line:
					Tag = Line[:3]
					if Tag != "\n":
						TagList.append(Tag)
					#print(Tag) #Use for debugging
	except IOError:
		print("The file could not be opened")
		Success = False

	if Success:
		print("Successfully Created Tag List.")
		
	return TagList
	
def GetTagDictionary(FilePath):
	TagList = {} #This dictionary will store every tag
	Success = True

	try:
		with open(FilePath, "r") as File:
			print("File successfully opened.")
			for Line in File:
				if not "#" in Line:
					Tag = Line[:3]
					FullName = Line[17:]
					NameLength = 0
					for Char in FullName:
						NameLength += 1
						if Char == ".":
							NameLength -= 1
							break
					FullName = FullName[:NameLength]
					if not "\n" in Tag:
						TagList[Tag] = FullName
				#print(Tag) #Use for debugging
	except IOError:
		print("The file could not be opened")
		Success = False

	if Success:
		print("Successfully Created Dictionary.")
		
	return TagList