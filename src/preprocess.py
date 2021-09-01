#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import h5py
import multiprocessing as mproc
import numpy as np
import re
import spacy
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import numpyByteArrayToStrList


#### GLOBALS #######################################################################################
NLP = spacy.load("en_core_web_sm")
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


def preprocess(hdf5_file, num_procs):
    """

    """
    # Return variables
    issue_lemmas = None
    commit_lemmas = None
    pull_request_lemmas = None

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

    # Issues
    # There are pragmas here because coverage is confused.
    if do_issues: # pragma: no cover
        # Get just the comments
        issue_comments = issues[:, 12]
        # Remove header row
        issue_comments = np.delete(issue_comments, (0), axis=0)
        # Convert bytestrings to strings
        issue_comments = numpyByteArrayToStrList(issue_comments)
        # Remove punctuation and non-space whitespace
        issue_comments = np.array(pool.map(_stripNonWords, issue_comments), dtype=str)
        # Lemmatize comments
        issue_lemmas = np.array(pool.map(_lemmatize, issue_comments), dtype=str)
        # Add header
        lemmas = np.insert(issue_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        # Reshape the lemmas array
        lemmas = np.array(lemmas, dtype=str).reshape((len(lemmas), 1))
        # Resize dataset
        f["issues"].resize((issues.shape[0], issues.shape[1] + 1))
        # Add lemmas to HDF5 file
        f["issues"][...] = np.hstack((issues, lemmas))
    else: # pragma: no cover
        pass

    if do_commits: # pragma: no cover
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
        # Add header
        lemmas = np.insert(commit_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        # Reshape the lemmas array
        lemmas = np.array(lemmas, dtype=str).reshape((len(lemmas), 1))
        # Resize dataset
        f["commits"].resize((commits.shape[0], commits.shape[1] + 1))
        # Add lemmas to HDF5 file
        f["commits"][...] = np.hstack((commits, lemmas))
    else: # pragma: no cover
        pass

    if do_pull_requests: # pragma: no cover
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
        # Add header
        lemmas = np.insert(pull_request_lemmas, 0, "COMMENT_TEXT_LEMMATIZED", axis=0)
        # Reshape the lemmas array
        lemmas = np.array(lemmas, dtype=str).reshape((len(lemmas), 1))
        # Resize dataset
        f["pull_requests"].resize((pull_requests.shape[0], pull_requests.shape[1] + 1))
        # Add lemmas to HDF5 file
        f["pull_requests"][...] = np.hstack((pull_requests, lemmas))
    else: # pragma: no cover
        pass

    # Close HDF5 file
    h5py.File.close(f)
    print("Lemmatized comments saved to: {}".format(hdf5_file))

    # Return lemmatized comments (this is used for unit tests)
    return [issue_lemmas, commit_lemmas, pull_request_lemmas]


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
