#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import os


#### PACKAGE IMPORTS ###############################################################################


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
    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")

    try:
        print("Deleting {}".format(issues_file))
        os.remove(issues_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(issues_file))

    try:
        print("Deleting {}".format(commits_file))
        os.remove(commits_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(commits_file))

    try:
        print("Deleting {}".format(pull_requests_file))
        os.remove(pull_requests_file)
    except FileNotFoundError:
        print("\tFile '{}' does not exist.".format(pull_requests_file))


#### MAIN ##########################################################################################
