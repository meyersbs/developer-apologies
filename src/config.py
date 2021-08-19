#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import canonicalize


#### GLOBALS #######################################################################################
API_TOKEN_PATH = canonicalize("github_api_token.txt")


#### FUNCTIONS #####################################################################################
def getAPIToken():
    """
    Read the secret GitHub API token from 'github_api_token.txt'. 

    RETURN:
      api_token (str) -- GitHub API token
    """
    api_token = None
    #print(API_TOKEN_PATH)
    with open(API_TOKEN_PATH, "r") as f:
        api_token = f.readline().strip("\n")

    return api_token


#### MAIN ##########################################################################################
