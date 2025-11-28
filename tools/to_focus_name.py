#!/usr/bin/env python3
# simbyls to delete
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
fucks_symbols = [
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
fucks_symbols_space = ["-", " "]

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
    for i in fucks_symbols:
        text = text.replace(i, "")
    for i in fucks_symbols_space:
        text = text.replace(i, "_")

    print(f"{country_tag}_{text}\n")

# By Andry#0980 05.05.2023 year
