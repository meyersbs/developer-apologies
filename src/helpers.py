##!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import os
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def canonicalize(path):
    """
    Helper function to canonicalize filepaths.

    GIVEN:
      path (str) -- a filepath to canonicalize

    RETURN:
      ____ (str) -- a canonicalized filepath
    """
    return os.path.realpath(path)


def doesPathExist(path):
    """
    Helper function to determine if a filepath exists.

    GIVEN:
      path (str) -- a filepath to check for existence

    RETURN:
      ____ (bool) -- True if the given filepath exists, False otherwise
    """
    return os.path.exists(path)


def validateDataDir(data_dir):
    """
    Check the data_dir for the existence of required subdirectories. If they do not exist, create
    them.

    GIVEN:
      data_dir (str) -- directory path to check
    """
    issues_path = os.path.join(data_dir, "issues/")
    commits_path = os.path.join(data_dir, "commits/")
    pull_requests_path = os.path.join(data_dir, "pull_requests/")

    if not doesPathExist(issues_path):
        os.mkdir(issues_path)
        Path(os.path.join(issues_path), "__init__.py").touch()
        print("Created: {}".format(issues_path))
    else:
        Path(os.path.join(issues_path), "__init__.py").touch()
    
    if not doesPathExist(commits_path):
        os.mkdir(commits_path)
        Path(os.path.join(commits_path), "__init__.py").touch()
        print("Created: {}".format(commits_path))
    else:
        Path(os.path.join(commits_path), "__init__.py").touch()
    
    if not doesPathExist(pull_requests_path):
        os.mkdir(pull_requests_path)
        Path(os.path.join(pull_requests_path), "__init__.py").touch()
        print("Created: {}".format(pull_requests_path))
    else:
        Path(os.path.join(pull_requests_path), "__init__.py").touch()


def parseRepoURL(repo_url):
    """
    Parse a repository URL and grab the owner and name fields.

    GIVEN:
      repo_url (str) -- URL to parse; e.g. https://github.com/meyersbs/SPLAT

    RETURN:
      repo_owner (str) -- the owner of the repo; e.g. meyersbs
      repo_name (str) -- the name of the repo; e.g. SPLAT
    """
    repo_owner = repo_url.split("/")[3]
    repo_name = repo_url.split("/")[4]

    return repo_owner, repo_name

#### MAIN ##########################################################################################
