#!/usr/bin/env python3
# Author(s): AngriestBird, Hiddengearz

import fnmatch
import logging
import os
import re
import sys
import time

import requests
from path_utils import clean_filepath

startTime = time.time()

__version__ = 1.0


# Function: check_basic_style
# Purpose: Validates files to ensure the basic stylization of MD is ensured.
def check_basic_style(filepath, bad_count, warningErrors, message):
    fixedErrors = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]

        for line in content:
            lineNum += 1
            if not line.startswith("#"):  # If the line doesn't start with a comment
                if "{" in line:  # if there is an open brace in this line
                    hasComment = re.search(
                        r"#.*[{}]+", line, re.M | re.I
                    )  # If comment at the start or before {
                    if (
                        not hasComment
                    ):  # if the line doesn't have a comment before the open brace
                        openBraces[0] += line.count("{")
                        # count total open braces and subtract open braces that are easy to find and used correctly
                        closingBraces = (
                            line.count("{") - line.count(" {\n") - line.count(" { ")
                        )

                        # if there are braces we couldn't find using efficient .count, use powerful inefficient regex
                        if closingBraces > 0:
                            hasNoSpace = re.search(
                                r"([^\s]+){|{([^\s]+)", line, re.M | re.I
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after open brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warningErrors += 1
                if "}" in line:  # if there is an close brace in this line
                    hasComment = re.search(
                        r"#.*[{}]+", line, re.M | re.I
                    )  # If comment at the start or before {
                    if (
                        not hasComment
                    ):  # if the line doesn't have a comment before the open brace
                        openBraces[0] += -line.count("}")
                        # count total close braces and subtract open braces that are easy to find and used correctly
                        openingBraces = (
                            line.count("}") - line.count(" }\n") - line.count(" } ")
                        )

                        # if there are braces we couldn't find using efficient .count, use powerful inefficient regex
                        if openingBraces > 0:
                            hasNoSpace = re.search(
                                r"([^\s]+)}|}([^\s]+)", line, re.M | re.I
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after close brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warningErrors += 1
                if '"' in line:  # if the line has a qoute
                    if (
                        line.count('"') % 2
                    ) != 0:  # if there are an odd number of qoutes on this line
                        hasComment = re.search(
                            r"#.*[\"]+", line, re.M | re.I
                        )  # If comment at the start or before "
                        if not hasComment:  # if there is no comment before the qoute
                            print(
                                "WARNING: Missing a quotation sign at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            warningErrors += 1

                if "=" in line:  # if the line has an equal sign
                    equalSign = 0
                    # count total equal signs that are easy to find and used correctly
                    equalSign = line.count("=") - line.count(" = ") - line.count(" =\n")

                    if (line.count("  =") > 0) or (line.count("=  ") > 0):
                        print(
                            "WARNING: Two spaces before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        equalSign = equalSign - line.count("  =") - line.count("=  ")
                        warningErrors += 1
                    if (
                        equalSign != 0
                    ):  # if there are equal signs that aren't used correctly
                        print(
                            "WARNING: Missing a space before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        warningErrors += 1
                if "    " in line:  # if 4 spaces in the line
                    print(
                        "WARNING: spaces indent (4) detected instead of tab at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    warningErrors += 1
                if openBraces[0] <= -1:
                    print(
                        "ERROR: A possible missing curly brace {{ in file {} {{line {1}}}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    openBraces[0] = 0
                    fixedErrors += 1

    file.close()

    return bad_count + fixedErrors, warningErrors, message


def main():
    logging.basicConfig(
        filename="pythontools.log", format="%(asctime)s %(message)s", filemode="w"
    )
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.info("Validating Basic Style - Secondary Check")
    message = "Validating Basic Style - Secondary Check\n"
    files_list = []
    bad_count = 0
    warningErrors = 0

    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    logger.debug("Checking the common folder...")
    for root, dirnames, filenames in os.walk(rootDir + "/" + "common" + "/"):
        for filename in fnmatch.filter(filenames, "*.txt"):
            files_list.append(os.path.join(root, filename))
    logger.debug("Common folder is checked...")

    logger.debug("Checking the events folder...")
    for root, dirnames, filenames in os.walk(rootDir + "/" + "events" + "/"):
        for filename in fnmatch.filter(filenames, "*.txt"):
            files_list.append(os.path.join(root, filename))
    logger.debug("Events folder is checked...")

    logger.debug("Checking the history folder...")
    for root, dirnames, filenames in os.walk(rootDir + "/" + "history" + "/"):
        for filename in fnmatch.filter(filenames, "*.txt"):
            files_list.append(os.path.join(root, filename))
    logger.debug("history folder is checked...")

    logger.debug("Checking the interface folder...")
    for root, dirnames, filenames in os.walk(rootDir + "/" + "interface" + "/"):
        for filename in fnmatch.filter(filenames, "*.txt"):
            files_list.append(os.path.join(root, filename))
    logger.debug("interface folder is checked...")

    for filename in files_list:
        try:
            bad_count, warningErrors, message = check_basic_style(
                filename, bad_count, warningErrors, message
            )
        except:
            print(
                f"{clean_filepath(filename)} has a potentially broken curly brace or some other fixes..."
            )
            bad_count += 1

    logger.info(
        "------\nChecked {0} files\nTotal Errors detected: {1}\nTotal Warnings detected: {2}".format(
            len(files_list), bad_count, warningErrors
        )
    )
    message = (
        message
        + "------\nChecked {0} files\nTotal Errors detected: {1}\nTotal Warnings Detected: {2}".format(
            len(files_list), bad_count, warningErrors
        )
    )
    if (bad_count == 0) and (warningErrors <= 4):
        logger.info("File validation PASSED")
        message = message + "File validation PASSED\n"
        postResults = False
    else:
        message = (
            message + "File validation FAILED\n Please fix all errors or warnings."
        )
        postResults = True

    logger.info("The script took {0} second!".format(time.time() - startTime))

    try:
        projectId = os.environ["CI_PROJECT_ID"]
        privateToken = privateToken = sys.argv[1]
        headers = {"PRIVATE-TOKEN": privateToken}
        payload = {"body": message}

        if postResults == True:
            if "CI_MERGE_REQUEST_IID" in os.environ:
                mergeRequestId = os.environ["CI_MERGE_REQUEST_IID"]
                r = requests.post(
                    "https://gitlab.com/api/v4/projects/"
                    + projectId
                    + "/merge_requests/"
                    + mergeRequestId
                    + "/discussions",
                    data=payload,
                    headers=headers,
                )
                print("Posted results to merge request")
            else:
                commitID = os.environ["CI_COMMIT_SHA"]
                r = requests.post(
                    "https://gitlab.com/api/v4/projects/"
                    + projectId
                    + "/commits/"
                    + commitID
                    + "/discussions",
                    data=payload,
                    headers=headers,
                )
                print("Posted results to commit")
        else:
            print("File validation passed Coding Standards: SUCCESS")
    except:
        print("Couldn't post results to gitlab")

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
