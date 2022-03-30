#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import multiprocessing as mproc
import sys
from pathlib import Path
from shutil import copyfile


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, fixNullBytes, getDataFilepaths, overwriteFile


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
def _labelApologies(count):
    """
    Label apologies based on count of apology lemmas.

    GIVEN:
      count (str) -- string representation of number of apology lemmas

    RETURN:
      is_apology (str) -- string representation of apology label; 0 means not an apology, 1 means
                          apology
    """
    is_apology = 0
    if int(count) > 0:
        is_apology = 1

    return str(is_apology)


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


def _classify(old_file, new_file, num_procs):
    """
    Helper function for classify(). Handles multiprocessing for classification.

    GIVEN:
      old_file (str) -- path to CSV file to be classified
      new_file (str) -- path to new CSV file to store classified data
      num_procs (str) -- number of processes (CPUs) to use for multiprocessing

    RETURN:
      new_columns (list) -- 2D list of of [NUM_APOLOGY_LEMMAS, IS_APOLOGY]
    """
    Path(new_file).touch()
    old_file_rows = list()
    old_file_processed_comments = list()
    new_file_num_apology_lemmas = list()
    new_file_is_apology = list()
    new_columns = list()
    processed_comment_index = -1
    header = list()
    if doesPathExist(old_file):
        # Read file contents to list
        with open(old_file, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            header = next(csv_reader) # Skip header row
            for line in csv_reader:
                old_file_rows.append(line)

        # Get processed comments only
        for line in old_file_rows:
            old_file_processed_comments.append(line[processed_comment_index])

        # Create the process pool
        pool = mproc.Pool(num_procs)

        # Count apology lemmas
        new_file_num_apology_lemmas = pool.map(_countApologies, old_file_processed_comments)

        # Label apologies
        new_file_is_apology = pool.map(_labelApologies, new_file_num_apology_lemmas)

        # Combine columns
        for i in range(0, len(new_file_num_apology_lemmas)):
            new_columns.append([
                new_file_num_apology_lemmas[i],
                new_file_is_apology[i]
            ])

        # Update header with new columns
        header.append("NUM_APOLOGY_LEMMAS")
        header.append("IS_APOLOGY")

        # Write new columns to new_file
        with open(new_file, "w") as f:
            class_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            class_writer.writerow(header)
            for i in range(0, len(old_file_rows)):
                new_row = old_file_rows[i] + new_columns[i]
                class_writer.writerow(new_row)
    else: # pragma: no cover
        # Copy old_file to new_file
        copyfile(old_file, new_file)

    # Memory management
    del old_file_rows
    del old_file_processed_comments
    del new_file_num_apology_lemmas
    del new_file_is_apology

    # Return counts of apology lemmas and data labels
    return new_columns


def classify(data_dir, num_procs, overwrite=True):
    """
    Count the number of apologies in each lemmatized comment.

    GIVEN:
      data_dir (str) -- path to the lemmatized data
      num_procs (int) -- number of processes (CPUs) to use for multiprocessing
      overwrite (bool) -- whether or not to overwrite the old data file

    RETURN:
      i_classes (list) -- apology classifications for issues
      c_classes (list) -- apology classifications for commits
      p_classes (list) -- apology classifications for pull requests
    """
    issues_file, commits_file, pull_requests_file = getDataFilepaths(data_dir)

    class_issues_file = issues_file.split(".csv")[0] + "_classified.csv"
    class_commits_file = commits_file.split(".csv")[0] + "_classified.csv"
    class_pull_requests_file = pull_requests_file.split(".csv")[0] + "_classified.csv"

    i_classes = _classify(issues_file, class_issues_file, num_procs)
    c_classes = _classify(commits_file, class_commits_file, num_procs)
    p_classes = _classify(pull_requests_file, class_pull_requests_file, num_procs)

    if overwrite: # pragma: no cover
        overwriteFile(issues_file, class_issues_file)
        overwriteFile(commits_file, class_commits_file)
        overwriteFile(pull_requests_file, class_pull_requests_file)

    # Return classifications (this is used for unit tests)
    return [i_classes, c_classes, p_classes]


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
