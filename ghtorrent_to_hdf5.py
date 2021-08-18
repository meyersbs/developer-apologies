#!/usr/bin/env python3

#### IMPORTS #######################################################################################
import argparse


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################


#### MAIN ##########################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scripts to facilitate access to our HDF5 file and analysis of its data."
    )

    command_parsers = parser.add_parser(
        help="Available commands."
    )

    #### LOAD ISSUES COMMAND
    load_issues_parser = command_parsers.add_parser(
        "load_issues", help="Load issues and their comments into the HDF5 file."
    )

    load_issues_parser.add_argument(
        "repo_name", type=str, help="The name of the repository to extract issues (and their"
        " comments) from. For example, for https://github.com/torvalds/linux, the repo_name would "
        "be 'linux'."
    )
    load_issues_parser.add_argument(
        "repo_owner", type=str, help="The owner of the repository to extract issues (and their "
        "comments) from. For example, for https://github.com/torvalds/linux, the repo_owner would "
        "be 'torvalds'."
    )

    #### LOAD COMMITS COMMAND
    load_commits_parser = command_parsers.add_parser(
        "load_commits", help="Load commits and their comments into the HDF5 file."
    )

    load_commits_parser.add_argument(
        "commit_comments_path", type=str, help="The file path for the CSV file to extract commit "
        "comments from. For example: '/path/to/file/commit_comments.csv'. Relative paths will be "
        "canonicalized. This should be a file obtained from GHTorrent's MySQL dump."
    )
    load_commits_parser.add_argument(
        "commits_path", type=str, help="The file path for the CSV file to extract commit hashes "
        "from. For example: '/path/to/file/commits.csv'. Relative paths will be canonicalized. "
        "This should be a file obtained from GHTorrent's MySQL dump."
    )

    #### LOAD PULL REQUESTS COMMAND
    load_pull_requests_parser = command_parsers.add_parser(
        "load_pull_requests", help="Load pull_requests and their comments into the HDF5 file."
    )

    load_pull_requests_parser.add_argument(
        "pull_request_comments_path", type=str, help="The file path for the CSV file to extract "
        "pull request comments from. For example: '/path/to/file/pull_request_comments.csv'. "
        "Relative paths will be canonicalized. This should be a file obtained from GHTorrent's "
        "MySQL dump."
    )
    load_pull_requests_parser.add_argument(
        "pull_requests_path", type=str, help="The file path for the CSV file to extract pull request"
        "info from. For example: '/path/to/file/pull_requests.csv'. Relative paths will be "
        "canonicalized. This should be a file obtained from GHTorrent's MySQL dump."
    )

