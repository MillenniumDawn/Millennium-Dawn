import os

while True:
    mode = input("Select mode:\n(File stats or All stats)\n").lower()

    if mode == "file stats" or mode == "file":
        while True:
            path_to_focuses = input("\nPath to file (Without .txt):\n(exit to exit)\n")
            if path_to_focuses == "exit" or path_to_focuses == "Exit":
                print()
                break
            path_to_focuses += ".txt"

            try: file = open(path_to_focuses,'r')
            except FileNotFoundError:
                print("File not found\n")
                continue

            count_of_line = 0
            focuses = 0
            exclusive = 0

            for line in file:
                line_text = line.replace("\n", "")
                if "focus = {" in line_text: focuses += 1
                if "mutually_exclusive = {" in line_text: exclusive += 1

            focus_per_exlusive = focuses // exclusive
            print(f'Focuses in file: {focuses}\nExclusiveses in file: {exclusive}\nFocuses per exclusiveses: {focus_per_exlusive}\n')

    elif mode == "all stats" or mode == "all":
        while True:
            path_to_focuses = input("\nPath to folder: (Folder with focuses)\n(exit to exit)\n")
            if path_to_focuses == "exit" or path_to_focuses == "Exit":
                print()
                break
            try: files_with_focuses = os.listdir(path_to_focuses)
            except FileNotFoundError:
                print("Files not found\n")
                continue

            count_of_line = 0
            focuses = 0
            focuses_in_this_file = 0
            exclusive = 0
            list_fc = []

            for file_i in range(len(files_with_focuses)):
                file_to_read = path_to_focuses + "\\" + files_with_focuses[file_i]
                file = open(file_to_read, 'r', encoding="UTF-8")
                focuses_in_this_file = 0
                for line in file:
                    line_text = line.replace("\n", "")
                    if "focus = {" in line_text:
                        focuses += 1
                        focuses_in_this_file += 1
                    if "mutually_exclusive = {" in line_text: exclusive += 1

                if focuses_in_this_file > 0: list_fc.append(str(focuses_in_this_file) + " " + str(files_with_focuses[file_i]))

            all_focuses_files = len(files_with_focuses)
            average_number_of_focuses = focuses // all_focuses_files
            focus_per_exlusive = focuses // exclusive
            average_number_of_exclusive = exclusive // all_focuses_files

            sorted_list = sorted(list_fc, key=lambda x: int(x.split()[0]), reverse=True)
            for i in range(len(sorted_list)):
                print(sorted_list[i])

            print(f'-------------------------\nAll files with focuses: {all_focuses_files}\nFocuses in all files: {focuses}\nAverage number of focuses in file: {average_number_of_focuses}\nExclusiveses in all files: {exclusive}\nAverage focuses per exclusiveses: {focus_per_exlusive}\nAaverage mutually exclusive focuses in file: {average_number_of_exclusive}\n')
            break

    else: continue