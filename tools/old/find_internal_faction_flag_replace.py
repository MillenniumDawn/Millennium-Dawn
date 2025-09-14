#!/usr/bin/env python3
from __future__ import print_function

import fnmatch
import os
from fileinput import FileInput


def find_replace(topdir, file_pattern, text, replacement):
    for dirpath, dirs, files in os.walk(topdir, topdown=True):
        dirs[:] = [d for d in dirs if d != ".svn"]  # skip .svn dirs
        files = [
            os.path.join(dirpath, filename)
            for filename in fnmatch.filter(files, file_pattern)
        ]
        for line in FileInput(files, inplace=True):
            print(line.replace(text, replacement), end="")


find_replace(
    r"C:/Users/Kenneth/Documents/Paradox Interactive/Hearts of Iron IV/mod/md_dev/history/countries",
    "*.txt",
    "set_country_flag = indifferent_small_medium_business_owners",
    "set_variable = { small_medium_business_owners_opinion = 75 }",
)
