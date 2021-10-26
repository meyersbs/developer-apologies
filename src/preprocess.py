#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import h5py
import multiprocessing as mproc
import numpy as np
#import os
#import psutil
import re
import spacy
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import numpyByteArrayToStrList


#### GLOBALS #######################################################################################
try:
    NLP = spacy.load("en_core_web_sm")
except OSError: # pragma: no cover
    NLP = spacy.load("en") 
RE_PUNCT = re.compile(r"[\.,:;?!]")
RE_WHITESPACE = re.compile(r"[\n\r\t\v\f]") # everything but regular spaces
RE_DUPLICATE_SPACES = re.compile(r"[\s]+")


#### FUNCTIONS #####################################################################################
def _stripNonWords(comment):
    """
    Lowercase, remove punctuation, and remove unnecessary whitespace.

    GIVEN:
      comment (str) -- natural language text

    RETURN:
      clean_comment (str) -- lowercased comment with punctuation and non-space whitespace removed
    RETURN:
    """
    clean_comment = RE_PUNCT.sub("", comment.lower())
    clean_comment = RE_WHITESPACE.sub(" ", clean_comment)
    clean_comment = RE_DUPLICATE_SPACES.sub(" ", clean_comment)
    return clean_comment


def _lemmatize(comment):
    """
    Convert words in a comment into lemmas.

    GIVEN:
      comment (str) -- natural language text

    RETURN:
      lemmatized_comment (str) -- comment with words converted to lemmas
    """
    comment = NLP(str(comment))
    lemmas = [token.lemma_ for token in comment]
    lemmatized_comment = " ".join(lemmas)
    return lemmatized_comment


def preprocess(hdf5_file, num_procs, test=False):
    """
    Clean up comments by lowercasing, removing punctuation and non-space whitespace, and
    lemmatizing.

    GIVEN:
      hdf5_file (str) -- path to a populated HDF5 file
      num_procs (int) -- number of processes (CPUs) to use for multiprocessing
      test (bool) -- flag for unit tests

    RETURN:
      issue_lemmas (np.array) -- lemmatized issue comments
      commit_lemmas (np.array) -- lemmatized commit comments
      pull_request_lemmas (np.array) -- lemmatized pull request comments
    """
    # Instantiate variables
    issue_lemmas = None
    commit_lemmas = None
    pull_request_lemmas = None

    # Return variables
    i_lemmas = None
    c_lemmas = None
    p_lemmas = None

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

    del issues
    del commits
    del pull_requests

    # Create the process pool
    pool = mproc.Pool(num_procs)

    # There are pragmas here because coverage is confused.
    if do_issues: # pragma: no cover
        print("\tPreprocessing issues...")
        # Get issues
        issues = f["issues"][...]
        # Get just the comments
        issue_comments = issues[:, 12]
        print("Hi 1")
        #print("{} MB".format(psutil.Process(os.getpid()).memory_info().rss / 2014 ** 2))
        # Remove header row
        issue_comments = np.delete(issue_comments, (0), axis=0)
        print("Hi 2")
        # Convert bytestrings to strings
        issue_comments = numpyByteArrayToStrList(issue_comments)
        print("Hi 3")
        # Remove punctuation and non-space whitespace
        issue_comments = np.array(pool.map(_stripNonWords, issue_comments), dtype=str)
        print("Hi 4")
        # Lemmatize comments
        issue_lemmas = np.array(pool.map(_lemmatize, issue_comments), dtype=str)
        del issue_comments
        if test:
            i_lemmas = np.copy(issue_lemmas)
        print("Hi 5")
        # Add header
        issue_lemmas = np.insert(issue_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        print("Hi 6")
        # Reshape the lemmas array
        issue_lemmas = np.array(issue_lemmas, dtype=str).reshape((len(issue_lemmas), 1))
        print("Hi 7")
        # Resize dataset
        f["issues"].resize((issues.shape[0], issues.shape[1] + 1))
        print("Hi 8")
        # Add lemmas to HDF5 file
        f["issues"][...] = np.hstack((issues, issue_lemmas))
        print("Hi 9")
        del issues
    else: # pragma: no cover
        pass

    if do_commits: # pragma: no cover
        print("\tPreprocessing commits...")
        # Get commits
        commits = f["commits"][...]
        # Get just the comments
        commit_comments = commits[:, 14]
        # Remove header row
        commit_comments = np.delete(commit_comments, (0), axis=0)
        # Convert bytestrings to strings
        commit_comments = numpyByteArrayToStrList(commit_comments)
        # Remove punctuation and non-space whitespace
        commit_comments = np.array(pool.map(_stripNonWords, commit_comments), dtype=str)
        # Lemmatize comments
        commit_lemmas = np.array(pool.map(_lemmatize, commit_comments), dtype=str)
        del commit_comments
        if test:
            c_lemmas = np.copy(commit_lemmas)
        # Add header
        commit_lemmas = np.insert(commit_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        # Reshape the lemmas array
        commit_lemmas = np.array(commit_lemmas, dtype=str).reshape((len(commit_lemmas), 1))
        # Resize dataset
        f["commits"].resize((commits.shape[0], commits.shape[1] + 1))
        # Add lemmas to HDF5 file
        f["commits"][...] = np.hstack((commits, commit_lemmas))
        del commits
    else: # pragma: no cover
        pass

    if do_pull_requests: # pragma: no cover
        print("\tPreprocessing pull requests...")
        # Get pull requests
        pull_requests = f["pull_requests"][...]
        # Get just the comments
        pull_request_comments = pull_requests[:, 12]
        # Remove header row
        pull_request_comments = np.delete(pull_request_comments, (0), axis=0)
        # Convert bytestrings to strings
        pull_request_comments = numpyByteArrayToStrList(pull_request_comments)
        # Remove punctuation and non-space whitespace
        pull_request_comments = np.array(pool.map(_stripNonWords, pull_request_comments), dtype=str)
        # Lemmatize comments
        pull_request_lemmas = np.array(pool.map(_lemmatize, pull_request_comments), dtype=str)
        del pull_request_comments
        if test:
            p_lemmas = np.copy(pull_request_lemmas)
        # Add header
        pull_request_lemmas = np.insert(pull_request_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        # Reshape the lemmas array
        pull_request_lemmas = np.array(pull_request_lemmas, dtype=str).reshape((len(pull_request_lemmas), 1))
        # Resize dataset
        f["pull_requests"].resize((pull_requests.shape[0], pull_requests.shape[1] + 1))
        # Add lemmas to HDF5 file
        f["pull_requests"][...] = np.hstack((pull_requests, pull_request_lemmas))
        del pull_requests
    else: # pragma: no cover
        pass

    # Close HDF5 file
    h5py.File.close(f)
    print("Lemmatized comments saved to: {}".format(hdf5_file))

    # Return lemmatized comments (this is used for unit tests)
    return [i_lemmas, c_lemmas, p_lemmas]


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
