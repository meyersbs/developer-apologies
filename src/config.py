#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import canonicalize


#### GLOBALS #######################################################################################
API_TOKEN_PATH = canonicalize("github_api_token.txt")


#### CLASSES #######################################################################################
class EmptyAPITokenError(Exception):
    """
    Exception raised by getAPIToken when API_TOKEN_PATH is an empty file.
    """
    pass


#### FUNCTIONS #####################################################################################
def getAPIToken(filepath=API_TOKEN_PATH):
    """
    Read the secret GitHub API token from 'github_api_token.txt'. 

    RETURN:
      api_token (str) -- GitHub API token
    """
    api_token = None
    with open(filepath, "r") as f:
        api_token = f.readline().strip("\n")

    if api_token == "":
        raise EmptyAPITokenError("GitHub API token cannot be empty!")

    return api_token


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
