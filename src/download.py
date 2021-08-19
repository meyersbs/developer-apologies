#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################


#### PACKAGE IMPORTS ###############################################################################
from src.graphql import runQuery
from src.helpers import validateDataDir, parseRepoURL


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def download(repo_file, data_dir, data_types):
    """
    Download data from GitHub repositories and save to disk.

    GIVEN:
      repo_file (str) -- the absolute path to a file containing repository URLs
      data_dir (str) -- the absolute path to a directory to store data in
      data_types (str) -- the type of data to download for each repo; one of ["issues", "commits",
                          "pull_requests", "all"]
    """

    # Make sure the necessary subdirectories exist
    validateDataDir(data_dir)

    with open(repo_file, "r") as f:
        # For each repository
        for line in f.readlines():
            # Get the the name of the repo and its owner
            repo_owner, repo_name = parseRepoURL(line.strip("\n"))

            # Run a GraphQL query
            results = runQuery(repo_owner, repo_name, data_types)
            print(results)


#### MAIN ##########################################################################################
