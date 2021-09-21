#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import requests
import sys
import time


#### PACKAGE IMPORTS ###############################################################################
from src.config import getAPIToken, EmptyAPITokenError
from src.queries import *


#### GLOBALS #######################################################################################
try: # pragma: no cover
    HEADERS = {"Authorization": "token {}".format(getAPIToken())}
except EmptyAPITokenError: # pragma: no cover
    sys.exit()

API_ENDPOINT = "https://api.github.com/graphql"
REPO_URL = "https://github.com/{}/{}/"


#### FUNCTIONS #####################################################################################
def _runQuery(query):
    """
    Helper function. Run a query against GitHub's GraphQL API.

    GIVEN:
      query (str) -- query to run

    RETURN:
      ____ (dict) -- raw response from GitHub's GraphQL API
    """
    try:
        req = requests.post(API_ENDPOINT, json={"query": query}, headers=HEADERS)
    except requests.exceptions.ChunkedEncodingError as e:
        print(e)
        req = None
    
    if req is None:
        print("Query failed: {}".format(query))
        return _runQuery(query)
    elif "documentation_url" in req.json().keys(): # pragma: no cover
        print(req.json())
        print("Hit secondary rate limit. Waiting 60 seconds...")
        time.sleep(60) # Wait 60 seconds
        return _runQuery(query)
    elif "errors" not in req.json().keys():
        #if req.status_code == 200:
        return req.json()
    else:
        # In theory, we should never get here
        print("Query failed: {}".format(query))
        return None


def _cleanUpAllIssues(results, all_issues):
    """
    Helper function for _getAllIssues(). Clean up issues and strip out cursor info.

    GIVEN:
      results (dict) -- initial query response with metadata
      all_issues (list) -- nested list of issues with comments and metadata

    RETURN:
      results (dict) -- cleaned up results
    """
    results["data"]["repository"]["issues"]["edges"] = all_issues
    results["data"]["repository"]["issues"].pop("pageInfo")
    return results


def _cleanUpAllPullRequests(results, all_pull_requests):
    """
    Helper function for _getAllPullRequests(). Clean up pull requests and strip out cursor info.

    GIVEN:
      results (dict) -- initial query response with metadata
      all_pull_requests (list) -- nested list of pull_requests with comments and metadata

    RETURN:
      results (dict) -- cleaned up results
    """
    results["data"]["repository"]["pullRequests"]["edges"] = all_pull_requests
    results["data"]["repository"]["pullRequests"].pop("pageInfo")
    return results


def _cleanUpAllCommits(results, all_commits):
    """
    Helper function for _getAllCommitss(). Clean up commits and strip out cursor info.

    GIVEN:
      results (dict) -- initial query response with metadata
      all_commits (list) -- nested list of commits with comments and metadata

    RETURN:
      results (dict) -- cleaned up results
    """
    results["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"] = all_commits
    results["data"]["repository"]["defaultBranchRef"]["target"]["history"].pop("pageInfo")
    return results


def _cleanUpSearchResults(search_results, total):
    """
    Helper function for _searchRepos(). Clean up search results.

    GIVEN:
      search_results (list) -- list of search results
      total (int) -- total number of search results to return

    RETURN:
      results (list) -- cleaned up search results
    """
    results = list()
    for res in search_results:
        element = [
            res["node"]["url"],
            res["node"]["stargazerCount"]
        ]
        if res["node"]["primaryLanguage"] is None:
            element.append("None")
        else:
            element.append(res["node"]["primaryLanguage"]["name"])

        results.append(element)

    if total == 0:
        return results
    else:
        return results[:total]


def _getAllCommentsByIssueNumber(repo_owner, repo_name, all_issues):
    """
    Helper function for _getAllIssues(). For issues where the first pass couldn't get all of the
    comments, get the missing comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT
      all_issues (dict) -- intermediate data from _getAllIssues()
    """
    # For each issue
    for issue in all_issues["data"]["repository"]["issues"]["edges"]:
        # While the number of comments is less than it should be
        issue_copy = issue
        while issue_copy["node"]["comments"]["pageInfo"]["hasNextPage"]:
            # Get the next page of comments
            end_cursor = issue["node"]["comments"]["pageInfo"]["endCursor"]
            res = _runQuery(
                QUERY_COMMENTS_BY_ISSUE_NUMBER.replace("OWNER", repo_owner)
                .replace("NAME", repo_name)
                .replace("NUMBER", str(issue["node"]["number"]))
                .replace("AFTER", end_cursor)
            )
            # Update our comments
            issue_copy["node"]["comments"]["edges"].extend(
                res["data"]["repository"]["issue"]["comments"]["edges"])
            # Update the pageInfo
            issue_copy["node"]["comments"]["pageInfo"] = \
                res["data"]["repository"]["issue"]["comments"]["pageInfo"]

        # Update the issue
        issue = issue_copy

    return all_issues


def _getAllCommentsByPullRequestNumber(repo_owner, repo_name, all_pull_requests):
    """
    Helper function for _getAllPullRequests(). For pull requests where the first pass couldn't get
    all of the comments, get the missing comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT
      all_pull_requests (dict) -- intermediate data from _getAllPullRequests()
    """
    # For each pull request
    for pull_request in all_pull_requests["data"]["repository"]["pullRequests"]["edges"]:
        # While the number of comments is less than it should be
        pull_request_copy = pull_request
        while pull_request_copy["node"]["comments"]["pageInfo"]["hasNextPage"]:
            # Get the next page of comments
            end_cursor = pull_request["node"]["comments"]["pageInfo"]["endCursor"]
            res = _runQuery(
                QUERY_COMMENTS_BY_PULL_REQUEST_NUMBER.replace("OWNER", repo_owner)
                .replace("NAME", repo_name)
                .replace("NUMBER", str(pull_request["node"]["number"]))
                .replace("AFTER", end_cursor)
            )
            # Update our comments
            pull_request_copy["node"]["comments"]["edges"].extend(
                res["data"]["repository"]["pullRequest"]["comments"]["edges"])
            # Update the pageInfo
            pull_request_copy["node"]["comments"]["pageInfo"] = \
                res["data"]["repository"]["pullRequest"]["comments"]["pageInfo"]

        # Update the issue
        pull_request = pull_request_copy

    return all_pull_requests


def _getAllCommentsByCommitOID(repo_owner, repo_name, all_commits):
    """
    Helper function for _getAllCommits(). For commits where the first pass couldn't get all of the
    comments, get the missing comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT
      all_commits (dict) -- intermediate data from _getAllCommits()
    """
    # For each commit
    for commit in all_commits["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]:
        # While the number of comments is less than it should be
        commit_copy = commit
        while commit_copy["node"]["comments"]["pageInfo"]["hasNextPage"]:
            # Get the next page of comments
            end_cursor = commit["node"]["comments"]["pageInfo"]["endCursor"]
            res = _runQuery(
                QUERY_COMMENTS_BY_COMMIT_OID.replace("OWNER", repo_owner)
                .replace("NAME", repo_name)
                .replace("OID", commit["node"]["oid"])
                .replace("AFTER", end_cursor)
            )
            # Update our comments
            commit_copy["node"]["comments"]["edges"].extend(
                res["data"]["repository"]["object"]["comments"]["edges"])
            # Update pageInfo
            commit_copy["node"]["comments"]["pageInfo"] = \
                res["data"]["repository"]["object"]["comments"]["pageInfo"]

        # Update the commit
        commit = commit_copy

    return all_commits


def _getAllIssues(repo_owner, repo_name):
    """
    Helper function for runQuery(). Get all issues with relevant metadata and their comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT

    RETURN:
      all_issues (JSON) -- JSON representation of all issues with their comments and metadata
    """
    print("\tGetting issues...")
    all_issues = list()
    results = None

    # First pass to get pagination cursors
    res = _runQuery(
        QUERY_ISSUES_1.replace("OWNER", repo_owner)
        .replace("NAME", repo_name)
    )
    results = res
    try:
        all_issues.extend(res["data"]["repository"]["issues"]["edges"])
        end_cursor = res["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
        has_next_page = res["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]
    except ValueError as e:
        print(e)
        print("Failed to get issues for repo_owner={}, repo_name={}".format(repo_owner, repo_name))
        return list()

    # Subsequent passes
    while has_next_page: # pragma: no cover
        res = _runQuery(
            QUERY_ISSUES_2.replace("OWNER", repo_owner)
            .replace("NAME", repo_name)
            .replace("AFTER", end_cursor)
        )
        # If the query failed, then has_next_page doesn't get updated, so it will simply try the same query again
        if res is not None:
            all_issues.extend(res["data"]["repository"]["issues"]["edges"])
            end_cursor = res["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
            has_next_page = res["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

    all_issues = _cleanUpAllIssues(results, all_issues)
    all_issues = _getAllCommentsByIssueNumber(repo_owner, repo_name, all_issues)
    return all_issues


def _getAllPullRequests(repo_owner, repo_name):
    """
    Helper function for runQuery(). Get all pull requests with relevant metadata and their comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT

    RETURN:
      all_pull_requests (JSON) -- JSON representation of all pull requests with their comments and
                                  metadata
    """
    print("\tGetting pull requests...")
    all_pull_requests = list()
    results = None

    # First pass to get pagination cursors
    res = _runQuery(
        QUERY_PULL_REQUESTS_1.replace("OWNER", repo_owner)
        .replace("NAME", repo_name)
    )
    results = res
    try:
    	all_pull_requests.extend(res["data"]["repository"]["pullRequests"]["edges"])
    	end_cursor = res["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
    	has_next_page = res["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]
    except ValueError as e:
        print(e)
        print("Failed to get pull requests for repo_owner={}, repo_name={}".format(repo_owner, repo_name))
        return list()

    # Subsequent passes
    while has_next_page: # pragma: no cover
        res = _runQuery(
            QUERY_PULL_REQUESTS_2.replace("OWNER", repo_owner)
            .replace("NAME", repo_name)
            .replace("AFTER", end_cursor)
        )
        # If the query failed, then has_next_page doesn't get updated, so it will simply try the same query again
        if res is not None:
            all_pull_requests.extend(res["data"]["repository"]["pullRequests"]["edges"])
            end_cursor = res["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
            has_next_page = res["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]

    all_pull_requests = _cleanUpAllPullRequests(results, all_pull_requests)
    all_pull_requests = _getAllCommentsByPullRequestNumber(repo_owner, repo_name, all_pull_requests)
    return all_pull_requests


def _getAllCommits(repo_owner, repo_name):
    """
    Helper function for runQuery(). Get all commits with relevant metadata.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT

    RETURN:
      all_commits (JSON) -- JSON representation of all commits with their comments and metadata
    """
    print("\tGetting commits...")
    all_commits = list()
    results = None

    # First pass to get pagination cursors
    res = _runQuery(
        QUERY_COMMITS_1.replace("OWNER", repo_owner)
        .replace("NAME", repo_name)
    )
    results = res
    try:
    	all_commits.extend(res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"])
    	end_cursor = res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["endCursor"]
    	has_next_page = res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["hasNextPage"]
    except ValueError as e:
        print(e)
        print("Failed to get commits for repo_owner={}, repo_name={}".format(repo_owner, repo_name))
        return lisT()

    # Subsequent passes
    while has_next_page: # pragma: no cover
        res = _runQuery(
            QUERY_COMMITS_2.replace("OWNER", repo_owner)
            .replace("NAME", repo_name)
            .replace("AFTER", end_cursor)
        )
        # If the query failed, then has_next_page doesn't get updated, so it will simply try the same query again
        if res is not None:
            all_commits.extend(res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"])
            end_cursor = res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["endCursor"]
            has_next_page = res["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["hasNextPage"]

    all_commits = _cleanUpAllCommits(results, all_commits)
    all_commits = _getAllCommentsByCommitOID(repo_owner, repo_name, all_commits)
    return all_commits


def _getAllData(repo_owner, repo_name):
    """
    Helper function for runQuer(). Get all issues, commits, and pull requests with relevant metadata
    and comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT

    RETURN:
      all_issues (JSON) -- JSON representation of all issues with their comments and metadata
      all_commits (JSON) -- JSON representation of all commits with their comments and metadata
      all_pull_requests (JSON) -- JSON representation of all pull requests with their comments and
                                  metadata
    """
    all_issues = _getAllIssues(repo_owner, repo_name)
    all_commits = _getAllCommits(repo_owner, repo_name)
    all_pull_requests = _getAllPullRequests(repo_owner, repo_name)

    return [all_issues, all_commits, all_pull_requests]


def runQuery(repo_owner, repo_name, data_types):
    """
    Run a query against GitHub's GraphQL API endpoint.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT
      data_types (str) -- the type of data to download; one of ["issues", "pull_requests",
                          "commits", "all"]

    RETURN:
      results (dict) -- response from GitHub's GraphQL API
    """
    results = None
    if data_types == "issues":
        results = _getAllIssues(repo_owner, repo_name)
    elif data_types == "pull_requests":
        results = _getAllPullRequests(repo_owner, repo_name)
    elif data_types == "commits":
        results =_getAllCommits(repo_owner, repo_name)
    elif data_types == "all":
        results = _getAllData(repo_owner, repo_name)
    else:
        # Something is very wrong if we end up here
        return None

    return results


def getRateLimitInfo():
    """
    Query GitHub's GraphQL API for rate limit information.

    RETURN:
      ____ (dict) -- rate limit info from GitHub's GraphQL API
    """
    req = requests.post(API_ENDPOINT, json={"query": QUERY_RATE_LIMIT}, headers=HEADERS)
    if "errors" not in req.json().keys():
    #if req.status_code == 200:
        return req.json()
    else: # pragma: no cover
        # In theory, we should never get here
        print("Failed to query rate limit: {}".format(req.json()))
        return None


def searchRepos(filters, total):
    """
    Query GitHub's GraphQL API for repositories matching the given filters.

    GIVEN:
      filters (str) -- filters for search results
      total (int) -- total number of results to return

    RETURN:
      search_results (list) -- search results
    """
    search_results = list()
    # First pass to get pagination cursors
    res = _runQuery(
        SEARCH_REPOS_1.replace("FILTERS", filters)
    )
    search_results.extend(res["data"]["search"]["edges"])
    end_cursor = res["data"]["search"]["pageInfo"]["endCursor"]
    has_next_page = res["data"]["search"]["pageInfo"]["hasNextPage"]

    # Subsequent passes
    while has_next_page and len(search_results) < total: # pragma: no cover
        res = _runQuery(
            SEARCH_REPOS_2.replace("FILTERS", filters)
            .replace("AFTER", end_cursor)
        )
        search_results.extend(res["data"]["search"]["edges"])
        end_cursor = res["data"]["search"]["pageInfo"]["endCursor"]
        has_next_page = res["data"]["search"]["pageInfo"]["hasNextPage"]

    search_results = _cleanUpSearchResults(search_results, total)
    return search_results


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
