#!/usr/bin/env python3

#### IMPORTS #######################################################################################
import requests
import sys


#### GLOBALS #######################################################################################
GITHUB_API_TOKEN = None
with open("github_api_token.txt", "r") as f:
    GITHUB_API_TOKEN = f.read().replace("\n", "")

REQUEST_HEADERS = {"Authorization": "token {}".format(GITHUB_API_TOKEN)}

GITHUB_ISSUES_URL = "https://api.github.com/repos/{}/issues?{}"

PROJECTS_MAP = {
    "d3": "d3/d3",
    "cptc-badge-2021": "JRWR/cptc-badge-2021",
    "mitre-attack-mapper": "meyersbs/mitre-attack-mapper",
}


#### FUNCTIONS #####################################################################################
def _getRawIssuesJSON(url):
    """
    Download the raw JSON data from the GitHub REST API for the given URL.

    GIVEN:
      url (str):            the REST API endpoint to hit

    RETURN:
      issues_json (dict):   dictionary containing raw JSON data
    """
    print("Running: _getRawIssuesJSON()")
    results = requests.get(url, headers=REQUEST_HEADERS)
    issues_json = results.json()

    # The following 3 lines were adapted from: https://stackoverflow.com/a/50731243/3546278
    while "next" in results.links.keys():
        results = requests.get(results.links["next"]["url"], headers=REQUEST_HEADERS)
        issues_json.extend(results.json())

    print("  Collected {} Issues!".format(len(issues_json)))
    return issues_json


def _getCommentCount(issues):
    """
    Get the total number of comments across all issues.

    GIVEN:
      issues (dict):        collection of issues; output of _getIssuesWithComments()

    RETURN:
      comment_count (int):  total number of comments
    """
    print("Running: _getCommentCount()")
    comment_count = 0
    for k, v in issues.items():
        comment_count += len(v["comments"])

    return comment_count


def _getIssueComments(comments_api):
    """
    Collect the comments from the given GitHub REST API endpoint.

    GIVEN:
      comments_api (str):   the REST API endpoint to hit

    RETURN:
      comments (list):      list of dictionaries, each representing a comment with metadata
    """
    print("Running: _getIssueComments()")
    comments = list()
    comments_json = requests.get(comments_api, headers=REQUEST_HEADERS).json()
    for comment in comments_json:
        comment_item = {
            "web_url": comment["html_url"],
            "timestamp": comment["created_at"],
            "author": comment["user"]["login"],
            "author_association": comment["author_association"],
            "text": comment["body"].lower()
        }
        comments.append(comment_item)

    print("  Collected {} Issue Comments!".format(len(comments)))
    return comments


def _getIssuesWithComments(issues_json):
    """
    Given a collection of issues (raw JSON), clean them up and collect their comments.

    GIVEN:
      issues_json (dict):   collection of unprocessed issues

    RETURN:
      issues (dict):        collection of processed issues with comments
    """
    print("Running: _getIssues()")
    issues = dict()
    for issue in issues_json:
        comments_url = issue["comments_url"]
        comments = _getIssueComments(comments_url)

        issue_body = None
        if issue["body"] is not None:
            issue_body = issue["body"].lower()

        issue_item = {
            "web_url": issue["html_url"],
            "title": issue["title"],
            "author": issue["user"]["login"],
            "text": issue_body,
            "comments": comments,
        }
        issues.update({issue["number"]: issue_item})

    return issues


def downloadIssuesForProject(project_id):
    """
    Get all of the issues and their comments for the given project ID.

    GIVEN:
      project_id (str): project ID to get issues/comments for; must match a key in PROJECTS_MAP

    RETURN:
      issues (dict):    dictionary containing issues, their comments, and all selected metadata
    """
    print("Running: downloadIssuesForProject()")
    querystring = "state=all&per_page=100&page=1"
    project = PROJECTS_MAP[project_id]
    url = GITHUB_ISSUES_URL.format(project, querystring)
    issues_json = _getRawIssuesJSON(url)
    issues = _getIssuesWithComments(issues_json)

    print("Total Issues: {}".format(len(issues.keys())))
    print("Total Comments: {}".format(_getCommentCount(issues)))
    for k, v in issues.items():
        print(v)
        break
    return issues


#### MAIN ##########################################################################################
if __name__ == "__main__":
    args = sys.argv[1:]
    print(args)
    issues = downloadIssuesForProject(args[0])
    
