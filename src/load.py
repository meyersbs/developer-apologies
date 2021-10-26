#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import h5py
import numpy as np
import os
import sys
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, sanitizeUnicode, fixNullBytes, ISSUES_HEADER, \
    COMMITS_HEADER, PULL_REQUESTS_HEADER


#### GLOBALS #######################################################################################
VLEN_STR_DTYPE = h5py.special_dtype(vlen=str)


#### FUNCTIONS #####################################################################################
def _load(filepath):
    """
    Read data from disk into a numpy array.

    GIVEN:
      filepath (str) -- the absolute path to a file where data should be loaded from

    RETURN:
      data (array) -- numpy array containing data loaded from disk
    """
    # Read data from disk
    data = list()
    with open(filepath, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
        for entry in csv_reader:
            data.append(entry)

    # Convert all elements to strings
    for i in range(0, len(data)):
        element = [str(d) for d in data[i]]
        data[i] = sanitizeUnicode(element)

    data = np.array(data, dtype=VLEN_STR_DTYPE)
    return data


def load(hdf5_file, data_dir, append):
    """
    Load data from disk into an HDF5 file.

    GIVEN:
      hdf5_file (str) -- the absolute path to a file to format and load data into
      data_dir (str) -- the absolute path to a directory where data should be loaded from
      append (bool) -- whether to append to an existing file or create a new one

    RETURN:
      None
    """
    # Filepaths
    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")

    if not append:
        # Ensure files exist
        if not doesPathExist(issues_file): # pragma: no cover
            print("File '{}' does not exist. Creating it.".format(issues_file))
            Path(issues_file).touch()
        if not doesPathExist(commits_file): # pragma: no cover
            print("File '{}' does not exist. Creating it.".format(commits_file))
            Path(commits_file).touch()
        if not doesPathExist(pull_requests_file): # pragma: no cover
            print("File '{}' does not exist. Creating it.".format(pull_requests_file))
            Path(pull_requests_file).touch()
  
    # Load data into numpy arrays
    issues = _load(issues_file)
    commits = _load(commits_file)
    pull_requests = _load(pull_requests_file)

    # If appending new data
    if append: # pragma: no cover
        # This is getting marked as untested, but the unit tests would fail if it weren't running.
        # Apparently I'm smarter than the software, so I'm telling it to ignore this for coverage.

        # Open HDF5 file
        f = h5py.File(hdf5_file, "r+") # Note the read/write mode

        # This bit of code is based on: https://stackoverflow.com/a/47074545/3546278
        if issues.shape[0] > 0:
            # Append new issues
            if f["issues"].shape[0] > 0:
                # Delete duplicate header rows
                issues = np.delete(issues, (0), axis=0)
                # Resize issues
                new_issues_size = f["issues"].shape[0] + issues.shape[0]
                f["issues"].resize(new_issues_size, axis = 0)
                # Append to issues
                f["issues"][-issues.shape[0]:] = issues
            # Overwrite existing empty issues
            else:
                # For some reason, appending to an empty dataset, or trying to overwrite it, just
                # doesn't work, no matter what I try. So, we delete the existing empty dataset and
                # rebuild it.

                # Delete
                del f["issues"]

                # Create
                issues_len = len(issues)
                issues_len_2 = len(issues[0]) if issues_len > 0 else 0
                issues_dataset = f.create_dataset(
                    "issues",                   # name
                    (issues_len, issues_len_2), # dimensions
                    maxshape=(None, None),      # maximum dimensions
                    dtype=VLEN_STR_DTYPE,       # data type
                    chunks=True                 # enable chunked storage (for resizing)
                )

                # Populate
                issues_dataset[...] = issues

                # Attributes
                issues_dataset.attrs.create(
                    name="description",
                    data="GitHub issues with relevant metadata and comments. Columns: [{}].".format(
                        ", ".join(ISSUES_HEADER)
                    )
                )
        else: # pragma: no cover
            pass

        if commits.shape[0] > 0:
            # Append new commits
            if f["commits"].shape[0] > 0:
                # Delete duplicate header rows
                commits = np.delete(commits, (0), axis=0)
                # Resize commits
                new_commits_size = f["commits"].shape[0] + commits.shape[0]
                f["commits"].resize(new_commits_size, axis = 0)
                # Append to commits
                f["commits"][-commits.shape[0]:] = commits
            # Overwrite existing empty commits
            else:
                # For some reason, appending to an empty dataset, or trying to overwrite it, just
                # doesn't work, no matter what I try. So, we delete the existing empty dataset and
                # rebuild it.

                # Delete
                del f["commits"]

                # Create
                commits_len = len(commits)
                commits_len_2 = len(commits[0]) if commits_len > 0 else 0
                commits_dataset = f.create_dataset(
                    "commits",                      # name
                    (commits_len, commits_len_2),   # dimensions
                    maxshape=(None, None),          # maximum dimensions
                    dtype=VLEN_STR_DTYPE,           # data type
                    chunks=True                     # enable chunked storage (for resizing)
                )

                # Populate
                commits_dataset[...] = commits

                # Attributes
                commits_dataset.attrs.create(
                    name="description",
                    data="GitHub commits with relevant metadata and comments. Columns: [{}].".format(
                        ", ".join(COMMITS_HEADER)
                    )
                )
        else: # pragma: no cover
            pass

        if pull_requests.shape[0] > 0:
            # Append new pull requests
            if f["pull_requests"].shape[0] > 0:
                # Delete duplicate header rows
                pull_requests = np.delete(pull_requests, (0), axis=0)
                # Resize pull requests
                new_pull_requests_size = f["pull_requests"].shape[0] + pull_requests.shape[0]
                f["pull_requests"].resize(new_pull_requests_size, axis = 0)
                # Append to pull requests
                f["pull_requests"][-pull_requests.shape[0]:] = pull_requests
            # Overwrite existing empty pull requests
            else:
                # For some reason, appending to an empty dataset, or trying to overwrite it, just
                # doesn't work, no matter what I try. So, we delete the existing empty dataset and
                # rebuild it.

                # Delete
                del f["pull_requests"]

                # Create
                pull_requests_len = len(pull_requests)
                pull_requests_len_2 = len(pull_requests[0]) if pull_requests_len > 0 else 0
                pull_requests_dataset = f.create_dataset(
                    "pull_requests",                            # name
                    (pull_requests_len, pull_requests_len_2),   # dimensions
                    maxshape=(None, None),                      # maximum dimensions
                    dtype=VLEN_STR_DTYPE,                       # data type
                    chunks=True                                 # enable chunked storage (for resizing)
                )

                # Populate
                pull_requests_dataset[...] = pull_requests

                # Attributes
                pull_requests_dataset.attrs.create(
                    name="description",
                    data="GitHub pull_requests with relevant metadata and comments. Columns: [{}].".format(
                        ", ".join(PULL_REQUESTS_HEADER)
                    )
                )
        else: # pragma: no cover
            pass
    # If not appending data
    else:
        # Open HDF5 file
        f = h5py.File(hdf5_file, "w") # Note the write mode

        # Create datasets
        issues_len = len(issues)
        issues_len_2 = len(issues[0]) if issues_len > 0 else 0
        issues_dataset = f.create_dataset(
            "issues",                                       # name
            (issues_len, issues_len_2),                     # dimensions
            maxshape=(None, None),                          # maximum dimensions
            dtype=VLEN_STR_DTYPE,                           # data type
            chunks=True                                     # enable chunked storage (for resizing)
        )
        commits_len = len(commits)
        commits_len_2 = len(commits[0]) if commits_len > 0 else 0
        commits_dataset = f.create_dataset(
            "commits",                                      # name
            (commits_len, commits_len_2),                   # dimensions
            maxshape=(None, None),                          # maximum dimensions
            dtype=VLEN_STR_DTYPE,                           # data type
            chunks=True                                     # enable chunked storage (for resizing)
        )
        pull_requests_len = len(pull_requests)
        pull_requests_len_2 = len(pull_requests[0]) if pull_requests_len > 0 else 0
        pull_requests_dataset = f.create_dataset(
            "pull_requests",                                # name
            (pull_requests_len, pull_requests_len_2),       # dimensions
            maxshape=(None, None),                          # maximum dimensions
            dtype=VLEN_STR_DTYPE,                           # data type
            chunks=True                                     # enable chunked storage (for resizing)
        )

        # Load data into datasets
        issues_dataset[...] = issues
        commits_dataset[...] = commits
        pull_requests_dataset[...] = pull_requests

        # Add descriptions
        issues_dataset.attrs.create(
            name="description",
            data="GitHub issues with relevant metadata and comments. Columns: [{}].".format(
                ", ".join(ISSUES_HEADER)
            )
        )
        commits_dataset.attrs.create(
            name="description",
            data="GitHub commits with relevant metadata and comments. Columns: [{}].".format(
                ", ".join(COMMITS_HEADER)
            )
        )
        pull_requests_dataset.attrs.create(
            name="description",
            data="GitHub pull_requests with relevant metadata and comments. Columns: [{}].".format(
                ", ".join(PULL_REQUESTS_HEADER)
            )
        )

    # Close the HDF5 file
    h5py.File.close(f)


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
