#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import argparse
import sys


#### PROJECT IMPORTS ###############################################################################
from src.delete import delete
from src.download import download
from src.graphql import getRateLimitInfo
from src.helpers import canonicalize, doesPathExist


#### GLOBALS #######################################################################################
ASSERT_NOT_EXIST = "The provided {}={} does not exist."


#### FUNCTIONS #####################################################################################
def downloadCommand(args):
    """
    Parse arguments for 'download' command and pass them to src.download:download().
    """
    # Canonicalize filepaths
    args.repo_file = canonicalize(args.repo_file)
    args.data_dir = canonicalize(args.data_dir)

    # Check assertions
    assert doesPathExist(args.repo_file), ASSERT_NOT_EXIST.format("repo_file", args.repo_file)
    assert doesPathExist(args.data_dir), ASSERT_NOT_EXIST.format("data_dir", args.data_dir)

    if args.data_types in ["all"]:
        sys.exit("Data type '{}' for downloadCommand() not yet implemented.".format(
            args.data_types))

    # Pass arguments to src.download:download()
    download(args.repo_file, args.data_dir, args.data_types)


def loadCommand(args):
    sys.exit("Not yet implemented.")


def deleteCommand(args):
    """
    Delete the CSV data stored in the given data_dir.
    """
    # Canonicalize filepaths
    args.data_dir = canonicalize(args.data_dir)

    # Verify with user
    input("Are you sure you want to delete the data in {}? Press CTRL+C now to abort, or any key to "
          "continue with deletion.".format(args.data_dir))

    # Pass arguments to src.delete:delete()
    delete(args.data_dir)


def infoDataCommand(args):
    sys.exit("Not yet implemented.")


def infoHDF5Command(args):
    sys.exit("Not yet implemented.")


def infoRateLimitCommand(args):
    """
    Query GitHub's GraphQL API for rate limit information.
    """
    print(getRateLimitInfo())


#### MAIN ##########################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scripts to facilitate downloading data from GitHub, loading it into an HDF5 "
        "file, and analyzing the data."
    )

    command_parsers = parser.add_subparsers(
        help="Available commands."
    )

    #### DOWNLOAD COMMAND
    download_parser = command_parsers.add_parser(
        "download", help="Download data from GitHub repositories using the GraphQL API."
    )

    download_parser.add_argument(
        "repo_file", type=str, help="The path for a file containing GitHub repository URLs to "
        "download data from. This file should contain a single repo URL per line. Relative paths "
        "will be canonicalized."
    )
    download_parser.add_argument(
        "data_types", type=str, choices=["issues", "pull_requests", "commits", "all"],
        help="The type of data to download from the given repositories. All of the relevant "
        "metadata, including comments will be downloaded for whichever option is given."
    )
    download_parser.add_argument(
        "data_dir", type=str, help="The path for a directory to save the downloaded data to. "
        "Relative paths will be canonicalized. Downloaded data will be in the form of a CSV file "
        "and placed in a subdirectory, e.g. data_dir/issues/."
    )
    download_parser.set_defaults(func=downloadCommand)

    #### LOAD COMMAND
    load_parser = command_parsers.add_parser(
        "load", help="Load downloaded data into an HDF5 file."
    )

    load_parser.add_argument(
        "hdf5_file", type=str, help="The path/name of the HDF5 file to create and load with data. "
        "Relative paths will be canonicalized."
    )
    load_parser.add_argument(
        "data_dir", type=str, help="The path to a directory where data is downloaded and ready to "
        "be loaded. Relative paths will be canonicalized."
    )
    load_parser.set_defaults(func=loadCommand)

    #### DELETE COMMAND
    delete_parser = command_parsers.add_parser(
        "delete", help="Delete local CSV data from disk. This command cannot be used to delete "
        "the HDF5 file."
    )
    
    delete_parser.add_argument(
        "data_dir", type=str, help="The path for a directory containing downloaded data. Relative "
        "paths will be canonicalized."
    )
    delete_parser.set_defaults(func=deleteCommand)

    #### INFO_DATA COMMAND
    info_data_parser = command_parsers.add_parser(
        "info_data", help="Display info about the downloaded data."
    )

    info_data_parser.add_argument(
        "data_dir", type=str, help="The path for a directory containing downloaded data. Relative "
        "paths will be canonicalized."
    )
    info_data_parser.set_defaults(func=infoDataCommand)

    #### INFO_HDF5 COMMAND
    info_hdf5_parser = command_parsers.add_parser(
        "info_hdf5", help="Display info about the data loaded into HDF5."
    )

    info_hdf5_parser.add_argument(
        "hdf5_file", type=str, help="The path/name of an HDF5 file. Relative paths will be "
        "canonicalized."
    )
    info_hdf5_parser.set_defaults(func=infoHDF5Command)

    #### INFO_RATE_LIMIT COMMAND
    info_rate_limit_parser = command_parsers.add_parser(
        "info_rate_limit", help="Display rate limiting info from GitHub's GraphQL API."
    )

    info_rate_limit_parser.set_defaults(func=infoRateLimitCommand)

    #### PARSER ARGUMENTS
    args = parser.parse_args()
    #print(args)
    args.func(args)


