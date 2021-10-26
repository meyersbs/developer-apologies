#!/usr/bin/env python3

#### PYTHON IMPORTS ################################################################################
import os
import shutil
import sys


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def canonicalize(top_dir):
    """
    Canonicalize filepath.
    """
    return os.path.realpath(top_dir)


def getSubDirNames(top_dir):
    """
    Get the names of subdirectories, one level deep.
    """
    return [d[1] for d in os.walk(top_dir)][0]


def moveFiles(top_dir, dir_names):
    """
    Rename files and move them to the top_dir.
    """
    for sub_dir in dir_names:
        co_file = os.path.join(top_dir, sub_dir, "commits/commits.csv")
        is_file = os.path.join(top_dir, sub_dir, "issues/issues.csv")
        pr_file = os.path.join(top_dir, sub_dir, "pull_requests/pull_requests.csv")

        if os.path.exists(co_file):
            new_co_file = os.path.join(top_dir, "co_{}.csv".format(sub_dir))
            os.rename(co_file, new_co_file)
            print("\tMoved {} --> {}".format(co_file, new_co_file))

        if os.path.exists(is_file):
            new_is_file = os.path.join(top_dir, "is_{}.csv".format(sub_dir))
            os.rename(is_file, new_is_file)
            print("\tMoved {} --> {}".format(is_file, new_is_file))

        if os.path.exists(pr_file):
            new_pr_file = os.path.join(top_dir, "pr_{}.csv".format(sub_dir))
            os.rename(pr_file, new_pr_file)
            print("\tMoved {} --> {}".format(pr_file, new_pr_file))


def deleteEmptyDirs(top_dir, dir_names):
    """
    Delete empty directories.
    """
    for sub_dir in dir_names:
        temp_path = os.path.join(top_dir, sub_dir)
        shutil.rmtree(temp_path)
        print("\tDeleted {}".format(temp_path))


#### MAIN ##########################################################################################
if __name__ == "__main__":
    top_dir = canonicalize(sys.argv[1])
    dir_names = getSubDirNames(top_dir)
    print("Moving files...")
    moveFiles(top_dir, dir_names)
    print("Deleting directories...")
    deleteEmptyDirs(top_dir, dir_names)
