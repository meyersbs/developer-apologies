#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import os
import random
import sys
csv.field_size_limit(sys.maxsize)


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import doesPathExist, getDataFilepaths, getSubDirNames, fixNullBytes


#### GLOBALS #######################################################################################
ABRIDGED_HEADER = ["SOURCE", "COMMENT_URL", "COMMENT_TEXT", "NUM_APOLOGY_LEMMAS", "IS_APOLOGY"]
CO_COLUMN_DICT = {"COMMENT_URL": 13, "COMMENT_TEXT": 14, "NUM_APOLOGY_LEMMAS": 16, "IS_APOLOGY": 17}
IS_COLUMN_DICT = {"COMMENT_URL": 11, "COMMENT_TEXT": 12, "NUM_APOLOGY_LEMMAS": 14, "IS_APOLOGY": 15}
PR_COLUMN_DICT = {"COMMENT_URL": 11, "COMMENT_TEXT": 12, "NUM_APOLOGY_LEMMAS": 14, "IS_APOLOGY": 15}
SOURCE_COLUMN_MAP = {"IS": IS_COLUMN_DICT, "CO": CO_COLUMN_DICT, "PR": PR_COLUMN_DICT}

#### FUNCTIONS #####################################################################################
def _getPopulationFilepaths(data_dir, source):
    """

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

    # Filter out sources we don't want to sample from
    pop_paths = list()
    if source == "ALL":
        pop_paths.extend(co_pop_paths)
        pop_paths.extend(is_pop_paths)
        pop_paths.extend(pr_pop_paths)
    elif source == "CO":
        pop_paths = co_pop_paths
    elif source == "IS":
        pop_paths = is_pop_paths
    # Unit tests are confused, this is definitely being tested
    elif source == "PR": # pragma: no cover
        pop_paths = pr_pop_paths
    else: # pragma: no cover
        pass

    # Return filepaths to sample from
    return pop_paths


def _deduplicateHeaders(rows, header):
    """

    """
    try:
        while True:
            rows.remove(header)
    except ValueError:
        pass

    return rows


def _getSourceFromFilepath(filepath):
    """

    """
    src = None
    if "commits.csv" in filepath:
        src = "CO"
    elif "issues.csv" in filepath:
        src = "IS"
    elif "pull_requests.csv" in filepath:
        src = "PR"

    return src


def _getTargetColumns(rows, source, filepath):
    """

    """
    target_rows = list()
    if source != "ALL":
        for row in rows:
            new_row = [
                source,                                               # SOURCE
                row[SOURCE_COLUMN_MAP[source]["COMMENT_URL"]],        # COMMENT_URL
                row[SOURCE_COLUMN_MAP[source]["COMMENT_TEXT"]],       # COMMENT_TEXT
                row[SOURCE_COLUMN_MAP[source]["NUM_APOLOGY_LEMMAS"]], # NUM_APOLOGY_LEMMAS
                row[SOURCE_COLUMN_MAP[source]["IS_APOLOGY"]]          # IS_APOLOGY
            ]
            target_rows.append(new_row)
    else:
        for row in rows:
            src = _getSourceFromFilepath(filepath)
            new_row = [
                src,                                               # SOURCE
                row[SOURCE_COLUMN_MAP[src]["COMMENT_URL"]],        # COMMENT_URL
                row[SOURCE_COLUMN_MAP[src]["COMMENT_TEXT"]],       # COMMENT_TEXT
                row[SOURCE_COLUMN_MAP[src]["NUM_APOLOGY_LEMMAS"]], # NUM_APOLOGY_LEMMAS
                row[SOURCE_COLUMN_MAP[src]["IS_APOLOGY"]]          # IS_APOLOGY
            ]
            target_rows.append(new_row)

    return target_rows


def _filterNonApologies(pop_data):
    """

    """
    filtered_pop_data = list()
    for row in pop_data:
        if row[4] == "1":
            filtered_pop_data.append(row)
        else: # pragma: no cover
            pass

    return filtered_pop_data


def _getPopulationData(data_dir, apologies_only, source):
    """

    """
    # Get filepaths to sample from
    pop_filepaths = _getPopulationFilepaths(data_dir, source)

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
            rows = _getTargetColumns(rows, source, filepath)

            # Add rows to population data
            pop_data.extend(rows)

            # Memory management
            del rows

    # Return population data
    return pop_data
    

def randomSample(data_dir, sample_size, apologies_only, source, output_file, export_all):
    """
    Collect a random sample of developer comments and save to disk.

    GIVEN:
      data_dir (str) -- path to processed and classified data
      sample_size (int) -- size of random sample to collect
      apologies_only (bool) -- whether or not to collect samples from all comments (False) or only
                               from comments classified as apologies
      source (str) -- source of comments to sample from; IS=issues, CO=commits, PR=pull requests,
                      ALL=all sources
      output_file (str) -- path to save random sample to, or directory to save multiple samples to
      export_all (bool) -- whether to export multiple samples of 'sample_size' or just one

    RETURN:
      None
    """
    # Get data to sample from
    pop_data = _getPopulationData(data_dir, apologies_only, source)

    # Filter out non-apologies, if necessary
    if apologies_only:
        pop_data = _filterNonApologies(pop_data)

    # Randomly select 'sample_size' elements from 'pop_data'
    sample_data = random.sample(pop_data, sample_size)

    if not export_all:
        # Randomly select 'sample_size' elements from 'pop_data'
        sample_data = random.sample(pop_data, sample_size)

        # Save samples to disk
        with open(output_file, "w") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

            # Write header row
            csv_writer.writerow(ABRIDGED_HEADER)

            for row in sample_data:
                csv_writer.writerow(row)
    else:
        # Shuffle data
        sample_data = random.sample(pop_data, len(pop_data))

        # Create chunks of sample_size
        chunks = list()
        for i in range(0, len(sample_data), sample_size):
            chunks.append(sample_data[i:i+sample_size])

        # Export chunks to disk
        for i in range(0, len(chunks)):
            export_file = os.path.join(output_file, "random_sample_{}_{}.csv".format(sample_size, i))
            with open(export_file, "w") as f:
                csv_writer = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

                # Write header row
                csv_writer.writerow(ABRIDGED_HEADER)

                curr_chunk = chunks[i]
                for row in curr_chunk:
                    csv_writer.writerow(row)


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
