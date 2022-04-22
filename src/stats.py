#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import os
import random
import sys
csv.field_size_limit(sys.maxsize)
from statistics import median


#### PACKAGE IMPORTS ###############################################################################
from src.apologies import APOLOGY_LEMMAS
from src.helpers import doesPathExist, getDataFilepaths, getSubDirNames, fixNullBytes


#### GLOBALS #######################################################################################
CO_COLUMN_DICT = {"COMMENT_TEXT": 14, "COMMENT_TEXT_LEMMATIZED": 15, "NUM_APOLOGY_LEMMAS": 16}
IS_COLUMN_DICT = {"COMMENT_TEXT": 12, "COMMENT_TEXT_LEMMATIZED": 13, "NUM_APOLOGY_LEMMAS": 14}
PR_COLUMN_DICT = {"COMMENT_TEXT": 12, "COMMENT_TEXT_LEMMATIZED": 13, "NUM_APOLOGY_LEMMAS": 14}
SOURCE_COLUMN_MAP = {"IS": IS_COLUMN_DICT, "CO": CO_COLUMN_DICT, "PR": PR_COLUMN_DICT}


#### FUNCTIONS #####################################################################################
def _getPopulationFilepaths(data_dir):
    """
    For the given 'data_dir', get a list of paths matching the given 'source'.

    GIVEN:
      data_dir (str) -- path to a directory containing data

    RETURN:
      pop_paths (list) -- list of filepaths matching target data source
    """
    # Get subdirs
    sub_dirs = getSubDirNames(data_dir)

    # Get all paths 
    co_pop_paths = list()
    is_pop_paths = list()
    pr_pop_paths = list()
    for sub_dir in sub_dirs:
        is_file, co_file, pr_file = getDataFilepaths(os.path.join(data_dir, sub_dir))

        if os.path.exists(co_file): # pragma: no cover
            co_pop_paths.append(co_file)

        if os.path.exists(is_file): # pragma: no cover
            is_pop_paths.append(is_file)

        if os.path.exists(pr_file): # pragma: no cover
            pr_pop_paths.append(pr_file)

    
    pop_paths = list()
    pop_paths.extend(co_pop_paths)
    pop_paths.extend(is_pop_paths)
    pop_paths.extend(pr_pop_paths)

    # Return filepaths
    return pop_paths


def _deduplicateHeaders(rows, header):
    """
    Remove duplicate header rows, if they exist.
    """
    try:
        while True:
            rows.remove(header)
    except ValueError:
        pass

    return rows


def _getSourceFromFilepath(filepath):
    """
    Parse filepath to determine data source.
    """
    src = None
    if "commits.csv" in filepath:
        src = "CO"
    elif "issues.csv" in filepath:
        src = "IS"
    elif "pull_requests.csv" in filepath:
        src = "PR"

    return src


def _getTargetColumns(rows, filepath):
    """
    Get a subset of columns from the raw data.
    """
    target_rows = list()
    for row in rows:
        src = _getSourceFromFilepath(filepath)
        if row[SOURCE_COLUMN_MAP[src]["COMMENT_TEXT"]] not in ["", "COMMENT_TEXT"]:
            new_row = [
                len(row[SOURCE_COLUMN_MAP[src]["COMMENT_TEXT"]].split(" ")),       # Word count
                row[SOURCE_COLUMN_MAP[src]["COMMENT_TEXT_LEMMATIZED"]].split(" "), # COMMENT_TEXT_LEMMATIZED
                row[SOURCE_COLUMN_MAP[src]["NUM_APOLOGY_LEMMAS"]]                  # NUM_APOLOGY_LEMMAS
            ]
            target_rows.append(new_row)

    return target_rows


def _getPopulationData(data_dir):
    """
    Get the data that we care about.
    """
    # Get filepaths to sample from
    pop_filepaths = _getPopulationFilepaths(data_dir)

    # Get data
    pop_data = list()
    for filepath in pop_filepaths:
        with open(filepath, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            # Get rows
            rows = list()
            header = next(csv_reader) # Skip header row
            for entry in csv_reader:
                rows.append(entry)

            # Deduplicate header rows
            rows = _deduplicateHeaders(rows, header)

            # Get a subset of the columns that we care about
            rows = _getTargetColumns(rows, filepath)

            # Add rows to population data
            pop_data.extend(rows)

            # Memory management
            del rows

    # Return population data
    return pop_data


def stats(data_dir, verbose=True):
    """
    Compute statistics for apology comments.

    GIVEN:
      data_dir (str) -- path to preprocessed and classified data
      verbose (bool) -- flag to enable/disable printing

    RETURN:
      stats_dict (dict) -- dictionary of statistics for unit tests
    """
    stats_dict = {
        "apologies": {
            "total": 0,
            "wc_total": 0,
            "wc_individual": list(),
            "wc_mean": -1,
            "wc_median": -1,
            "wc_min": -1,
            "wc_max": -1,
            "lc_total": 0,
            "lc_individual": list(),
            "lc_mean": -1,
            "lc_median": -1,
            "lc_min": -1,
            "lc_max": -1
        },
        "non-apologies": {
            "total": 0,
            "wc_total": 0,
            "wc_individual": list(),
            "wc_mean": -1,
            "wc_median": -1,
            "wc_min": -1,
            "wc_max": -1
        },
        "lemmas": {
            "apology": 0,
            "apologise": 0,
            "apologize": 0,
            "blame": 0,
            "excuse": 0,
            "fault": 0,
            "forgive": 0,
            "mistake": 0,
            "mistaken": 0,
            "oops": 0,
            "pardon": 0,
            "regret": 0,
            "sorry": 0
        }
    }

    # Get the data
    pop_data = _getPopulationData(data_dir)

    cnt = 1
    for row in pop_data:
        if verbose: # pragma: no cover
            print("{} / {}".format(cnt, len(pop_data)))
            cnt += 1
        # Determine if current row is an apology
        is_apology = True if int(row[2]) > 0 else False
        
        # Determine word count
        word_count = row[0]

        if is_apology:
            # Count the total frequency of apology lemmas
            lc = 0
            for lemma in row[1]:
                for apology in APOLOGY_LEMMAS:
                    if apology == lemma:
                        stats_dict["lemmas"][apology] += 1
                        stats_dict["apologies"]["lc_total"] += 1
                        lc += 1
            stats_dict["apologies"]["lc_individual"].append(lc)

        if is_apology:
            stats_dict["apologies"]["total"] += 1
            stats_dict["apologies"]["wc_total"] += word_count
            stats_dict["apologies"]["wc_individual"].append(word_count)
        else:
            stats_dict["non-apologies"]["total"] += 1
            stats_dict["non-apologies"]["wc_total"] += word_count
            stats_dict["non-apologies"]["wc_individual"].append(word_count)

    # Memory management
    del pop_data

    # Compute MEAN, MEDIAN, MIN, MAX
    stats_dict["apologies"]["wc_mean"] = stats_dict["apologies"]["wc_total"] / stats_dict["apologies"]["total"]
    stats_dict["apologies"]["wc_median"] = median(stats_dict["apologies"]["wc_individual"])
    stats_dict["apologies"]["wc_min"] = min(stats_dict["apologies"]["wc_individual"])
    stats_dict["apologies"]["wc_max"] = max(stats_dict["apologies"]["wc_individual"])
    stats_dict["apologies"]["lc_mean"] = stats_dict["apologies"]["lc_total"] / stats_dict["apologies"]["total"]
    stats_dict["apologies"]["lc_median"] = median(stats_dict["apologies"]["lc_individual"])
    stats_dict["apologies"]["lc_min"] = min(stats_dict["apologies"]["lc_individual"])
    stats_dict["apologies"]["lc_max"] = max(stats_dict["apologies"]["lc_individual"])
    stats_dict["non-apologies"]["wc_mean"] = stats_dict["non-apologies"]["wc_total"] / stats_dict["non-apologies"]["total"]
    stats_dict["non-apologies"]["wc_median"] = median(stats_dict["non-apologies"]["wc_individual"])
    stats_dict["non-apologies"]["wc_min"] = min(stats_dict["non-apologies"]["wc_individual"])
    stats_dict["non-apologies"]["wc_max"] = max(stats_dict["non-apologies"]["wc_individual"])

    # Display data
    print("APOLOGIES:")
    print("      TOTAL: {}".format(stats_dict["apologies"]["total"]))
    print("    MEAN WC: {}".format(stats_dict["apologies"]["wc_mean"]))
    print("  MEDIAN WC: {}".format(stats_dict["apologies"]["wc_median"]))
    print("     MIN WC: {}".format(stats_dict["apologies"]["wc_min"]))
    print("     MAX WC: {}".format(stats_dict["apologies"]["wc_max"]))

    print("    MEAN LC: {}".format(stats_dict["apologies"]["lc_mean"]))
    print("  MEDIAN LC: {}".format(stats_dict["apologies"]["lc_median"]))
    print("     MIN LC: {}".format(stats_dict["apologies"]["lc_min"]))
    print("     MAX LC: {}".format(stats_dict["apologies"]["lc_max"]))

    print("NON-APOLOGIES:")
    print("      TOTAL: {}".format(stats_dict["non-apologies"]["total"]))
    print("    MEAN WC: {}".format(stats_dict["non-apologies"]["wc_mean"]))
    print("  MEDIAN WC: {}".format(stats_dict["non-apologies"]["wc_median"]))
    print("     MIN WC: {}".format(stats_dict["non-apologies"]["wc_min"]))
    print("     MAX WC: {}".format(stats_dict["non-apologies"]["wc_max"]))

    print("LEMMAS:")
    print("    APOLOGY: {}".format(stats_dict["lemmas"]["apology"]))
    print("  APOLOGISE: {}".format(stats_dict["lemmas"]["apologise"]))
    print("  APOLOGIZE: {}".format(stats_dict["lemmas"]["apologize"]))
    print("      BLAME: {}".format(stats_dict["lemmas"]["blame"]))
    print("     EXCUSE: {}".format(stats_dict["lemmas"]["excuse"]))
    print("      FAULT: {}".format(stats_dict["lemmas"]["fault"]))
    print("    FORGIVE: {}".format(stats_dict["lemmas"]["forgive"]))
    print("    MISTAKE: {}".format(stats_dict["lemmas"]["mistake"]))
    print("   MISTAKEN: {}".format(stats_dict["lemmas"]["mistaken"]))
    print("       OOPS: {}".format(stats_dict["lemmas"]["oops"]))
    print("     PARDON: {}".format(stats_dict["lemmas"]["pardon"]))
    print("     REGRET: {}".format(stats_dict["lemmas"]["regret"]))
    print("      SORRY: {}".format(stats_dict["lemmas"]["sorry"]))

    # Return data (for unit tests)
    return stats_dict


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
