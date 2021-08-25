#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import h5py
import numpy as np
import os
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.download import ISSUES_HEADER, COMMITS_HEADER, PULL_REQUESTS_HEADER


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
    with open(filepath, "r") as f:
        csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
        for entry in csv_reader:
            data.append(entry)

    # Convert all elements to strings
    for i in range(0, len(data)):
        element = [str(d) for d in data[i]]
        data[i] = element

    data = np.array(data, dtype=VLEN_STR_DTYPE)
    return data


def load(hdf5_file, data_dir):
    """
    Load data from disk into an HDF5 file.

    GIVEN:
      hdf5_file (str) -- the absolute path to a file to format and load data into
      data_dir (str) -- the absolute path to a directory where data should be loaded from
    """
    # Filepaths
    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")
    
    # Load data into numpy arrays
    issues = _load(issues_file)
    commits = _load(commits_file)
    pull_requests = _load(pull_requests_file)

    # Create HDF5 file
    f = h5py.File(hdf5_file, "w")

    # Create datasets
    issues_dataset = f.create_dataset(
        "issues",                                       # name
        (len(issues), len(issues[0])),                  # dimensions
        maxshape=(None, ),                              # maximum dimensions
        dtype=VLEN_STR_DTYPE,                           # data type
        chunks=True                                     # enable chunked storage (for resizing)
    )
    commits_dataset = f.create_dataset(
        "commits",                                      # name
        (len(commits), len(commits[0])),                # dimensions
        maxshape=(None, ),                              # maximum dimensions
        dtype=VLEN_STR_DTYPE,                           # data type
        chunks=True                                     # enable chunked storage (for resizing)
    )
    pull_requests_dataset = f.create_dataset(
        "issues",                                       # name
        (len(pull_requests), len(pull_requests[0])),    # dimensions
        maxshape=(None, ),                              # maximum dimensions
        dtype=VLEN_STR_DTYPE,                           # data type
        chunks=True                                     # enable chunked storage (for resizing)
    )

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
