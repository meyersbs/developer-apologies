#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import operator
import os


#### PACKAGE IMPORTS ###############################################################################
from src.graphql import runQuery
from src.helpers import validateDataDir, parseRepoURL


#### GLOBALS #######################################################################################
ISSUES_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "ISSUE_NUMBER", "ISSUE_TITLE",
    "ISSUE_AUTHOR","ISSUE_CREATION_DATE", "ISSUE_URL", "ISSUE_TEXT", "COMMENT_CREATION_DATE",
    "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"]
COMMITS_HEADER = list()
PULL_REQUESTS_HEADER = list()


#### FUNCTIONS #####################################################################################
def _sortIssues(issues):
    """
    Helper function from _formatIssues(). Sort a list of issues by issue number and then by comment
    creation date.

    GIVEN:
      issues (list) -- nested list of issues and their comments

    RETURN:
      new_issues (list) -- the given 'issues' list, but sorted by issue number and comment creation
                           date
    """
    new_issues = sorted(issues, key=operator.itemgetter(3, 9))
    return new_issues


def _formatIssues(issues, repo_url, repo_name, repo_owner):
    """
    Helper function for _formatCSV(). Transform issues (and their comments) from JSON to CSV.

    GIVEN:
      issues (list) -- list of dictionaries representing issues
      repo_url (str) -- the URL for the repository
      repo_name (str) -- the name of the repository
      repo_owner (str) -- the owner of the repository

    RETURN:
      issues_list (list) -- flat list of issues and their comments
    """
    issues_list = list()
    # For each issue
    for issue in issues:
        issue_num = issue["node"]["number"]
        issue_title = issue["node"]["title"]
        issue_author = issue["node"]["author"]["login"]
        issue_created = issue["node"]["createdAt"]
        issue_url = issue["node"]["url"]
        issue_text = issue["node"]["bodyText"]

        # If there are comments
        if issue["node"]["comments"]["totalCount"] != 0:
            # For each comments
            for comment in issue["node"]["comments"]["edges"]:
                comment_author = comment["node"]["author"]["login"]
                comment_created = comment["node"]["createdAt"]
                comment_url = comment["node"]["url"]
                comment_text = comment["node"]["bodyText"]

                issues_list.append([
                    repo_url,
                    repo_name,
                    repo_owner,
                    issue_num,
                    issue_created,
                    issue_author,
                    issue_title,
                    issue_url,
                    issue_text,
                    comment_created,
                    comment_author,
                    comment_url,
                    comment_text
                ])
        # If there are no comments
        else:
            issues_list.append([
                repo_url,
                repo_name,
                repo_owner,
                issue_num,
                issue_created,
                issue_author,
                issue_title,
                issue_url,
                issue_text,
                "",
                "",
                "",
                ""
            ])

    issues_list = _sortIssues(issues_list)
    return issues_list


def _formatCSV(data, repo_url, data_types):
    """
    Helper function for download(). Take raw JSON data from GitHub's GraphQL API and convert it to
    CSV.

    GIVEN:
      data (JSON) -- raw JSON from GitHub's GraphQL API
      repo_url (str) -- the URL for the repository
      data_types (str) -- the type of data contained in 'data'; one of ['issues', 'comments',
                          'pull_requests', 'all']

    RETURN:
      issues (list) -- flat list of issues and their comments
      pull_requests (list) -- flat list of pull requests and their comments
      commits (list) -- flat list of commits and their comments
    """
    repo_url = repo_url
    repo_name = data["data"]["repository"]["name"]
    repo_owner = data["data"]["repository"]["owner"]["login"]

    issues = list()
    commits = list()
    pull_requests = list()
    if data_types == "issues":
        issues = _formatIssues(data["data"]["repository"]["issues"]["edges"], repo_url, repo_name, repo_owner)
    elif data_types == "commits":
        pass
    elif data_types == "pull_requests":
        pass
    elif data_types == "all":
        pass

    print(repo_url)
    print(repo_name)
    print(repo_owner)
    print(issues)
    print(commits)
    print(pull_requests)

    return issues, pull_requests, commits


def _writeCSV(issues, pull_requests, commits, data_dir):
    """
    Helper function for download(). Write CSV data to disk.

    GIVEN:
      issues (list) -- issues to write to disk
      pull_requests (list) -- pull requests to write to disk
      commits (list) -- commits to write to disk
      data_dir (str) -- directory to write data to

    RETURN:
      None
    """
    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")

    # Write issues
    if len(issues) > 0:
        print("Writing issues to: {}".format(issues_file))
        with open(issues_file, "a") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"")
            csv_writer.writerow(ISSUES_HEADER)
            for issue in issues:
                csv_writer.writerow(issue)

    # Write commits
    if len(commits) > 0:
        print("Writing commits to: {}".format(commits_file))
        with open(commits_file, "a") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"")
            csv_writer.writerow(COMMITS_HEADER)
            for commit in commits:
                csv_writer.writerow(commit)

    # Write pull requests
    if len(pull_requests) > 0:
        print("Writing pull requests to: {}".format(pull_requests_file))
        with open(pull_requests_file, "a") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar="\"")
            csv_writer.writerow(PULL_REQUESTS_HEADER)
            for pull_request in pull_requests:
                csv_writer.writerow(pull_request)


def download(repo_file, data_dir, data_types):
    """
    Download data from GitHub repositories and save to disk.

    GIVEN:
      repo_file (str) -- the absolute path to a file containing repository URLs
      data_dir (str) -- the absolute path to a directory to store data in
      data_types (str) -- the type of data to download for each repo; one of ["issues", "commits",
                          "pull_requests", "all"]
    """

    # Make sure the necessary subdirectories exist
    validateDataDir(data_dir)

    with open(repo_file, "r") as f:
        # For each repository
        for line in f.readlines():
            # Get the the name of the repo and its owner
            repo_url = line.strip("\n")
            repo_owner, repo_name = parseRepoURL(repo_url)

            # Run a GraphQL query
            results = runQuery(repo_owner, repo_name, data_types)
            # Convert results to CSV
            issues, pull_requests, comments = _formatCSV(results, repo_url, data_types)
            # Write data to disk
            _writeCSV(issues, pull_requests, comments, data_dir)


#### MAIN ##########################################################################################
