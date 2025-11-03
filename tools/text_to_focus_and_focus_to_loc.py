#!/usr/bin/env python3
russian = [
    "а",
    "б",
    "в",
    "г",
    "д",
    "е",
    "ё",
    "ж",
    "з",
    "и",
    "й",
    "к",
    "л",
    "м",
    "н",
    "о",
    "п",
    "р",
    "с",
    "т",
    "у",
    "ф",
    "х",
    "ц",
    "ч",
    "ш",
    "щ",
    "ъ",
    "ы",
    "ь",
    "э",
    "ю",
    "я",
]

first_fucks_symbols = [
    "!",
    "+",
    "=",
    "`",
    "~",
    "№",
    "$",
    "&",
    "?",
    "*",
    "(",
    ")",
    "\\",
    "/",
    ".",
    ",",
]
first_fucks_symbols_space = ["-", " "]

second_fucks_symbols_space = ["_"]
second_not_title = [
    "as",
    "at",
    "but",
    "by",
    "for",
    "in",
    "of",
    "off",
    "on",
    "out",
    "outside",
    "past",
    "to",
    "up",
    "with",
    "without",
    "for",
    "in",
]

print(
    "This program can:\n1. Make the focus ID from the text\n2. Make the focus name into a localization\n3. Make text to focus ID and localisation"
)

mode = int(input("Write 1 or 2 or 3: "))
print("\n\n")
if mode == 1:
    # set vars
    country_tag = str(input("Country tag: ").upper())
    country_tag = country_tag[:3]
    print("\n\n")

    while True:
        text = str(input("Focus name: "))
        text = text.lower()

        # delete from text fucks simbyls
        for i in russian:
            text = text.replace(i, "")
        for i in first_fucks_symbols:
            text = text.replace(i, "")
        for i in first_fucks_symbols_space:
            text = text.replace(i, "_")

        print(f"{country_tag}_{text}\n")

elif mode == 2:
    while True:
        text = input("Focus: \n")
        focus_name = text

        text = text.split("_", 1)[1]
        text = " ".join(
            word if word.lower() in second_not_title else word.title()
            for word in text.split()
        )
        # delete from text fucks simbyls
        for i in russian:
            text = text.replace(i, "")
        for i in second_fucks_symbols_space:
            text = text.replace(i, " ")
        text = '"' + text + '"'

        text_final = focus_name + ": " + text

        print(f"{text_final}\n")

elif mode == 3:
    while True:
        # set vars
        country_tag = str(input("Country tag: ").upper())
        country_tag = country_tag[:3]
        print("\n\n")

        while True:
            text_start = str(input("Focus name: "))
            text = text_start
            text = text.lower()
            # delete from text fucks simbyls
            for i in russian:
                text = text.replace(i, "")
            for i in first_fucks_symbols:
                text = text.replace(i, "")
            for i in first_fucks_symbols_space:
                text = text.replace(i, "_")
            print(f"\n{country_tag}_{text}")

            ##################################################################

            loc_text = country_tag + "_" + text
            focus_name = loc_text

            loc_text = loc_text.split("_", 1)[1]
            loc_text = " ".join(
                word if word.lower() in second_not_title else word.title()
                for word in loc_text.split()
            )
            # delete from text fucks simbyls
            for i in russian:
                loc_text = loc_text.replace(i, "")
            for i in second_fucks_symbols_space:
                loc_text = loc_text.replace(i, " ")
            loc_text = '"' + loc_text + '"'

            text_final = focus_name + ": " + loc_text

            print(f"{text_final}\n")

else:
    exit()

# By Andry#0980 07.05.2023 year
