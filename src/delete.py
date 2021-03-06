#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import os
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import getDataFilepaths

#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def delete(data_dir):
    """
    Delete the CSV data from disk.

    GIVEN:
      data_dir (str) -- the path to a directory containing CSV data

    RETURN:
      None
    """
    issues_file, commits_file, pull_requests_file = getDataFilepaths(data_dir)

    try:
        os.remove(issues_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(issues_file))

    try:
        os.remove(commits_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(commits_file))

    try:
        os.remove(pull_requests_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(pull_requests_file))


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
