##!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import datetime
import os
import sys
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################


#### GLOBALS #######################################################################################


#### CLASSES #######################################################################################
class InvalidGitHubURLError(Exception):
    """
    Exception raised by parseRepoURL() when the provided input is not a valid GitHub repository.
    """
    pass


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
        #print("Created: {}".format(issues_path))
    else:
        Path(os.path.join(issues_path), "__init__.py").touch()
    
    if not doesPathExist(commits_path):
        os.mkdir(commits_path)
        Path(os.path.join(commits_path), "__init__.py").touch()
        #print("Created: {}".format(commits_path))
    else:
        Path(os.path.join(commits_path), "__init__.py").touch()
    
    if not doesPathExist(pull_requests_path):
        os.mkdir(pull_requests_path)
        Path(os.path.join(pull_requests_path), "__init__.py").touch()
        #print("Created: {}".format(pull_requests_path))
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

    if not repo_url.startswith("https://github.com/"):
        raise InvalidGitHubURLError(
            "The URL '{}' is not a valid GitHub repository.".format(repo_url))

    repo_owner = repo_url.split("/")[3]
    repo_name = repo_url.split("/")[4]

    return repo_owner, repo_name


def numpyByteArrayToStrList(numpy_byte_array):
    """
    Convert a numpy array containing byte strings to a regular list containing strings.

    GIVEN:
      numpy_byte_array (array) -- numpy array containing byte strings

    RETURN:
      string_list (list) -- list containing regular strings
    """
    string_list = numpy_byte_array.astype(str).tolist()
    return string_list


def getFileSizeMB(filepath):
    """
    Get the filesize (in MB) of the given file.

    GIVEN:
      filepath (str) -- absolute path to a file

    RETURN:
      size_mb (float) -- size of the file in MB
    """
    size_bytes = os.path.getsize(filepath)
    size_mb = float(size_bytes) / (1024 * 1024)
    return size_mb


def getFileCreationTime(filepath):
    """
    Get the creation date for a file.

    GIVEN:
      filepath (str) -- absolute path to a file

    RETURN:
      creation_time (str) -- timestamp of the file's creation date
    """
    filename = Path(filepath)
    creation_time = datetime.datetime.fromtimestamp(filename.stat().st_ctime)
    creation_time = creation_time.strftime("%Y/%m/%d @ %H:%M:%S")
    return creation_time


def getFileModifiedTime(filepath):
    """
    Get the modification date for a file.

    GIVEN:
      filepath (str) -- absolute path to a file

    RETURN:
      modification_time (str) -- timestamp of the file's modification date
    """
    filename = Path(filepath)
    modification_time = datetime.datetime.fromtimestamp(filename.stat().st_mtime)
    modification_time = modification_time.strftime("%Y/%m/%d @ %H:%M:%S")
    return modification_time


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
