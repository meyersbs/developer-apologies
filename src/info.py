#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import h5py
import numpy as np
import sys
csv.field_size_limit(sys.maxsize)
from collections import OrderedDict
from pprint import PrettyPrinter


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, getDataFilepaths, getFileSizeMB, getFileCreationTime, \
    getFileModifiedTime


#### GLOBALS #######################################################################################
PP = PrettyPrinter(width=120)

#### FUNCTIONS #####################################################################################
def _fixNullBytes(file_pointer):
    """
    Helper function for _getStats(). Replaces null bytes with "<NULL>" so csv.reader() doesn't
    produce an error.

    GIVEN:
      file_pointer (...) -- pointer to an open file
    """
    for line in file_pointer:
        yield line.replace("\0", "<NULL>")


def _getStats(filepath):
    """
    Helper function for infoData(). Count the number of repos, (issues or commits or pull requests),
    and comments in a CSV file.

    GIVEN:
      filepath (str) -- filepath to a CSV containing issues, commits, or pull requests and their
                        comments

    RETURN:
      num_entries (int) -- number of issues, commits, or pull requests
      num_comments (int) -- number of comments
      repos_list (list) -- list of repository URLs
    """

    repos = dict()
    num_entries = 0
    num_comments = 0

    with open(filepath, "r") as f:
        csv_reader = csv.reader(_fixNullBytes(f), delimiter=",", quotechar="\"")

        next(csv_reader) # Skip header row
        # For each entry
        for line in csv_reader:
            if line[0] == "REPO_URL":
                pass
            else:
                # If we haven't seen this repo before
                if line[0] not in repos.keys():
                    repos.update({line[0]: [line[3]]})
                else:
                    if line[3] not in repos[line[0]]:
                        repos[line[0]].append(line[3])

                if line[-1] != "":
                    num_comments += 1

    for k, v in repos.items():
        num_entries += len(v)

    repos_list = list(repos.keys())

    return [num_entries, num_comments, repos_list]


def infoData(data_dir, verbose=True):
    """
    Print the total number of repos, issues, commits, pull requests, and comments for each.

    GIVEN:
      data_dir (str) -- absolute path to a directory containing data
      verbose (bool) -- flag to turn off printing during unit testing

    RETURN:
      num_repos (int) -- number of repositories
      num_issues (int) -- number of issues
      num_issue_comments (int) -- number of issue comments
      num_commits (int) -- number of commits
      num_commit_comments (int) -- number of commit comments
      num_pull_requests (int) -- number of pull requests
      num_pull_request_comments (int) -- number of pull request comments
    """

    issues_file, commits_file, pull_requests_file = getDataFilepaths(data_dir)

    repos_list = list()
    num_repos = 0
    num_issues = 0
    num_issue_comments = 0
    num_commits = 0
    num_commit_comments = 0
    num_pull_requests = 0
    num_pull_request_comments = 0

    if doesPathExist(issues_file): # pragma: no cover
        num_issues, num_issue_comments, repos = _getStats(issues_file)
        repos_list.extend(repos)

    if doesPathExist(commits_file): # pragma: no cover
        num_commits, num_commit_comments, repos = _getStats(commits_file)
        repos_list.extend(repos)

    if doesPathExist(pull_requests_file): # pragma: no cover
        num_pull_requests, num_pull_request_comments, repos = _getStats(pull_requests_file)
        repos_list.extend(repos)

    num_repos = len(list(set(repos_list)))

    if verbose: # pragma: no cover
        print("Data Directory: {}".format(data_dir))
        print("\t# Repos: {}".format(num_repos))
        print("\t# Issues: {}".format(num_issues))
        print("\t# Issue Comments: {}".format(num_issue_comments))
        print("\t# Commits: {}".format(num_commits))
        print("\t# Commit Comments: {}".format(num_commit_comments))
        print("\t# Pull Requests: {}".format(num_pull_requests))
        print("\t# Pull Request Comments: {}".format(num_pull_request_comments))

    return [
        num_repos, num_issues, num_issue_comments, num_commits, num_commit_comments, num_pull_requests,
        num_pull_request_comments
    ]


def infoHDF5(hdf5_file, verbose=True):
    """
    Display useful information about the HDF5 file and its contents.

    GIVEN:
      hdf5_file (str) -- absolute path to an HDF5 file
      verbose (bool) -- flag to turn off printing during unit testing

    RETURN:
      metadata (OrderedDict) -- metadata for the HDF5 file
    """
    # Open the file
    f = h5py.File(hdf5_file, "r")

    # Get metadata
    metadata = OrderedDict()
    metadata.update({"filepath": hdf5_file})
    metadata.update({"keys": list(f.keys())})
    metadata.update({"filesize": "{} MB".format(round(getFileSizeMB(hdf5_file), 2))})
    metadata.update({"creation": getFileCreationTime(hdf5_file)})
    metadata.update({"modified": getFileModifiedTime(hdf5_file)})
    for dataset in list(f.keys()):
        ds_len = f[dataset][:].shape[0]
        ds_description = dict(f[dataset].attrs)["description"]
        if ds_len == 0:
            ds_repos = 0
        else:
            df = f[dataset][:]
            df = df[1:, ]
            repo_urls = df[:, 0]
            ds_repos = len(np.unique(repo_urls))
        metadata.update({
            dataset: OrderedDict({
                "num_items": ds_len,
                "num_repos": ds_repos,
                "description": ds_description
            })
        })

    # Cleanup
    h5py.File.close(f)

    # Display
    if verbose: # pragma: no cover
        PP.pprint(metadata)

    return metadata


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
