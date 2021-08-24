#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import os
import shutil
import unittest
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################
from src.config import getAPIToken, EmptyAPITokenError
from src.delete import delete
from src.graphql import _runQuery, _cleanUpAllIssues, _cleanUpAllPullRequests, _cleanUpAllCommits, \
    _getAllCommentsByIssueNumber, _getAllCommentsByPullRequestNumber, _getAllCommentsByCommitOID, \
    _getAllIssues, _getAllPullRequests, _getAllCommits, _getAllData, runQuery, getRateLimitInfo
from src.helpers import canonicalize, doesPathExist, validateDataDir, parseRepoURL, \
    InvalidGitHubURLError


#### GLOBALS #######################################################################################
CWD = os.path.dirname(os.path.realpath(__file__))


#### TEST CASES ####################################################################################
class TestHelpers(unittest.TestCase):
    """
    Test cases for functions in src.helpers.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test_canonicalize(self):
        """
        Test src.helpers:canonicalize().
        """
        # Case 1 -- simple relative path
        input_path = "data/"
        expected = os.path.join(CWD, "data")
        actual = canonicalize(input_path)
        self.assertEqual(expected, actual)

        # Case 2 -- complex relative path
        input_path = "data/../data/"
        expected = os.path.join(CWD, "data")
        actual = canonicalize(input_path)
        self.assertEqual(expected, actual)


    def test_doesPathExist(self):
        """
        Test src.helpers:doesPathExist().
        """
        # Case 1 -- relative path that doesn't exist
        input_path = "data/apples/"
        actual = doesPathExist(input_path)
        self.assertFalse(actual)

        # Case 2 -- absolute path that doesn't exist
        input_path = "data/apples/"
        actual = doesPathExist(canonicalize(input_path))
        self.assertFalse(actual)

        # Case 3 -- relative path that does exist
        input_path = "data/__init__.py"
        actual = doesPathExist(input_path)
        self.assertTrue(actual)

        # Case 4 -- absolute path that does exist
        input_path = "data/__init__.py"
        actual = doesPathExist(canonicalize(input_path))
        self.assertTrue(actual)


    def test_validateDataDir(self):
        """
        Test src.helpers:validateDataDir().
        """
        expected = [
            (os.path.join(CWD, "test_data/"), ["commits", "issues", "pull_requests"], []),
            (os.path.join(CWD, "test_data/commits"), [], ["__init__.py"]),
            (os.path.join(CWD, "test_data/issues"), [], ["__init__.py"]),
            (os.path.join(CWD, "test_data/pull_requests"), [], ["__init__.py"])
        ]

        # Case 1 -- empty data_dir
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)       
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 2 -- data_dir with just issues dir
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "issues/"))
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 3 -- data_dir with just issues dir containing __init__.py
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "issues/"))
        Path(os.path.join(data_dir, "issues/__init__.py")).touch()
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 4 -- data_dir with just commits dir
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "commits/"))
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 5 -- data_dir with just commits dir containing __init__.py
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "commits/"))
        Path(os.path.join(data_dir, "commits/__init__.py")).touch()
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 6 -- data_dir with just pull_requests dir
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "pull_requests/"))
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 7 -- data_dir with just pull_requests dir containing __init__.py
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "pull_requests/"))
        Path(os.path.join(data_dir, "pull_requests/__init__.py")).touch()
        validateDataDir(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test


    def test_parseRepoURL(self):
        """
        Test src.helpers:parseRepoURL().
        """
        # Case 1 -- GitHub URL
        input_url = "https://github.com/meyersbs/developer-apologies/"
        expected = ("meyersbs", "developer-apologies")
        actual = parseRepoURL(input_url)
        self.assertTupleEqual(expected, actual)

        # Case 2 -- Non-GitHub URL
        input_url = "http://www.se.rit.edu/~swen-331/"
        self.assertRaises(InvalidGitHubURLError, parseRepoURL, input_url)


class TestConfig(unittest.TestCase):
    """
    Test cases for functions in src.config.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test_getAPIToken(self):
        """
        Test src.config:getAPIToken().
        """
        # Case 1 -- API token exists
        token_path = canonicalize("test_files/test_github_api_token.txt")
        expected = "abc_defG32ef6abd9mP4Qdmr5TY901sN01gF27eU"
        actual = getAPIToken(token_path)
        self.assertEqual(expected, actual)

        # Case 2 -- blank API token
        token_path = canonicalize("test_files/test_github_api_token_empty.txt")
        self.assertRaises(EmptyAPITokenError, getAPIToken, token_path)


class TestDelete(unittest.TestCase):
    """
    Test cases for function in src.delete.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test_delete(self):
        """
        Test src.delete:delete().
        """
        expected = [
            (os.path.join(CWD, "test_data/"), ["commits", "issues", "pull_requests"], []),
            (os.path.join(CWD, "test_data/commits"), [], ["__init__.py"]),
            (os.path.join(CWD, "test_data/issues"), [], ["__init__.py"]),
            (os.path.join(CWD, "test_data/pull_requests"), [], ["__init__.py"])
        ]

        # Case 1 -- all files exist
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 2 -- everything but issues.csv exists
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 3 -- everything but commits.csv exists
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test

        # Case 4 -- everything but pull_requests.csv exists
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        shutil.rmtree(data_dir) # Clean up before next test


class TestGraphQL(unittest.TestCase):
    """
    Test cases for function in src.graphql.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test__runQuery(self):
        """
        Test src.graphql:_runQuery().
        """
        # Case 1 -- dynamic, valid query
        input_query = """
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
        actual = _runQuery(input_query)
        self.assertTrue("data" in actual.keys())
        self.assertTrue("viewer" in actual["data"].keys())
        self.assertTrue("login" in actual["data"]["viewer"].keys())
        self.assertTrue("rateLimit" in actual["data"].keys())
        self.assertTrue("limit" in actual["data"]["rateLimit"].keys())
        self.assertTrue("cost" in actual["data"]["rateLimit"].keys())
        self.assertTrue("remaining" in actual["data"]["rateLimit"].keys())
        self.assertTrue("resetAt" in actual["data"]["rateLimit"].keys())

        # Case 2 -- static, valid query
        input_query = """
        query {
            repository(owner:"meyersbs", name:"tvdb-dl-nfo") {
                issue(number:1) {
                    author { login }
                    title
                    assignees { totalCount }
                    createdAt
                    bodyText
                    state
                    url
                }
            }
        }
        """
        expected = {
            "data": {
                "repository": {
                    "issue": {
                        "author": {
                            "login": "meyersbs"
                        },
                        "title": "Ampersands in Metadata",
                        "assignees": {
                            "totalCount": 1
                        },
                        "createdAt": "2019-05-11T20:58:59Z",
                        "bodyText": "If a show has an ampersand (&) in its name or description, the"
                                    " following error will occur:\n    PHP Warning:  SimpleXMLEleme"
                                    "nt::addChild(): unterminated entity reference\n\nThe tvshow.nf"
                                    "o file is still generated, but the field containing the ampers"
                                    "and will be empty.",
                        "state": "CLOSED",
                        "url": "https://github.com/meyersbs/tvdb-dl-nfo/issues/1"
                    }
                }
            }
        }
        actual = _runQuery(input_query)
        self.assertDictEqual(expected, actual)

        # Case 3 -- invalid query, status code != 200
        # This can't really be tested. GitHub's GraphQL API responds with status code = 200 even
        # when the query was malformed. It responds with a JSON dict with the key "errors", which
        # we can test.

        # Case 4 -- invalid query, returning errors
        input_query = "query {}"
        expected = None
        actual = _runQuery(input_query)
        self.assertEqual(expected, actual)


    def test_runQuery(self):
        """
        Test src.graphql:runQuery().
        """
        # Case 1 -- data_types="issues"
        input_repo_owner = "meyersbs"
        input_repo_name = "tvdb-dl-nfo"
        input_data_types = "issues"
        expected = {
            "data": {
                "repository": {
                    "name": "tvdb-dl-nfo",
                    "owner": {
                        "login": "meyersbs"
                    },
                    "issues": {
                        "totalCount": 1,
                        "edges": [
                            {
                                "node": {
                                    "id": "MDU6SXNzdWU0NDMwMzU3MTU=",
                                    "number": 1,
                                    "title": "Ampersands in Metadata",
                                    "author": {
                                        "login": "meyersbs"
                                    },
                                    "createdAt": "2019-05-11T20:58:59Z",
                                    "url": "https://github.com/meyersbs/tvdb-dl-nfo/issues/1",
                                    "bodyText": "If a show has an ampersand (&) in its name or desc"
                                                "ription, the following error will occur:\n    PHP "
                                                "Warning:  SimpleXMLElement::addChild(): unterminat"
                                                "ed entity reference\n\nThe tvshow.nfo file is stil"
                                                "l generated, but the field containing the ampersan"
                                                "d will be empty.",
                                    "comments": {
                                        "totalCount": 0,
                                        "edges": [],
                                        "pageInfo": {
                                            "startCursor": None,
                                            "endCursor": None,
                                            "hasNextPage": False
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        self.assertDictEqual(expected, actual)

        # Case 2 -- data_types="issues", with over 100 comments
        input_repo_owner = "meyersbs"
        input_repo_name = "developer-apologies" # Yes, that's this repo!
        input_data_types = "issues"
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        self.assertEqual(2, actual["data"]["repository"]["issues"]["totalCount"])
        issues = actual["data"]["repository"]["issues"]["edges"]
        for issue in issues:
            if issue["node"]["number"] == 1:
                self.assertEqual("Test Issue with Over 100 Comments", issue["node"]["title"])
                self.assertEqual("meyersbs", issue["node"]["author"]["login"])
                self.assertEqual(101, len(issue["node"]["comments"]["edges"]))
                self.assertEqual("2021-08-19T21:25:39Z", issue["node"]["createdAt"])
            elif issue["node"]["number"] == 2:
                self.assertEqual("Test Issue", issue["node"]["title"])
                self.assertEqual("meyersbs", issue["node"]["author"]["login"])
                self.assertEqual(2, len(issue["node"]["comments"]["edges"]))
                self.assertEqual("2021-08-19T21:46:16Z", issue["node"]["createdAt"])
                comments = issue["node"]["comments"]["edges"]
                for comment in comments:
                    if comment["node"]["id"] == "IC_kwDOFyefKs41x4vo":
                        self.assertEqual("Dummy comment.", comment["node"]["bodyText"])
                        self.assertEqual("meyersbs", comment["node"]["author"]["login"])
                        self.assertEqual("2021-08-19T21:46:23Z", comment["node"]["createdAt"])
                    elif comment["node"]["id"] == "IC_kwDOFyefKs41zfVm":
                        self.assertEqual(
                            "Sorry, but I figured I'd add a data point. Sorrynotsorry.",
                            comment["node"]["bodyText"]
                        )
                        self.assertEqual("andymeneely", comment["node"]["author"]["login"])
                        self.assertEqual("2021-08-20T13:23:06Z", comment["node"]["createdAt"])

        # Case 3 -- data_types="pull_requests"
        input_repo_owner = "meyersbs"
        input_repo_name = "developer-apologies" # Yes, that's this repo!
        input_data_types = "pull_requests"
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        pull_requests = actual["data"]["repository"]["pullRequests"]["edges"]
        self.assertEqual(1, len(pull_requests))
        self.assertEqual("Update README.md", pull_requests[0]["node"]["title"])
        self.assertEqual("andymeneely", pull_requests[0]["node"]["author"]["login"])
        self.assertEqual("", pull_requests[0]["node"]["bodyText"])
        self.assertEqual("2021-08-23T14:33:22Z", pull_requests[0]["node"]["createdAt"])
        comments = pull_requests[0]["node"]["comments"]["edges"]
        self.assertEqual(101, len(comments))
        for comment in comments:
            self.assertEqual("meyersbs", comment["node"]["author"]["login"])

        # Case 4 -- data_types="commits"
        input_repo_owner = "meyersbs"
        input_repo_name = "tvdb-dl-nfo"
        input_data_types = "commits"
        expected = None
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        commits = actual["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        self.assertEqual(12, len(commits))
        for commit in commits:
            if commit["node"]["oid"] == "5b2009b8db3299cdb810b20caaaea88adb5ebe08":
                self.assertEqual(1, commit["node"]["additions"])
                self.assertEqual(1, commit["node"]["deletions"])
                self.assertEqual("2019-11-27T19:09:42Z", commit["node"]["committedDate"])
                self.assertEqual("Update README.md", commit["node"]["messageHeadline"])
                self.assertEqual("", commit["node"]["messageBody"])
                self.assertEqual(1, commit["node"]["comments"]["totalCount"])
                self.assertEqual(
                    "Dummy comment.",
                    commit["node"]["comments"]["edges"][0]["node"]["bodyText"]
                )
                self.assertEqual(
                    "2021-08-24T12:52:30Z",
                    commit["node"]["comments"]["edges"][0]["node"]["createdAt"]
                )
                break

        # Case 5 -- data_types="all"
        input_repo_owner = "meyersbs"
        input_repo_name = "tvdb-dl-nfo"
        input_data_types = "all"
        expected = None
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        self.assertEqual(expected, actual)

        # Case 6 -- invalid data_types
        input_repo_owner = "meyersbs"
        input_repo_name = "tvdb-dl-nfo"
        input_data_types = "apples"
        expected = None
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        self.assertEqual(expected, actual)


    def test_getRateLimitInfo(self):
        """
        Test src.graphql:getRateLimitInfo().
        """
        actual = getRateLimitInfo()
        self.assertTrue("data" in actual.keys())
        self.assertTrue("viewer" in actual["data"].keys())
        self.assertTrue("login" in actual["data"]["viewer"].keys())
        self.assertTrue("rateLimit" in actual["data"].keys())
        self.assertTrue("limit" in actual["data"]["rateLimit"].keys())
        self.assertTrue("cost" in actual["data"]["rateLimit"].keys())
        self.assertTrue("remaining" in actual["data"]["rateLimit"].keys())
        self.assertTrue("resetAt" in actual["data"]["rateLimit"].keys())


#### MAIN ##########################################################################################
if __name__ == "__main__":
    unittest.main(warnings="ignore")
