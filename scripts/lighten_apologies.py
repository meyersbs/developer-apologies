#!/usr/bin/env python3

#### PYTHON IMPORTS ################################################################################
import csv
import multiprocessing as mproc
import numpy as np
import os
import re
import shutil
import sys
from pathlib import Path


#### CONFIG ########################################################################################
csv.field_size_limit(sys.maxsize)

#### GLOBALS #######################################################################################
ISSUES_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "ISSUE_NUMBER", "ISSUE_CREATION_DATE",
    "ISSUE_AUTHOR", "ISSUE_TITLE", "ISSUE_URL", "ISSUE_TEXT", "COMMENT_CREATION_DATE",
    "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT", "COMMENT_TEXT_LEMMATIZED","NUM_APOLOGY_LEMMAS"]
COMMITS_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
    "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE", "COMMIT_URL",
    "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT",
    "COMMENT_TEXT_LEMMATIZED", "NUM_APOLOGY_LEMMAS"]
PULL_REQUESTS_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "PULL_REQUEST_NUMBER",
    "PULL_REQUEST_TITLE", "PULL_REQUEST_AUTHOR", "PULL_REQUEST_CREATION_DATE", "PULL_REQUEST_URL",
    "PULL_REQUEST_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT",
    "COMMENT_TEXT_LEMMATIZED", "NUM_APOLOGY_LEMMAS"]


#### FUNCTIONS #####################################################################################
def fixNullBytes(file_pointer):
    """
    Replaces null bytes with "<NULL>" so csv.reader() doesn't produce an error.

    GIVEN:
      file_pointer (...) -- pointer to an open file
    """
    for line in file_pointer:
        yield line.replace("\0", "<NULL>")


def getDataFilepaths(data_dir):
    """
    Get filepaths for issues, commits, and pull requests in the given data_dir.

    GIVEN:
      data_dir (str) -- absolute path to data

    RETURN:
      issues_file (str) -- absolute path to issues CSV
      commits_file (str) -- absolute path to commits CSV
      pull_requests_file (str) -- absolute path to pull requests CSV
    """

    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")

    return [issues_file, commits_file, pull_requests_file]


def canonicalize(top_dir):
    """
    Canonicalize filepath.

    GIVEN:
      top_dir (str) -- relative filepath

    RETURN:
      _ (str) -- absolute filepath for top_dir
    """
    return os.path.realpath(top_dir)


def getSubDirNames(top_dir):
    """
    Get the names of subdirectories, one level deep.
    """
    return [d[1] for d in os.walk(top_dir)][0]


def _getRows(old_file):
    rows = list()
    with open(old_file, "r") as f:
        csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
        next(csv_reader)
        for line in csv_reader:
            rows.append(line)

    return rows


def _writeLightApologies(new_file, src, light_rows):
    if src == "is":
        print("        Writing {}...".format(new_file))
        header_row = ["REPO_URL", "ISSUE_URL", "COMMENT_URL", "COMMENT_TEXT", "NUM_APOLOGY_LEMMAS"]
        with open(new_file, "w") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header_row)
            for row in light_rows:
                csv_writer.writerow(row)
    elif src == "co":
        print("        Writing {}...".format(new_file))
        header_row = ["REPO_URL", "COMMIT_URL", "COMMENT_URL", "COMMENT_TEXT", "NUM_APOLOGY_LEMMAS"]
        with open(new_file, "w") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header_row)
            for row in light_rows:
                csv_writer.writerow(row)
    elif src == "pr":
        print("        Writing {}...".format(new_file))
        header_row = ["REPO_URL", "PULL_REQUEST_URL", "COMMENT_URL", "COMMENT_TEXT", "NUM_APOLOGY_LEMMAS"]
        with open(new_file, "w") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header_row)
            for row in light_rows:
                csv_writer.writerow(row)


def _getLightRowsIS(old_row):
    new_row = [
        old_row[0],	# REPO_URL
        old_row[7],	# ISSUE_URL
        old_row[11],	# COMMENT_URL
        old_row[12],	# COMMENT_TEXT
        old_row[14]	# NUM_APOLOGY_LEMMAS
    ]
    return new_row


def _getLightRowsCO(old_row):
    new_row = [
        old_row[0],	# REPO_URL
        old_row[9],	# COMMIT_URL
        old_row[13],	# COMMENT_URL
        old_row[14],	# COMMENT_TEXT
        old_row[16]	# NUM_APOLOGY_LEMMAS
    ]
    return new_row


def _getLightRowsPR(old_row):
    new_row = [
        old_row[0],	# REPO_URL
        old_row[7],	# PULL_REQUEST_URL
        old_row[11],	# COMMENT_URL
        old_row[12],	# COMMENT_TEXT
        old_row[14]	# NUM_APOLOGY_LEMMAS
    ]
    return new_row


def _getLightApologies(old_file, new_file, src, mproc_pool):
    rows = _getRows(old_file)
    if src == "is":
        light_rows = mproc_pool.map(_getLightRowsIS, rows)
    elif src == "co":
        light_rows = mproc_pool.map(_getLightRowsCO, rows)
    elif src == "pr":
        light_rows = mproc_pool.map(_getLightRowsPR, rows)
    del rows
    _writeLightApologies(new_file, src, light_rows)


def lightenApologies(top_dir, sub_dirs, num_cpus):
    pool = mproc.Pool(num_cpus)

    for sub_dir in sub_dirs:
        curr_data_dir = os.path.join(top_dir, sub_dir)
        print("Lightening {}...".format(curr_data_dir))
        is_file, co_file, pr_file = getDataFilepaths(curr_data_dir)

        new_is_file = is_file.split(".csv")[0] + "_light.csv"
        new_co_file = co_file.split(".csv")[0] + "_light.csv"
        new_pr_file = pr_file.split(".csv")[0] + "_light.csv"

        if os.path.exists(is_file):
            print("    Lightening {}...".format(is_file))
            _getLightApologies(is_file, new_is_file, "is", pool)
        if os.path.exists(co_file):
            print("    Lightening {}...".format(co_file))
            _getLightApologies(co_file, new_co_file, "co", pool)
        if os.path.exists(pr_file):
            print("    Lightening {}...".format(pr_file))
            _getLightApologies(pr_file, new_pr_file, "pr", pool)


#### MAIN ##########################################################################################
if __name__ == "__main__":
    top_dir = canonicalize(sys.argv[1])
    num_cpus = int(sys.argv[2])
    dir_names = getSubDirNames(top_dir)
    lightenApologies(top_dir, dir_names, num_cpus)
