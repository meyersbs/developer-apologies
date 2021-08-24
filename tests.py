#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import os
import shutil
import unittest
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################
from src.config import getAPIToken, EmptyAPITokenError
from src.delete import delete
from src.download import download
from src.graphql import _runQuery, runQuery, getRateLimitInfo
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


    def tearDown(self):
        """
        Necessary cleanup for these test cases.
        """
        try:
            data_dir = os.path.join(CWD, "test_data/") 
            shutil.rmtree(data_dir)
        except FileNotFoundError:
            pass # We don't want the directory to exist, so this is fine


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


    def tearDown(self):
        """
        Necessary cleanup for these test cases.
        """
        try:
            data_dir = os.path.join(CWD, "test_data/") 
            shutil.rmtree(data_dir)
        except FileNotFoundError:
            pass # We don't want the directory to exist, so this is fine


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


class TestDownload(unittest.TestCase):
    """
    Test cases for function in src.download.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def tearDown(self):
        """
        Necessary cleanup for these test cases.
        """
        try:
            data_dir = os.path.join(CWD, "test_data/") 
            shutil.rmtree(data_dir)
        except FileNotFoundError:
            pass # We don't want the directory to exist, so this is fine


    def test_download(self):
        """
        Test src.download:download().
        """
        # Case 1 -- data_types="issues"
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_2.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "issues"
        expected = [
            [
                "REPO_URL", "REPO_NAME", "REPO_OWNER", "ISSUE_NUMBER", "ISSUE_CREATION_DATE",
                "ISSUE_AUTHOR", "ISSUE_TITLE", "ISSUE_URL", "ISSUE_TEXT", "COMMENT_CREATION_DATE",
                "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs", "1",
                "2019-05-11T20:58:59Z", "meyersbs", "Ampersands in Metadata",
                "https://github.com/meyersbs/tvdb-dl-nfo/issues/1",
                "If a show has an ampersand (&) in its name or description, the following error wil"
                "l occur:\n    PHP Warning:  SimpleXMLElement::addChild(): unterminated entity refe"
                "rence\n\nThe tvshow.nfo file is still generated, but the field containing the ampe"
                "rsand will be empty.", "", "", "", ""
            ]
        ]
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "issues/issues.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected, actual)
        shutil.rmtree(input_data_dir)

        # Case 2 -- data_types="issues", with over 100 comments
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "issues"
        expected = [
            ["REPO_URL", "REPO_NAME", "REPO_OWNER", "ISSUE_NUMBER", "ISSUE_CREATION_DATE",
             "ISSUE_AUTHOR", "ISSUE_TITLE", "ISSUE_URL", "ISSUE_TEXT", "COMMENT_CREATION_DATE",
             "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258838", "1"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:44Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258857", "2"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:46Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258876", "3"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:48Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258891", "4"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:55Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258949", "5"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:25:58Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258971", "6"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:01Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902258993", "7"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:03Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259007", "8"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259028", "9"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259059", "10"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:10Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259089", "11"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:12Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259116", "12"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259138", "13"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:18Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259168", "14"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:21Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259190", "15"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:25Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259222", "16"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:27Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259247", "17"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:29Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259270", "18"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:32Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259299", "19"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:35Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259322", "20"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:38Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259347", "21"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:40Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259361", "22"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259385", "23"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259408", "24"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:48Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259438", "25"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:51Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259461", "26"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:54Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259491", "27"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:56Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259522", "28"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:26:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259550", "29"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:02Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259578", "30"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259598", "31"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259617", "32"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:10Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259644", "33"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259685", "34"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:17Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259716", "35"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:20Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259733", "36"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:23Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259771", "37"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259798", "38"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:39Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902259921", "39"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:52Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260036", "40"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:27:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260103", "41"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260148", "42"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:10Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260197", "43"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260257", "44"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:18Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260286", "45"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:22Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260313", "46"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:25Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260335", "47"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:28Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260366", "48"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:32Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260395", "49"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:35Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260436", "50"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:38Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260470", "51"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260497", "52"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260518", "53"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260557", "54"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:52Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260586", "55"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:55Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260621", "56"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:28:58Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260655", "57"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:01Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260683", "58"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260717", "59"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260749", "60"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:11Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260784", "61"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260813", "62"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:20Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260860", "63"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:23Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260890", "64"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260917", "65"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:29Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260943", "66"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:32Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902260974", "67"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:35Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261010", "68"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:38Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261045", "69"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261080", "70"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261114", "71"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261143", "72"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:53Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261177", "73"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:56Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261203", "74"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:29:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261232", "75"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:03Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261256", "76"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261277", "77"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:09Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261311", "78"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:12Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261347", "79"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:16Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261359", "80"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:18Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261384", "81"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:22Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261422", "82"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261458", "83"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:30Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261493", "84"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:33Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261523", "85"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:37Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261556", "86"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:41Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261587", "87"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:43Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261605", "88"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:46Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261636", "89"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261661", "90"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:53Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261685", "91"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:56Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261709", "92"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:30:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261744", "93"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:03Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261789", "94"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261819", "95"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261838", "96"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:11Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261864", "97"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:14Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261888", "98"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:16Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261906", "99"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:20Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261939", "100"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "1",
             "2021-08-19T21:25:39Z", "meyersbs", "Test Issue with Over 100 Comments",
             "https://github.com/meyersbs/developer-apologies/issues/1", "Test Issue with Over 100 Comments.",
             "2021-08-19T21:31:23Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/issues/1#issuecomment-902261971", "101"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "2",
             "2021-08-19T21:46:16Z", "meyersbs", "Test Issue",
             "https://github.com/meyersbs/developer-apologies/issues/2", "Test Issue", "2021-08-19T21:46:23Z",
             "meyersbs", "https://github.com/meyersbs/developer-apologies/issues/2#issuecomment-902269928",
             "Dummy comment."],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "2",
             "2021-08-19T21:46:16Z", "meyersbs", "Test Issue",
             "https://github.com/meyersbs/developer-apologies/issues/2", "Test Issue", "2021-08-20T13:23:06Z",
             "andymeneely", "https://github.com/meyersbs/developer-apologies/issues/2#issuecomment-902690150",
             "Sorry, but I figured I'd add a data point. Sorrynotsorry."]
        ]
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "issues/issues.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected, actual)
        shutil.rmtree(input_data_dir)

        # Case 3 -- data_types="pull_requests"
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "pull_requests"
        expected = [
            ["REPO_URL", "REPO_NAME", "REPO_OWNER", "PULL_REQUEST_NUMBER", "PULL_REQUEST_TITLE",
             "PULL_REQUEST_AUTHOR", "PULL_REQUEST_CREATION_DATE", "PULL_REQUEST_URL", "PULL_REQUEST_TEXT",
             "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:12Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830546", "1"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830587", "2"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:18Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830629", "3"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:20Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830663", "4"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:23Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830695", "5"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830726", "6"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:30Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830765", "7"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:32Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830803", "8"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:35Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830834", "9"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:39Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830889", "10"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830931", "11"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903830972", "12"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831020", "13"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:52Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831066", "14"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:34:55Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831114", "15"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:00Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831187", "16"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:03Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831223", "17"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:07Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831283", "18"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:10Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831337", "19"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:13Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831387", "20"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:16Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831422", "21"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:19Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831470", "22"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:22Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831506", "23"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:25Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831556", "24"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:28Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831611", "25"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:31Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831651", "26"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:34Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831696", "27"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:37Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831740", "28"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:40Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831778", "29"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:44Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831832", "30"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:46Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831872", "31"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831905", "32"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:51Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831944", "33"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:54Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903831979", "34"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:35:58Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832027", "35"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:01Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832083", "36"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:04Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832124", "37"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:07Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832177", "38"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:10Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832226", "39"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:13Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832268", "40"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832297", "41"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:18Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832327", "42"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:20Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832359", "43"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:23Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832395", "44"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832425", "45"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:29Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832472", "46"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:31Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832501", "47"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:34Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832551", "48"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:37Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832587", "49"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:40Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832637", "50"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832677", "51"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832716", "52"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:48Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832765", "53"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:51Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832802", "54"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:53Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832833", "55"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:57Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832879", "56"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:36:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832920", "57"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:02Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903832961", "58"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833012", "59"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833067", "60"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:11Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833098", "61"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:14Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833135", "62"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:16Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833177", "63"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:19Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833206", "64"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:21Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833236", "65"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:24Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833267", "66"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:26Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833307", "67"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:29Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833329", "68"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:31Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833365", "69"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:34Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833406", "70"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:37Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833439", "71"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:39Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833464", "72"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833504", "73"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:46Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833561", "74"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:49Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833593", "75"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:51Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833618", "76"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:54Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833661", "77"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:56Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833689", "78"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:37:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833716", "79"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:01Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833742", "80"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:05Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833784", "81"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:08Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833827", "82"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:11Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833866", "83"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:15Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833934", "84"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:19Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903833989", "85"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:22Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834037", "86"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:25Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834076", "87"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:28Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834126", "88"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:31Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834165", "89"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:34Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834203", "90"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:36Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834237", "91"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:39Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834275", "92"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:42Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834312", "93"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:45Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834354", "94"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:48Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834398", "95"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:51Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834443", "96"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:54Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834470", "97"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:56Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834500", "98"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:38:59Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834538", "99"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:39:03Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834590", "100"], 
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "3",
             "2021-08-23T14:33:22Z", "andymeneely", "Update README.md",
             "https://github.com/meyersbs/developer-apologies/pull/3", "", "2021-08-23T14:39:07Z", "meyersbs",
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834642", "101"]
        ]

        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "pull_requests/pull_requests.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected, actual)
        shutil.rmtree(input_data_dir)

        # Case 4 -- data_types="commits"
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "commits"
        expected_header = [
            "REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
            "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE",
            "COMMIT_URL", "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR",
            "COMMENT_URL", "COMMENT_TEXT"
        ]
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "commits/commits.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected_header, actual[0])
        over_100_count = 0
        for entry in actual:
            if entry[8] == "Implement pull request downloading.":
                over_100_count += 1
        self.assertEqual(102, over_100_count)
        shutil.rmtree(input_data_dir)

#### MAIN ##########################################################################################
if __name__ == "__main__":
    unittest.main(warnings="ignore")
