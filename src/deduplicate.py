#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import os
import sys
from pathlib import Path
from shutil import copyfile


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, fixNullBytes, getDataFilepaths, overwriteFile, \
    ISSUES_HEADER, COMMITS_HEADER, PULL_REQUESTS_HEADER


#### GLOBALS #######################################################################################


#### CLASSES #######################################################################################


#### FUNCTIONS #####################################################################################
def _deduplicate(old_file, new_file, header):
    """
    Helper function for deduplicate(). Remove duplicate header rows from downloaded CSV files.

    GIVEN:
      old_file (str) -- path to downloaded file
      new_file (str) -- path to store deduplicated old_file
      header (list) -- header row to deduplicate

    RETURN:
      None
    """
    Path(new_file).touch()
    if doesPathExist(old_file):
        # Set up dedup file access
        f_dedup = open(new_file, "a")
        dedup_writer = csv.writer(f_dedup, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
        # Keep track of whether we've seen the header row before
        seen_header = False
        # Open file with duplicates
        with open(old_file, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(fixNullBytes(f), delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
            for entry in csv_reader:
                # If the current entry is the header row
                if entry == header:
                    #print("Found header!")
                    # If we haven't seen the header row before, write it
                    if not seen_header:
                        #print("Writing header!")
                        dedup_writer.writerow(entry)
                        seen_header = True
                    else: # pragma: no cover
                        #print("Skipping header!")
                        pass
                else:
                    dedup_writer.writerow(entry)
        f_dedup.close()
    else: # pragma: no cover
        # Copy of the old_file to the new_file
        copyfile(old_file, new_file)


def deduplicate(data_dir, overwrite=False):
    """
    Remove duplicate header rows from downloaded CSV files.

    GIVEN:
      data_dir (str) -- path to downloaded data
      overwrite (bool) -- whether or not to overwrite the old data files

    RETURN:
      None
    """
    issues_file, commits_file, pull_requests_file = getDataFilepaths(data_dir)

    dedup_issues_file = issues_file.split(".csv")[0] + "_dedup.csv"
    dedup_commits_file = commits_file.split(".csv")[0] + "_dedup.csv"
    dedup_pull_requests_file = pull_requests_file.split(".csv")[0] + "_dedup.csv"

    _deduplicate(issues_file, dedup_issues_file, ISSUES_HEADER)
    _deduplicate(commits_file, dedup_commits_file, COMMITS_HEADER)
    _deduplicate(pull_requests_file, dedup_pull_requests_file, PULL_REQUESTS_HEADER)

    if overwrite:
        overwriteFile(issues_file, dedup_issues_file)
        overwriteFile(commits_file, dedup_commits_file)
        overwriteFile(pull_requests_file, dedup_pull_requests_file)


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
