#!/usr/bin/env python3

#### PYTHON IMPORTS ################################################################################
import json
import os
import shutil
import sys
from pathlib import Path
from statistics import median


#### CONFIG ########################################################################################


#### GLOBALS #######################################################################################
APOLOGY_LEMMAS = [
    "admit", "afraid", "apology", "apologise", "apologize", "blame", "excuse", "fault", "forgive",
    "forgot", "mistake", "mistaken", "oops", "pardon", "regret", "sorry"
]


#### FUNCTIONS #####################################################################################
def canonicalize(top_dir):
    """
    Canonicalize filepath.

    GIVEN:
      top_dir (str) -- relative filepath

    RETURN:
      _ (str) -- absolute filepath for top_dir
    """
    return os.path.realpath(top_dir)


def _getFilepaths(data_dir):
    for dirpath, _, filepaths in os.walk(data_dir):
        for f in filepaths:
            yield os.path.abspath(os.path.join(dirpath, f))


def _getJsonFromFile(filepath):
    json_dict = dict()
    with open(filepath, "r") as f:
        json_dict = json.load(f)

    return json_dict


def aggregateStats(filepaths):    
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
            "admit": 0,
            "afraid": 0,
            "apology": 0,
            "apologise": 0,
            "apologize": 0,
            "blame": 0,
            "excuse": 0,
            "fault": 0,
            "forgive": 0,
            "forgot": 0,
            "mistake": 0,
            "mistaken": 0,
            "oops": 0,
            "pardon": 0,
            "regret": 0,
            "sorry": 0
        }
    }

    for filepath in filepaths:
        print(filepath)
        # Get stats
        print("\tGetting dictionary...")
        json_dict = _getJsonFromFile(filepath)
        
        # Aggregate stats
        print("\tAggregating stats...")
        stats_dict["apologies"]["total"] += json_dict["apologies"]["total"]
        stats_dict["apologies"]["wc_total"] += json_dict["apologies"]["wc_total"]
        stats_dict["apologies"]["wc_individual"].extend(json_dict["apologies"]["wc_individual"])
        stats_dict["apologies"]["lc_total"] += json_dict["apologies"]["lc_total"]
        stats_dict["apologies"]["lc_individual"].extend(json_dict["apologies"]["lc_individual"])

        stats_dict["non-apologies"]["total"] += json_dict["non-apologies"]["total"]
        stats_dict["non-apologies"]["wc_total"] += json_dict["non-apologies"]["wc_total"]
        stats_dict["non-apologies"]["wc_individual"].extend(json_dict["non-apologies"]["wc_individual"])

        for apology in APOLOGY_LEMMAS:
            stats_dict["lemmas"][apology] += json_dict["lemmas"][apology]

        del json_dict

    # Compute MEAN, MEDIAN, MIN, MAX
    print("Computing metrics...")
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
    print("      ADMIT: {}".format(stats_dict["lemmas"]["admit"]))
    print("     AFRAID: {}".format(stats_dict["lemmas"]["afraid"]))
    print("    APOLOGY: {}".format(stats_dict["lemmas"]["apology"]))
    print("  APOLOGISE: {}".format(stats_dict["lemmas"]["apologise"]))
    print("  APOLOGIZE: {}".format(stats_dict["lemmas"]["apologize"]))
    print("      BLAME: {}".format(stats_dict["lemmas"]["blame"]))
    print("     EXCUSE: {}".format(stats_dict["lemmas"]["excuse"]))
    print("      FAULT: {}".format(stats_dict["lemmas"]["fault"]))
    print("    FORGIVE: {}".format(stats_dict["lemmas"]["forgive"]))
    print("     FORGOT: {}".format(stats_dict["lemmas"]["forgot"]))
    print("    MISTAKE: {}".format(stats_dict["lemmas"]["mistake"]))
    print("   MISTAKEN: {}".format(stats_dict["lemmas"]["mistaken"]))
    print("       OOPS: {}".format(stats_dict["lemmas"]["oops"]))
    print("     PARDON: {}".format(stats_dict["lemmas"]["pardon"]))
    print("     REGRET: {}".format(stats_dict["lemmas"]["regret"]))
    print("      SORRY: {}".format(stats_dict["lemmas"]["sorry"]))


#### MAIN ##########################################################################################
if __name__ == "__main__":
    data_dir = canonicalize(sys.argv[1])
    filepaths = list(_getFilepaths(data_dir))
    #print(filepaths)
    aggregateStats(filepaths)
