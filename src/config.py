#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import canonicalize


#### GLOBALS #######################################################################################
API_TOKEN_PATH = canonicalize("github_api_token.txt")


#### CLASSES #######################################################################################
class EmptyAPITokenError(Exception):
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
