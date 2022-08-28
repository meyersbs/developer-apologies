#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import collections
import csv
import multiprocessing as mproc
import sys
from pathlib import Path
from shutil import copyfile


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, fixNullBytes, getDataFilepaths, getSubDirNames, overwriteFile


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def _flattenDicts(dict_list):
    """
    Helper function. Given a list of dictionaries, combine them into a single dictionary.

    GIVEN:
      dict_list (list) -- list of dictionaries

    RETURN:
      flattened_dict (dict) -- combined dictionary
    """
    # Get dictionary keys
    dict_keys = list()
    for d in dict_list:
        dict_keys.extend(d.keys())
    dict_keys = list(set(dict_keys))

    # Set up flattened dict
    flattened_dict = dict()
    for username in dict_keys:
        flattened_dict[username] = {"num_apology_lemmas": 0}

    # Combine dictionaries
    for d in dict_list:
        for username in d.keys():
            flattened_dict[username]["num_apology_lemmas"] += d[username]["num_apology_lemmas"]

    return flattened_dict


def _countDeveloperApologies(file_path, comment_author_index, num_apology_lemmas_index):
    """
    Helper function for _getDeveloperDicts(). Given a path to a CSV file and the column indexes for
    the comment author's username and the num_apology_lemmas, return a dictionary of developer
    usernames and apology_lemma_count.

    GIVEN:
      file_path (str) -- path to a CSV file
      comment_author_index (int) -- CSV index for "comment_author" column
      num_apology_lemmas_index (int) -- CSV index for "num_apology_lemmas" column

    RETURN:
      developers_dict (dict) -- dictionary with username keys pointing to sub-dictionaries with a
                                "num_apology_lemmas" key
    """
    developers_dict = dict()

    with open(file_path, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

        next(csv_reader) # Skip Header
        for line in csv_reader:
            comment_author = line[comment_author_index]

            if comment_author in developers_dict.keys():
                developers_dict[comment_author]["apology_lemma_count"] += int(line[16])
            else:
                developers_dict[comment_author] = {
                    "apology_lemma_count": int(line[num_apology_lemmas_index])
                }

    return developers_dict


def _getDeveloperDicts(language_dir):
    """
    Helper function for developerStats(). Given a data_dir for a specific language, get a
    dictionary of developer usernames and the number of apology lemmas in their comments.

    GIVEN:
      language_dir (str) -- path to language directory

    RETURN:
      developers_dict (dict) -- dictionary with username keys pointing to sub-dictionaries with a
                                "num_apology_lemmas" key
    """
    i_dict = dict()
    c_dict = dict()
    p_dict = dict()
    issues_file, commits_file, pull_requests_file = getDataFilepaths(language_dir)

    if doesPathExist(issues_file):
        i_dict = _countDeveloperApologies(issues_file, 12, 16)

    if doesPathExist(commits_file):
        c_dict = _countDeveloperApologies(commits_file, 12, 16)

    if doesPathExist(pull_request_file):
        p_dict = _countDeveloperApologies(pull_requests_file, 10, 14)

    developers_dict = _flattenDicts([i_dict, c_dict, p_dict])


def developerStats(data_dir, num_procs, overwrite=True):
    """

    """
    developer_dict = dict()

    language_dirs = getSubDirNames(data_dir)
    print(language_dirs)

    pool = mproc.Pool(num_procs)

    # Get a dictionary with username keys pointing to sub-dictionaries with keys for
    # "num_apology_lemmas"
    developer_dicts = pool.map(_getDeveloperDicts(language_dirs))
    developer_dict = _flattenDicts(developer_dicts)

    # Get list of unique usernames from our dataset
    developer_usernames = developer_dict.keys()

    # Compute other metrics
    pass


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
