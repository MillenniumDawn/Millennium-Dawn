import os

ddslist = []
exceptionlist = []
ddsdict = {}
inputpath = ""

def main():
	dirName = input("Please Input a Path to the File Directory:\n")
	print(f'Creating batch script for directory {dirName}')

	getfiles(dirName)

	outScript = open('convertDDS.nvtt', 'w', encoding='utf-8') # Start a new script

	for file in ddsdict:
		newFileName = file.rpartition('.')[0] + '.dds' # Replace .png with .dds
		# Use forward slashes and ensure proper escaping for nvtt_export
		file_path = file.replace('\\', '/')
		output_path = newFileName.replace('\\', '/')
		outScript.write(f'"{file_path}" --no-mips --format bgra8 --export-transfer-function linear --output "{output_path}"\n')

	outScript.close()
	print('Done')


def getfiles(path):
	for filename in os.listdir(path):
		f = os.path.join(path,filename)
		if os.path.isfile(f):
			# if '.dds' in f:
			# 	ddsdict[f] = filename
			# 	ddslist.append(filename)
			if '.png' in f:
				ddsdict[f] = filename
				ddslist.append(filename)
		else:
			getfiles(f)

if __name__ == "__main__":
	main()


# How to Run batch
# 1. open CMD
# 2. run the command "nvtt_export.exe --batch convertDDS.nvtt"

#  C:\Users\Kenny McCormick\Documents\Millennium_Dawn\gfx\interface\goals
# "C:\Program Files\NVIDIA Corporation\NVIDIA Texture Tools\nvtt_export.exe" --batch convertDDS.nvtt