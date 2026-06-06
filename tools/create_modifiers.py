#!/user/bin/python
import os
import re
import codecs
from tokenize import Ignore

# Modfolder = the mod folder name
# mod = The mod name
modfolder = 'Millennium_Dawn\\'
mod = 'Millennium_Dawn'

def main():
	english_array = []
	french_array = []
	russian_array = []
	exception_strings = []

	english_dictionary = {}
	french_dictionary = {}
	russian_dictionary = {}

	vanilla_french = os.path.abspath(os.path.join(os.path.dirname(modfolder), '..\\..\\modifiers_l_french.yml'))
	vanilla_russian = os.path.abspath(os.path.join(os.path.dirname(modfolder), '..\\..\\modifiers_l_russian.yml'))

	vanilla_french_file = codecs.open(vanilla_french, 'r', 'UTF-8-SIG')
	vanilla_french_lines = vanilla_french_file.readlines()

	vanilla_russian_file = codecs.open(vanilla_russian, 'r', 'UTF-8-SIG')
	vanilla_russian_lines = vanilla_russian_file.readlines()


	english_md = os.path.abspath(os.path.join(os.path.dirname(modfolder), '..\\..\\localisation\\english\\replace\\replaced_from_vanilla_modifiers_l_english.yml'))

	read_tags = codecs.open(english_md, 'r', 'UTF-8-SIG')
	lines = read_tags.readlines()
	bad_line = 0
	for l in lines:
		if l == lines[0]:
			bad_line = bad_line + 1
		elif ':' in l:
			temp_string = l.split(':', 1)
			english_dictionary[temp_string[0]] = temp_string[1]
		else:
			bad_line = bad_line + 1

	bad_line = 0
	for l in vanilla_french_lines:
		if l == lines[0]:
			bad_line = bad_line + 1
		elif ':' in l:
			temp_string = l.split(':', 1)
			french_dictionary[temp_string[0]] = temp_string[1]
		else:
			bad_line = bad_line + 1

	english_texticon_dictionary = {}
	for k, v in english_dictionary.items():
		try:
			value = regex_lookup(v)
			english_texticon_dictionary[k] = value
		except:
			exception_strings.append(f"This dictionary entry has failed. Key: {k} Value: {v}")

	str2 = ""
	str3 = ""
	for k, v in sorted(french_dictionary.items()):
		for a, b in english_texticon_dictionary.items():
			if a == k:
				print(f'{k} | {a}\n')
				str2 = v

				str2 = str2.split('\"', 1)
				str3 = '\"' + b + ' ' + str2[1]
				print(str3)
				french_dictionary[k] = str3


	for k, v in sorted(french_dictionary.items()):
		french_array.append(f'{k}: {v}')

	# bad_line = 0
	# for l in vanilla_russian_lines:
	# 	if l == lines[0]:
	# 		bad_line = bad_line + 1
	# 	elif ':' in l:
	# 		temp_tuple = tuple(map(str, l.split(':')))
	# 		russian_dictionary[temp_tuple[0]] = temp_tuple[1]
	# 	else:
	# 		bad_line = bad_line + 1

	# for k, v in russian_dictionary.items():
	# 	russian_array.append(f'{k}: {v}')

	with codecs.open("replaced_from_vanilla_modifiers_l_french.yml","w", "UTF-8-SIG") as ffile:
		ffile.write("l_french:\n")
		for l in french_array:
			ffile.write(l)
	# with codecs.open("replaced_from_vanilla_modifiers_l_russian.yml","w", "UTF-8-SIG") as ffile:
	# 	ffile.write("l_russian:\n")
	# 	for l in russian_array:
	# 		ffile.write(l)

	with codecs.open("error.log", "w", "UTF-8-SIG") as ffile:
		ffile.write("Error Log:\n")
		for l in exception_strings:
			ffile.write(f'{l}')

def regex_lookup(string):
	m = re.search(r"£(.+?) ", string)
	value = m.group(0)
	return value

# I don't need to explain what this
if __name__ == "__main__":
	main()
