#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import requests
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.config import getAPIToken


#### GLOBALS #######################################################################################
HEADERS = {"Authorization": "token {}".format(getAPIToken())}
API_ENDPOINT = "https://api.github.com/graphql"
REPO_URL = "https://github.com/{}/{}/"

QUERY_RATE_LIMIT = """
{
    viewer { login }
    rateLimit {
        limit
        cost
        remaining
        resetAt
    }
}
"""
QUERY_COMMITS = """"""
QUERY_ALL = """"""
QUERY_PULL_REQUESTS_1 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        pullRequests(first:100, states:[OPEN,CLOSED,MERGED]) {
            totalCount
            edges {
                node {
                    number
                    title
                    author { login }
                    createdAt
                    url
                    bodyText
                    comments(first:100) {
                        totalCount
                        edges {
                            node {
                                id
                                author { login }
                                bodyText
                                createdAt
                                url
                            }
                        }
                        pageInfo {
                            startCursor
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
            pageInfo {
                startCursor
                endCursor
                hasNextPage
            }
        }
    }
}
"""
QUERY_PULL_REQUESTS_2 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        pullRequests(first:100, states:[OPEN,CLOSED,MERGED], after:"AFTER") {
            totalCount
            edges {
                node {
                    number
                    title
                    author { login }
                    createdAt
                    url
                    bodyText
                    comments(first:100) {
                        totalCount
                        edges {
                            node {
                                id
                                author { login }
                                bodyText
                                createdAt
                                url
                            }
                        }
                        pageInfo {
                            startCursor
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
            pageInfo {
                startCursor
                endCursor
                hasNextPage
            }
        }
    }
}
"""
QUERY_ISSUES_1 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        issues(first:100, states:[OPEN,CLOSED]) {
            totalCount
            edges {
                node {
                    id
                    number
                    title
                    author { login }
                    createdAt
                    url
                    bodyText
                    comments(first:100) {
                        totalCount
                        edges {
                            node {
                                id
                                author { login }
                                bodyText
                                createdAt
                                url
                            }
                        }
                        pageInfo {
                            startCursor
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
            pageInfo {
                startCursor
                endCursor
                hasNextPage
            }
        }
    }
}
"""
QUERY_ISSUES_2 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        issues(first:100, states:[OPEN,CLOSED], after:"AFTER") {
            totalCount
            edges {
                node {
                    id
                    number
                    title
                    author { login }
                    createdAt
                    url
                    bodyText
                    comments(first:100) {
                        totalCount
                        edges {
                            node {
                                id
                                author { login }
                                bodyText
                                createdAt
                                url
                            }
                        }
                        pageInfo {
                            startCursor
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
            pageInfo {
                startCursor
                endCursor
                hasNextPage
            }
        }
    }
}
"""
QUERY_COMMENTS_BY_ISSUE_NUMBER = """
query {
    repository(owner:"OWNER", name:"NAME") {
        issue(number: NUMBER) {
            comments(first:100, after:"AFTER") {
                edges {
                    node {
                        id
                        author { login }
                        bodyText
                        createdAt
                        url
                    }
                }
                pageInfo {
                    startCursor
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
"""
QUERY_COMMENTS_BY_PULL_REQUEST_NUMBER = """
query {
    repository(owner:"OWNER", name:"NAME") {
        pullRequest(number: NUMBER) {
            comments(first:100, after:"AFTER") {
                edges {
                    node {
                        id
                        author { login }
                        bodyText
                        createdAt
                        url
                    }
                }
                pageInfo {
                    startCursor
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
"""


#### FUNCTIONS #####################################################################################
def _runQuery(query):
    """
    Helper function. Run a query against GitHub's GraphQL API.

    GIVEN:
      query (str) -- query to run

    RETURN:
      ____ (dict) -- raw response from GitHub's GraphQL API
    """
    req = requests.post(API_ENDPOINT, json={"query": query}, headers=HEADERS)
    if req.status_code == 200:
        return req.json()
    else:
        # In theory, we should never get here
        print("Query failed. Status code: {}".format(req.status_code))
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


def _getAllIssues(repo_owner, repo_name):
    """
    Helper function fro runQuery(). Get all issues with relevant metadata and their comments.

    GIVEN:
      repo_owner (str) -- the owner of the repository; e.g. meyersbs
      repo_name (str) -- the name of the repository; e.g. SPLAT
    """
    all_issues = list()
    results = None

    # First pass to get pagination cursors
    res = _runQuery(
        QUERY_ISSUES_1.replace("OWNER", repo_owner)
        .replace("NAME", repo_name)
    )
    results = res
    all_issues.extend(res["data"]["repository"]["issues"]["edges"])
    end_cursor = res["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
    has_next_page = res["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

    # Subsequent passes
    while has_next_page:
        res = _runQuery(
            QUERY_ISSUES_2.replace("OWNER", repo_owner)
            .replace("NAME", repo_name)
            .replace("AFTER", end_cursor)
        )
        all_issues.extend(res["data"]["repository"]["issues"]["edges"])
        end_cursor = res["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
        has_next_page = res["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

    all_issues = _cleanUpAllIssues(results, all_issues)
    all_issues = _getAllCommentsByIssueNumber(repo_owner, repo_name, all_issues)
    return all_issues


def _getAllPullRequests(repo_owner, repo_name):
    """

    """
    all_pull_requests = list()
    results = None

    # First pass to get pagination cursors
    res = _runQuery(
        QUERY_PULL_REQUESTS_1.replace("OWNER", repo_owner)
        .replace("NAME", repo_name)
    )
    results = res
    print(res)
    all_pull_requests.extend(res["data"]["repository"]["pullRequests"]["edges"])
    end_cursor = res["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
    has_next_page = res["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]

    # Subsequent passes
    while has_next_page:
        res = _runQuery(
            QUERY_PULL_REQUESTS_2.replace("OWNER", repo_owner)
            .replace("NAME", repo_name)
            .replace("AFTER", end_cursor)
        )
        all_pull_requests.extend(res["data"]["repository"]["pullRequests"]["edges"])
        end_cursor = res["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
        has_next_page = res["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]

    all_pull_requests = _cleanUpAllPullRequests(results, all_pull_requests)
    all_pull_requests = _getAllCommentsByPullRequestNumber(repo_owner, repo_name, all_pull_requests)
    return all_pull_requests


def _getAllCommits(repo_owner, repo_name):
    sys.exit("Not yet implemented.")


def _getAllData(repo_owner, repo_name):
    sys.exit("Not yet implemented.")


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
        sys.exit("Something is terribly wrong.")

    return results

def getRateLimitInfo():
    """
    Query GitHub's GraphQL API for rate limit information.

    RETURN:
      ____ (dict) -- rate limit info from GitHub's GraphQL API
    """
    req = requests.post(API_ENDPOINT, json={"query": QUERY_RATE_LIMIT}, headers=HEADERS)
    if req.status_code == 200:
        return req.json()
    else:
        # In theory, we should never get here
        print("Failed to query rate limit. Status code: {}".format(req.status_code))
        return None


#### MAIN ##########################################################################################
