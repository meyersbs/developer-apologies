#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import h5py
import multiprocessing as mproc
import numpy as np
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import numpyByteArrayToStrList


#### GLOBALS #######################################################################################
APOLOGY_LEMMAS = [
    "apology", "apologise", "apologize", "blame", "excuse", "fault", "forgive", "mistake",
    "mistaken", "oops", "pardon", "regret", "sorry"
]
APOLOGY_SIMPLE_PHRASES = [
    "blame me", "excuse me", "forgive me", "i regret", "i shouldn't have", "i should not have",
    "i wasn't thinking", "i was confused", "i was not thinking", "i'm afraid", "i am afraid",
    "it was wrong of me", "it will not happen again", "it won't happen again", "my bad",
    "my fault", "my mistake", "pardon me"
]
APOLOGY_COMPLEX_PHRASES = [
    ["i", "", "apologise"],
    ["i", "", "apologize"],
    ["i'll never", "", "again"],
    ["i'm", "", "sorry"],
    ["i'm afraid", ""],
    ["i'm sorry if", "", "hurt"],
    ["i am", "", "sorry"],
    ["i am afraid", ""],
    ["i am sorry if", "", "hurt"],
    ["i didn't mean to", ""],
    ["i didn't intend to", ""],
    ["i did not mean to", ""],
    ["i did not intend to", ""],
    ["i feel", "", "awful"],
    ["i feel", "", "bad"],
    ["i owe", "", "an apology"],
    ["i will never", "", "again"]
]

#### FUNCTIONS #####################################################################################
def _countApologies(lemmas):
    """
    Count the occurrences of apology lemmas in the given lemmas.

    GIVEN:
      lemmas (str) -- string of lemmatized text

    RETURN:
      num_apology_lemmas (str) -- number of occurrences of apology lemmas
    """
    num_apology_lemmas = 0
    lems = lemmas.split(" ")
    for lem in lems:
        for apology in APOLOGY_LEMMAS:
            if apology == lem:
                num_apology_lemmas += 1

    return str(num_apology_lemmas)


def classify(hdf5_file, num_procs):
    """
    Count the number of apologies in each lemmatized comment.

    GIVEN:
      hdf5_file (str) -- path to a populated HDF5 file
      num_procs (int) -- number of processes (CPUs) to use for multiprocessing

    RETURN:
      issue_apologies (np.array) -- apology counts for lemmatized issue comments
      commit_apologies (np.array) -- apology counts for lemmatized commit comments
      pull_request_apologies (np.array) -- apology counts for lemmatized pull request comments
    """
    # Return variables
    issue_apologies = list()
    commit_apologies = list()
    pull_request_apologies = list()

    # Grab the data
    f = h5py.File(hdf5_file, "r+") # read/write mode 
    issues = f["issues"][...]
    commits = f["commits"][...]
    pull_requests = f["pull_requests"][...]

    # Datasets might be empty, so we need to check this
    do_issues = False
    do_commits = False
    do_pull_requests = False
    if issues.shape[0] > 0: # pragma: no cover
        do_issues = True
    if commits.shape[0] > 0: # pragma: no cover
        do_commits = True
    if pull_requests.shape[0] > 0: # pragma: no cover
        do_pull_requests = True

    # Create the process pool
    pool = mproc.Pool(num_procs)

    # There are pragmas here because coverage is confused.
    if do_issues: # pragma: no cover
        # Get just the lemmas
        issue_lemmas = issues[:, -1]
        # Convert bytestrings to strings
        issue_lemmas = numpyByteArrayToStrList(issue_lemmas)
        # Classify apologies
        issue_apologies = np.array(pool.map(_countApologies, issue_lemmas), dtype=str)
        # Add header
        issue_apologies = issue_apologies.tolist()
        issue_apologies[0] = "NUM_APOLOGY_LEMMAS"
        # Reshape the apologies array
        apologies = np.array(issue_apologies, dtype=str).reshape((len(issue_apologies), 1))
        # Resize dataset
        f["issues"].resize((issues.shape[0], issues.shape[1] + 1))
        # Add apology counts to HDF5 file
        f["issues"][...] = np.hstack((issues, apologies))
    else: # pragma: no cover
        pass

    if do_commits: # pragma: no cover
        # Get just the lemmas
        commit_lemmas = commits[:, -1]
        # Convert bytestrings to strings
        commit_lemmas = numpyByteArrayToStrList(commit_lemmas)
        # Classify apologies
        commit_apologies = np.array(pool.map(_countApologies, commit_lemmas), dtype=str)
        # Add header
        commit_apologies = commit_apologies.tolist()
        commit_apologies[0] = "NUM_APOLOGY_LEMMAS"
        # Reshape the apologies array
        apologies = np.array(commit_apologies, dtype=str).reshape((len(commit_apologies), 1))
        # Resize dataset
        f["commits"].resize((commits.shape[0], commits.shape[1] + 1))
        # Add apology counts to HDF5 file
        f["commits"][...] = np.hstack((commits, apologies))
    else: # pragma: no cover
        pass

    if do_pull_requests: # pragma: no cover
        # Get just the lemmas
        pull_request_lemmas = pull_requests[:, -1]
        # Convert bytestrings to strings
        pull_request_lemmas = numpyByteArrayToStrList(pull_request_lemmas)
        # Classify apologies
        pull_request_apologies = np.array(
            pool.map(_countApologies, pull_request_lemmas), dtype=str)
        # Add header
        pull_request_apologies = pull_request_apologies.tolist()
        pull_request_apologies[0] = "NUM_APOLOGY_LEMMAS"
        # Reshape the apologies array
        apologies = np.array(
            pull_request_apologies, dtype=str).reshape((len(pull_request_apologies), 1))
        # Resize dataset
        f["pull_requests"].resize((pull_requests.shape[0], pull_requests.shape[1] + 1))
        # Add apology counts to HDF5 file
        f["pull_requests"][...] = np.hstack((pull_requests, apologies))
    else: # pragma: no cover
        pass

    # Close HDF5 file
    h5py.File.close(f)
    print("Number of apologies saved to: {}".format(hdf5_file))

    # Return number of apologies (this is used for unit tests)
    return [issue_apologies, commit_apologies, pull_request_apologies]


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
