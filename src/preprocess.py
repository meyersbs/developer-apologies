#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import multiprocessing as mproc
import re
import spacy
import sys
from pathlib import Path
from shutil import copyfile


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, fixNullBytes, getDataFilepaths, overwriteFile


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


def _preprocess(old_file, new_file, num_procs):
    """
    Helper function for preprocess(). Handles multiprocessing for preprocessing.

    GIVEN:
      old_file (str) -- path to CSV file to be preprocessed
      new_file (str) -- path to new CSV file to store processed text
      num_procs (int) -- number of processes (CPUs) to use for multiprocessing

    RETURN:
      new_file_comments (list) -- list of processed comment text
    """
    Path(new_file).touch()
    old_file_rows = list()
    old_file_comments = list()
    new_file_comments = list()
    comments_index = -1
    header = list()
    if doesPathExist(old_file):
        # Read file contents to list
        with open(old_file, "r", encoding="utf=8") as f:
            csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            header = next(csv_reader) # Skip header row
            for line in csv_reader:
                old_file_rows.append(line)
       
        # Get raw comments only
        for line in old_file_rows:
            old_file_comments.append(line[comments_index])

        # Create the process pool
        pool = mproc.Pool(num_procs)

        # Lowercase, remove punctuation, remove unnecessary whitespace
        new_file_comments = pool.map(_stripNonWords, old_file_comments)

        # Lemmatize
        new_file_comments = pool.map(_lemmatize, new_file_comments)

        # Update header with new column
        header.append("COMMENT_TEXT_LEMMATIZED")

        # Write new column to new_file
        with open(new_file, "w") as f:
            preproc_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            preproc_writer.writerow(header)
            for i in range(0, len(old_file_rows)):
                new_row = old_file_rows[i] + [new_file_comments[i]]
                preproc_writer.writerow(new_row)
    else: # pragma: no cover
        # Copy old_file to new_file
        copyfile(old_file, new_file)

    # Memory management
    del old_file_rows
    del old_file_comments

    # Return lemmatized comments
    return new_file_comments


def preprocess(data_dir, num_procs, overwrite=True, test=False):
    """
    Clean up comments by lowercasing, removing punctuation and non-space whitespace, and
    lemmatizing.

    GIVEN:
      data_dir (str) -- path to downloaded data
      num_procs (int) -- number of processes (CPUs) to use for multiprocessing
      overwrite (bool) -- whether or not to overwrite the old data file
      test (bool) -- flag for unit tests

    RETURN:
       i_lemmas (list) -- lemmatized issue comments
       c_lemmas (list) -- lemmatized commit comments
       p_lemmas (list) -- lemmatized pull request comments
    """
    issues_file, commits_file, pull_requests_file = getDataFilepaths(data_dir)

    pre_issues_file = issues_file.split(".csv")[0] + "_preprocessed.csv"
    pre_commits_file = commits_file.split(".csv")[0] + "_preprocessed.csv"
    pre_pull_requests_file = pull_requests_file.split(".csv")[0] + "_preprocessed.csv"

    i_lemmas = _preprocess(issues_file, pre_issues_file, num_procs)
    c_lemmas = _preprocess(commits_file, pre_commits_file, num_procs)
    p_lemmas = _preprocess(pull_requests_file, pre_pull_requests_file, num_procs)

    if overwrite: # pragma: no cover
        overwriteFile(issues_file, pre_issues_file)
        overwriteFile(commits_file, pre_commits_file)
        overwriteFile(pull_requests_file, pre_pull_requests_file)

    # Return lemmatized comments (this is used for unit tests)
    return [i_lemmas, c_lemmas, p_lemmas]


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
