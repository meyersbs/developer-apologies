#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import csv
import h5py
import os
import shutil
import unittest
from collections import OrderedDict
from pathlib import Path
import unittest.mock as mock


#### PACKAGE IMPORTS ###############################################################################
from src.apologies import classify, _countApologies
from src.config import getAPIToken, EmptyAPITokenError
from src.delete import delete
from src.download import download
from src.graphql import _runQuery, runQuery, getRateLimitInfo
from src.helpers import canonicalize, doesPathExist, validateDataDir, parseRepoURL, \
    numpyByteArrayToStrList, InvalidGitHubURLError
from src.info import infoHDF5
from src.load import load
from src.preprocess import preprocess, _stripNonWords, _lemmatize
from src.search import search, topRepos


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
        #### Case 1 -- simple relative path
        input_path = "data/"
        expected = os.path.join(CWD, "data")
        actual = canonicalize(input_path)
        self.assertEqual(expected, actual)

        #### Case 2 -- complex relative path
        input_path = "data/../data/"
        expected = os.path.join(CWD, "data")
        actual = canonicalize(input_path)
        self.assertEqual(expected, actual)


    def test_doesPathExist(self):
        """
        Test src.helpers:doesPathExist().
        """
        #### Case 1 -- relative path that doesn't exist
        input_path = "data/apples/"
        actual = doesPathExist(input_path)
        self.assertFalse(actual)

        #### Case 2 -- absolute path that doesn't exist
        input_path = "data/apples/"
        actual = doesPathExist(canonicalize(input_path))
        self.assertFalse(actual)

        #### Case 3 -- relative path that does exist
        input_path = "data/__init__.py"
        actual = doesPathExist(input_path)
        self.assertTrue(actual)

        #### Case 4 -- absolute path that does exist
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

        #### Case 1 -- empty data_dir
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)       
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 2 -- data_dir with just issues dir
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "issues/"))
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 3 -- data_dir with just issues dir containing __init__.py
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "issues/"))
        Path(os.path.join(data_dir, "issues/__init__.py")).touch()
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 4 -- data_dir with just commits dir
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "commits/"))
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 5 -- data_dir with just commits dir containing __init__.py
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "commits/"))
        Path(os.path.join(data_dir, "commits/__init__.py")).touch()
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 6 -- data_dir with just pull_requests dir
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "pull_requests/"))
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 7 -- data_dir with just pull_requests dir containing __init__.py
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        os.mkdir(os.path.join(data_dir, "pull_requests/"))
        Path(os.path.join(data_dir, "pull_requests/__init__.py")).touch()
        validateDataDir(data_dir)
        # Test
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test


    def test_parseRepoURL(self):
        """
        Test src.helpers:parseRepoURL().
        """
        #### Case 1 -- GitHub URL
        input_url = "https://github.com/meyersbs/developer-apologies/"
        expected = ("meyersbs", "developer-apologies")
        actual = parseRepoURL(input_url)
        self.assertTupleEqual(expected, actual)

        #### Case 2 -- Non-GitHub URL
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
        #### Case 1 -- API token exists
        token_path = canonicalize("test_files/test_github_api_token.txt")
        expected = "abc_defG32ef6abd9mP4Qdmr5TY901sN01gF27eU"
        actual = getAPIToken(token_path)
        self.assertEqual(expected, actual)

        #### Case 2 -- blank API token
        token_path = canonicalize("test_files/test_github_api_token_empty.txt")
        self.assertRaises(EmptyAPITokenError, getAPIToken, token_path)


class TestInfo(unittest.TestCase):
    """
    Test cases for functions in src.info.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test_infoHDF5(self):
        """
        Test src.info:infoHDF5().
        """
        input_hdf5_file = canonicalize("test_files/test.hdf5")
        expected = OrderedDict([
            ("filepath", "/home/benjamin/Code/developer-apologies/test_files/test.hdf5"),
            ("keys", ["commits", "issues", "pull_requests"]),
            ("filesize", "0.02 MB"),
            ("creation", mock.ANY),
            ("modified", mock.ANY),
            ("commits", OrderedDict([
                ("num_items", 13),
                ("num_repos", 1),
                ("description", "GitHub commits with relevant metadata and comments. Columns: [REPO"
                                "_URL, REPO_NAME, REPO_OWNER, COMMIT_OID, COMMIT_CREATION_DATE, COM"
                                "MIT_AUTHOR, COMMIT_ADDITIONS, COMMIT_DELETIONS, COMMIT_HEADLINE, C"
                                "OMMIT_URL, COMMIT_TEXT, COMMENT_CREATION_DATE, COMMENT_AUTHOR, COM"
                                "MENT_URL, COMMENT_TEXT].")
            ])),
            ("issues", OrderedDict([
                ("num_items", 2),
                ("num_repos", 1),
                ("description", "GitHub issues with relevant metadata and comments. Columns: [REPO_"
                                "URL, REPO_NAME, REPO_OWNER, ISSUE_NUMBER, ISSUE_CREATION_DATE, ISS"
                                "UE_AUTHOR, ISSUE_TITLE, ISSUE_URL, ISSUE_TEXT, COMMENT_CREATION_DA"
                                "TE, COMMENT_AUTHOR, COMMENT_URL, COMMENT_TEXT].")
            ])),
            ("pull_requests", OrderedDict([
                ("num_items", 0),
                ("num_repos", 0),
                ("description", "GitHub pull_requests with relevant metadata and comments. Columns:"
                                " [REPO_URL, REPO_NAME, REPO_OWNER, PULL_REQUEST_NUMBER, PULL_REQUE"
                                "ST_TITLE, PULL_REQUEST_AUTHOR, PULL_REQUEST_CREATION_DATE, PULL_RE"
                                "QUEST_URL, PULL_REQUEST_TEXT, COMMENT_CREATION_DATE, COMMENT_AUTHO"
                                "R, COMMENT_URL, COMMENT_TEXT].")
            ]))
        ])
        actual = infoHDF5(input_hdf5_file, verbose=False)
        self.assertDictEqual(expected, actual)


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

        #### Case 1 -- all files exist
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        # Test
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 2 -- everything but issues.csv exists
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        # Test
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 3 -- everything but commits.csv exists
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "pull_requests/pull_requests.csv")).touch()
        # Test
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(data_dir) # Clean up before next test

        #### Case 4 -- everything but pull_requests.csv exists
        # Setup
        data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(data_dir)
        validateDataDir(data_dir) # We can use this because the test already passed
        Path(os.path.join(data_dir, "issues/issues.csv")).touch()
        Path(os.path.join(data_dir, "commits/commits.csv")).touch()
        # Test
        delete(data_dir)
        actual = list(os.walk(data_dir))
        self.assertListEqual(expected, actual)
        # Cleanup
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
        #### Case 1 -- dynamic, valid query
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

        #### Case 2 -- static, valid query
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

        #### Case 3 -- invalid query, status code != 200
        # This can't really be tested. GitHub's GraphQL API responds with status code = 200 even
        # when the query was malformed. It responds with a JSON dict with the key "errors", which
        # we can test.

        #### Case 4 -- invalid query, returning errors
        input_query = "query {}"
        expected = None
        actual = _runQuery(input_query)
        self.assertEqual(expected, actual)


    def test_runQuery(self):
        """
        Test src.graphql:runQuery().
        """
        #### Case 1 -- data_types="issues"
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

        #### Case 2 -- data_types="issues", with over 100 comments
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

        #### Case 3 -- data_types="pull_requests"
        input_repo_owner = "meyersbs"
        input_repo_name = "developer-apologies" # Yes, that's this repo!
        input_data_types = "pull_requests"
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        pull_requests = actual["data"]["repository"]["pullRequests"]["edges"]
        self.assertEqual(2, len(pull_requests))
        self.assertEqual("Update README.md", pull_requests[0]["node"]["title"])
        self.assertEqual("andymeneely", pull_requests[0]["node"]["author"]["login"])
        self.assertEqual("", pull_requests[0]["node"]["bodyText"])
        self.assertEqual("2021-08-23T14:33:22Z", pull_requests[0]["node"]["createdAt"])
        comments = pull_requests[0]["node"]["comments"]["edges"]
        self.assertEqual(101, len(comments))
        for comment in comments:
            self.assertEqual("meyersbs", comment["node"]["author"]["login"])

        #### Case 4 -- data_types="commits"
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

        #### Case 5 -- data_types="all"
        input_repo_owner = "meyersbs"
        input_repo_name = "tvdb-dl-nfo"
        input_data_types = "all"
        expected = None
        expected_issues = {
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
        expected_commits = {
            "data": {
                "repository": {
                    "name": "tvdb-dl-nfo",
                    "owner": {
                        "login": "meyersbs"
                    },
                    "defaultBranchRef": {
                        "target": {
                            "history": {
                                "edges": [
                                    {
                                        "node": {
                                            "oid": "5b2009b8db3299cdb810b20caaaea88adb5ebe08",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 1, "deletions": 1,
                                            "committedDate": "2019-11-27T19:09:42Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 1,
                                                "edges": [
                                                    {
                                                        "node": {
                                                        	"author": {"login": "meyersbs"},
                                                        	"bodyText": "Dummy comment.",
                                                        	"createdAt": "2021-08-24T12:52:30Z",
                                                        	"url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08#commitcomment-55353873"
                                                        }
                                                    }
                                                ],
                                                "pageInfo": {
                                                    "startCursor": "Y3Vyc29yOnYyOpHOA0yiEQ==",
                                                    "endCursor": "Y3Vyc29yOnYyOpHOA0yiEQ==",
                                                    "hasNextPage": False
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 6, "deletions": 2,
                                            "committedDate": "2019-11-27T19:03:34Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    }, 
                                    {
                                        "node": {
                                            "oid": "f307305e5a12208baa4cb01f188e8fa20d7a6ef3",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 3, "deletions": 3,
                                            "committedDate": "2019-05-11T21:04:23Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/f307305e5a12208baa4cb01f188e8fa20d7a6ef3",
                                            "messageHeadline": "Fix #1", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "c399298846a2bcdbc4daa53076b5f9899d8f916b",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 16, "deletions": 13,
                                            "committedDate": "2019-05-11T20:52:00Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/c399298846a2bcdbc4daa53076b5f9899d8f916b",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "23af721b3f70cdde0bcc3dc58ba3750dbab34b46",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 6, "deletions": 3,
                                            "committedDate": "2019-05-11T20:51:50Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/23af721b3f70cdde0bcc3dc58ba3750dbab34b46",
                                            "messageHeadline": "Read API Key from file rather than CLI.", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "bd163c63771e2e314470ce36a251b8e8ab9ce712",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 13, "deletions": 3,
                                            "committedDate": "2019-05-11T20:51:19Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/bd163c63771e2e314470ce36a251b8e8ab9ce712",
                                            "messageHeadline": "Change directory structure. Create apikey.txt", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "09929a23b30307ebbb426637d420b69216aa9772",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 10, "deletions": 0,
                                            "committedDate": "2019-05-07T23:45:44Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/09929a23b30307ebbb426637d420b69216aa9772",
                                            "messageHeadline": "Create install.sh", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 59, "deletions": 0,
                                            "committedDate": "2019-05-07T23:45:06Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308",
                                            "messageHeadline": "Create tvdb-dl-nfo.php", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "110efd9108faee147fa2430702999312d68f2329",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 12, "deletions": 1,
                                            "committedDate": "2019-05-07T23:41:41Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/110efd9108faee147fa2430702999312d68f2329",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "1445c6376609dbf6c6017b19ed418d1cd73f2f6e",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 30, "deletions": 4,
                                            "committedDate": "2019-05-07T23:38:41Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/1445c6376609dbf6c6017b19ed418d1cd73f2f6e",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "ae38a7f77d211c7678d1a518e797d0668598b472",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 78, "deletions": 1,
                                            "committedDate": "2019-05-07T20:01:02Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/ae38a7f77d211c7678d1a518e797d0668598b472",
                                            "messageHeadline": "Update README.md", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    },
                                    {
                                        "node": {
                                            "oid": "75614c09991b4313b1b999971aadd1d6d38f6ce7",
                                            "author": {"user": {"login": "meyersbs"}},
                                            "additions": 23, "deletions": 0,
                                            "committedDate": "2019-05-07T19:32:43Z",
                                            "url": "https://github.com/meyersbs/tvdb-dl-nfo/commit/75614c09991b4313b1b999971aadd1d6d38f6ce7",
                                            "messageHeadline": "Initial commit", "messageBody": "",
                                            "comments": {
                                                "totalCount": 0, "edges": [],
                                                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False}
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        expected_pull_requests = {
            "data": {
                "repository": {
                    "name": "tvdb-dl-nfo",
                    "owner": {
                        "login": "meyersbs"
                    },
                    "pullRequests": {
                        "totalCount": 0,
                        "edges": []
                    }
                }
            }
        }
        actual = runQuery(input_repo_owner, input_repo_name, input_data_types)
        self.assertDictEqual(expected_issues, actual[0])
        self.assertDictEqual(expected_commits, actual[1])
        self.assertDictEqual(expected_pull_requests, actual[2])

        #### Case 6 -- invalid data_types
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
        #### Case 1 -- data_types="issues"
        # Setup
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
        # Test
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "issues/issues.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected, actual)
        # Cleanup
        shutil.rmtree(input_data_dir)

        #### Case 2 -- data_types="issues", with over 100 comments
        # Setup
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "issues"
        expected_issues_3 = [
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
        # Test
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "issues/issues.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected_issues_3, actual)
        # Cleanup
        shutil.rmtree(input_data_dir)

        #### Case 3 -- data_types="pull_requests"
        # Setup
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "pull_requests"
        expected_pull_requests_3 = [
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
             "https://github.com/meyersbs/developer-apologies/pull/3#issuecomment-903834642", "101"],
            ["https://github.com/meyersbs/developer-apologies/", "developer-apologies", "meyersbs", "4",
             "2021-08-24T17:59:32Z", "bnk5096", "Brandon-test",
             "https://github.com/meyersbs/developer-apologies/pull/4", "", "", "", "", ""]
        ]
        # Test
        download(input_repo_file, input_data_dir, input_data_types)
        actual = list()
        with open(os.path.join(input_data_dir, "pull_requests/pull_requests.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual.append(entry)
        self.assertListEqual(expected_pull_requests_3, actual)
        # Cleanup
        shutil.rmtree(input_data_dir)

        #### Case 4 -- data_types="commits"
        # Setup
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
        # Test
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
        # Cleanup
        shutil.rmtree(input_data_dir)

        #### Case 5 -- data_types="all"
        # Setup
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_3.txt")
        input_data_dir = os.path.join(CWD, "test_data/")
        os.mkdir(input_data_dir)
        input_data_types = "all"
        actual_issues = list()
        actual_commits = list()
        actual_pull_requests = list()
        # Test
        download(input_repo_file, input_data_dir, input_data_types)
        with open(os.path.join(input_data_dir, "issues/issues.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual_issues.append(entry)
        with open(os.path.join(input_data_dir, "commits/commits.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual_commits.append(entry)
        with open(os.path.join(input_data_dir, "pull_requests/pull_requests.csv"), "r") as f:
            csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar="\"")
            for entry in csv_reader:
                actual_pull_requests.append(entry)
        # Test issues
        self.assertListEqual(expected_issues_3, actual_issues)
        # Test commits
        expected_header = [
            "REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
            "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE",
            "COMMIT_URL", "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR",
            "COMMENT_URL", "COMMENT_TEXT"
        ]
        self.assertListEqual(expected_header, actual_commits[0])
        over_100_count = 0
        for entry in actual_commits:
            if entry[8] == "Implement pull request downloading.":
                over_100_count += 1
        self.assertEqual(102, over_100_count)
        # Test pull requests
        self.assertListEqual(expected_pull_requests_3, actual_pull_requests)
        # Cleanup
        shutil.rmtree(input_data_dir)


class TestLoad(unittest.TestCase):
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


    def test_load(self):
        """
        Test src.load:load().
        """
        #### Case 1 -- append=False
        # Setup
        input_hdf5_file = os.path.join(CWD, "test_file.hdf5")
        input_data_dir = os.path.join(CWD, "test_data/")
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_2.txt")
        input_data_types = "all"
        os.mkdir(input_data_dir)
        validateDataDir(input_data_dir)
        expected_keys = ["commits", "issues", "pull_requests"]
        expected_issues = [
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
        expected_issues_attrs = {
            "description": "GitHub issues with relevant metadata and comments. Columns: [REPO_URL, "
                           "REPO_NAME, REPO_OWNER, ISSUE_NUMBER, ISSUE_CREATION_DATE, ISSUE_AUTHOR,"
                           " ISSUE_TITLE, ISSUE_URL, ISSUE_TEXT, COMMENT_CREATION_DATE, COMMENT_AUTH"
                           "OR, COMMENT_URL, COMMENT_TEXT]."
        }
        expected_commits = [
            [
                "REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
                "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE",
                "COMMIT_URL", "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR",
                "COMMENT_URL", "COMMENT_TEXT"
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "75614c09991b4313b1b999971aadd1d6d38f6ce7", "2019-05-07T19:32:43Z", "meyersbs", "23",
                "0", "Initial commit",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/75614c09991b4313b1b999971aadd1d6d38f6ce7",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "ae38a7f77d211c7678d1a518e797d0668598b472", "2019-05-07T20:01:02Z", "meyersbs", "78",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/ae38a7f77d211c7678d1a518e797d0668598b472",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "1445c6376609dbf6c6017b19ed418d1cd73f2f6e", "2019-05-07T23:38:41Z", "meyersbs", "30",
                "4", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/1445c6376609dbf6c6017b19ed418d1cd73f2f6e",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "110efd9108faee147fa2430702999312d68f2329", "2019-05-07T23:41:41Z", "meyersbs", "12",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/110efd9108faee147fa2430702999312d68f2329",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308", "2019-05-07T23:45:06Z", "meyersbs", "59",
                "0", "Create tvdb-dl-nfo.php",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "09929a23b30307ebbb426637d420b69216aa9772", "2019-05-07T23:45:44Z", "meyersbs", "10",
                "0", "Create install.sh",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/09929a23b30307ebbb426637d420b69216aa9772",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "bd163c63771e2e314470ce36a251b8e8ab9ce712", "2019-05-11T20:51:19Z", "meyersbs", "13",
                "3", "Change directory structure. Create apikey.txt",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/bd163c63771e2e314470ce36a251b8e8ab9ce712",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "23af721b3f70cdde0bcc3dc58ba3750dbab34b46", "2019-05-11T20:51:50Z", "meyersbs", "6",
                "3", "Read API Key from file rather than CLI.",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/23af721b3f70cdde0bcc3dc58ba3750dbab34b46",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "c399298846a2bcdbc4daa53076b5f9899d8f916b", "2019-05-11T20:52:00Z", "meyersbs", "16",
                "13", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/c399298846a2bcdbc4daa53076b5f9899d8f916b",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "f307305e5a12208baa4cb01f188e8fa20d7a6ef3", "2019-05-11T21:04:23Z", "meyersbs", "3",
                "3", "Fix #1",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/f307305e5a12208baa4cb01f188e8fa20d7a6ef3",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6", "2019-11-27T19:03:34Z", "meyersbs", "6",
                "2", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "5b2009b8db3299cdb810b20caaaea88adb5ebe08", "2019-11-27T19:09:42Z", "meyersbs", "1",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08",
                "", "2021-08-24T12:52:30Z", "meyersbs",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08#commitcomment-55353873",
                "Dummy comment."
            ]
        ]
        expected_commits_attrs = {
            "description": "GitHub commits with relevant metadata and comments. Columns: [REPO_URL,"
                           " REPO_NAME, REPO_OWNER, COMMIT_OID, COMMIT_CREATION_DATE, COMMIT_AUTHOR"
                           ", COMMIT_ADDITIONS, COMMIT_DELETIONS, COMMIT_HEADLINE, COMMIT_URL, COMM"
                           "IT_TEXT, COMMENT_CREATION_DATE, COMMENT_AUTHOR, COMMENT_URL, COMMENT_TE"
                           "XT]."
        }
        expected_pull_requests = list()
        expected_pull_requests_attrs = {
            "description": "GitHub pull_requests with relevant metadata and comments. Columns: [REP"
                           "O_URL, REPO_NAME, REPO_OWNER, PULL_REQUEST_NUMBER, PULL_REQUEST_TITLE, "
                           "PULL_REQUEST_AUTHOR, PULL_REQUEST_CREATION_DATE, PULL_REQUEST_URL, PULL"
                           "_REQUEST_TEXT, COMMENT_CREATION_DATE, COMMENT_AUTHOR, COMMENT_URL, COMM"
                           "ENT_TEXT]."
        }
        download(input_repo_file, input_data_dir, input_data_types)
        input_append = False
        # Test
        load(input_hdf5_file, input_data_dir, input_append)
        f = h5py.File(input_hdf5_file, "r")
        actual_keys = list(f.keys())
        actual_issues = numpyByteArrayToStrList(f["issues"][:])
        actual_commits = numpyByteArrayToStrList(f["commits"][:])
        actual_pull_requests = numpyByteArrayToStrList(f["pull_requests"][:])
        actual_issues_attrs = dict(f["issues"].attrs)
        actual_commits_attrs = dict(f["commits"].attrs)
        actual_pull_requests_attrs = dict(f["pull_requests"].attrs)
        self.assertListEqual(expected_keys, actual_keys)
        self.assertListEqual(expected_issues, actual_issues)
        self.assertListEqual(expected_commits, actual_commits)
        self.assertListEqual(expected_pull_requests, actual_pull_requests)
        self.assertDictEqual(expected_issues_attrs, actual_issues_attrs)
        self.assertDictEqual(expected_commits_attrs, actual_commits_attrs)
        self.assertDictEqual(expected_pull_requests_attrs, actual_pull_requests_attrs)
        # Cleanup
        shutil.rmtree(input_data_dir)
        h5py.File.close(f)

        #### Case 2 -- append=True
        # Setup
        input_hdf5_file = os.path.join(CWD, "test_file.hdf5")
        input_data_dir = os.path.join(CWD, "test_data_2/")
        input_repo_file = os.path.join(CWD, "test_files/repo_lists/test_repos_4.txt")
        input_data_types = "all"
        os.mkdir(input_data_dir)
        validateDataDir(input_data_dir)
        download(input_repo_file, input_data_dir, input_data_types)
        input_append = True
        expected_issues = [
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
                "rsand will be empty.",
                "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs", "1",
                "2018-11-07T20:03:46Z", "sojusnik", "Layout improvements",
                "https://github.com/meyersbs/gedit-text-stats/issues/1",
                'Your useful plugin has a small vertical offset (about 2px) in comparison to the ot'
                'her text in the status bar. Also the space between "CharCount" and "Reiner Text" c'
                'ould be bigger for aesthetical reasons, imho.\nHappens on Gedit 3.30.1 on Ubuntu 1'
                '8.10 with the Numix theme.',
                "2018-11-07T20:30:21Z", "meyersbs",
                "https://github.com/meyersbs/gedit-text-stats/issues/1#issuecomment-436766586",
                "Thank you for pointing this out. Unfortunately, I do not see the same error on Ged"
                "it 3.28.1 on Ubuntu 18.04 with the BlackMATE theme.\nI will look into it, but it m"
                "ay be a while before I have the time. If you find or can implement a fix, I welcom"
                "e you to submit a pull-request for review!"
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs", "1",
                "2018-11-07T20:03:46Z", "sojusnik", "Layout improvements",
                "https://github.com/meyersbs/gedit-text-stats/issues/1",
                'Your useful plugin has a small vertical offset (about 2px) in comparison to the ot'
                'her text in the status bar. Also the space between "CharCount" and "Reiner Text" c'
                'ould be bigger for aesthetical reasons, imho.\nHappens on Gedit 3.30.1 on Ubuntu 1'
                '8.10 with the Numix theme.',
                "2018-11-13T21:11:56Z", "sojusnik",
                "https://github.com/meyersbs/gedit-text-stats/issues/1#issuecomment-438438136",
                "Since I'm code illiterate I have to rely on your contribution. Thanks in advance!"
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs", "1",
                "2018-11-07T20:03:46Z", "sojusnik", "Layout improvements",
                "https://github.com/meyersbs/gedit-text-stats/issues/1",
                'Your useful plugin has a small vertical offset (about 2px) in comparison to the ot'
                'her text in the status bar. Also the space between "CharCount" and "Reiner Text" c'
                'ould be bigger for aesthetical reasons, imho.\nHappens on Gedit 3.30.1 on Ubuntu 1'
                '8.10 with the Numix theme.',
                "2018-12-19T16:18:23Z", "meyersbs",
                "https://github.com/meyersbs/gedit-text-stats/issues/1#issuecomment-448653856",
                "I cannot recreate the vertical offset bug that @sojusnik described. I welcome cont"
                "ributions from other developers if anyone can recreate and fix the bug."
            ]
        ]
        expected_commits = [
            [
                "REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
                "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE",
                "COMMIT_URL", "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR",
                "COMMENT_URL", "COMMENT_TEXT"
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "75614c09991b4313b1b999971aadd1d6d38f6ce7", "2019-05-07T19:32:43Z", "meyersbs", "23",
                "0", "Initial commit",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/75614c09991b4313b1b999971aadd1d6d38f6ce7",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "ae38a7f77d211c7678d1a518e797d0668598b472", "2019-05-07T20:01:02Z", "meyersbs", "78",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/ae38a7f77d211c7678d1a518e797d0668598b472",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "1445c6376609dbf6c6017b19ed418d1cd73f2f6e", "2019-05-07T23:38:41Z", "meyersbs", "30",
                "4", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/1445c6376609dbf6c6017b19ed418d1cd73f2f6e",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "110efd9108faee147fa2430702999312d68f2329", "2019-05-07T23:41:41Z", "meyersbs", "12",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/110efd9108faee147fa2430702999312d68f2329",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308", "2019-05-07T23:45:06Z", "meyersbs", "59",
                "0", "Create tvdb-dl-nfo.php",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/eb9c54a516ed2ae17b9b9b8ad22d854f9bf60308",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "09929a23b30307ebbb426637d420b69216aa9772", "2019-05-07T23:45:44Z", "meyersbs", "10",
                "0", "Create install.sh",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/09929a23b30307ebbb426637d420b69216aa9772",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "bd163c63771e2e314470ce36a251b8e8ab9ce712", "2019-05-11T20:51:19Z", "meyersbs", "13",
                "3", "Change directory structure. Create apikey.txt",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/bd163c63771e2e314470ce36a251b8e8ab9ce712",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "23af721b3f70cdde0bcc3dc58ba3750dbab34b46", "2019-05-11T20:51:50Z", "meyersbs", "6",
                "3", "Read API Key from file rather than CLI.",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/23af721b3f70cdde0bcc3dc58ba3750dbab34b46",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "c399298846a2bcdbc4daa53076b5f9899d8f916b", "2019-05-11T20:52:00Z", "meyersbs", "16",
                "13", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/c399298846a2bcdbc4daa53076b5f9899d8f916b",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "f307305e5a12208baa4cb01f188e8fa20d7a6ef3", "2019-05-11T21:04:23Z", "meyersbs", "3",
                "3", "Fix #1",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/f307305e5a12208baa4cb01f188e8fa20d7a6ef3",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6", "2019-11-27T19:03:34Z", "meyersbs", "6",
                "2", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/ba20e4c9218d445ab74ff26855e6bed2f3c4c5d6",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/tvdb-dl-nfo", "tvdb-dl-nfo", "meyersbs",
                "5b2009b8db3299cdb810b20caaaea88adb5ebe08", "2019-11-27T19:09:42Z", "meyersbs", "1",
                "1", "Update README.md",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08",
                "", "2021-08-24T12:52:30Z", "meyersbs",
                "https://github.com/meyersbs/tvdb-dl-nfo/commit/5b2009b8db3299cdb810b20caaaea88adb5ebe08#commitcomment-55353873",
                "Dummy comment."
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "69aeccf9c824a1b0da6711c97c1e3e1bf997c554", "2016-12-09T18:41:04Z", "meyersbs", "23",
                "0", "Initial commit",
                "https://github.com/meyersbs/gedit-text-stats/commit/69aeccf9c824a1b0da6711c97c1e3e1bf997c554",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "0572c2d8da209a407a74b7a5e06918e8c019ad62", "2016-12-09T18:41:29Z", "meyersbs", "1",
                "1", "Update LICENSE",
                "https://github.com/meyersbs/gedit-text-stats/commit/0572c2d8da209a407a74b7a5e06918e8c019ad62",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "1758bd16de74f12db54afe299b5b8ec11f48a605", "2016-12-09T21:52:09Z", "meyersbs", "86",
                "0", "Plugin displays Character Count, Word Count, and Sentence Count. WillBAD_CHAR",
                "https://github.com/meyersbs/gedit-text-stats/commit/1758bd16de74f12db54afe299b5b8ec11f48a605",
                "BAD_CHAR add more features later.",
                "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "b3b533630c6f955f8fb5fd8c06faeca664027c42", "2016-12-09T22:04:01Z", "meyersbs", "36",
                "0", "Update README.md",
                "https://github.com/meyersbs/gedit-text-stats/commit/b3b533630c6f955f8fb5fd8c06faeca664027c42",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "26ea166966eca25e4f88b6728438b06073054fa9", "2016-12-10T02:18:48Z", "meyersbs", "9",
                "0", "Created install script.",
                "https://github.com/meyersbs/gedit-text-stats/commit/26ea166966eca25e4f88b6728438b06073054fa9",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "8c8f4eb7bbd8cfe9046fcf7f3a57b465083935b3", "2016-12-10T02:19:17Z", "meyersbs", "0",
                "0", "Rename LICENSE to LICENSE.md",
                "https://github.com/meyersbs/gedit-text-stats/commit/8c8f4eb7bbd8cfe9046fcf7f3a57b465083935b3",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "3aec2be95dd2660c8c6d7941a6400f4f53a67b4d", "2016-12-10T02:21:38Z", "meyersbs", "6",
                "4", "Update README.md",
                "https://github.com/meyersbs/gedit-text-stats/commit/3aec2be95dd2660c8c6d7941a6400f4f53a67b4d",
                "", "", "", "", ""
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs",
                "c5515b7e7e4525d6767409b00cd03cb40090e705", "2018-08-22T20:07:29Z", "meyersbs", "9",
                "1", "Legacy commit: Added line count.",
                "https://github.com/meyersbs/gedit-text-stats/commit/c5515b7e7e4525d6767409b00cd03cb40090e705",
                "", "", "", "", ""
            ]
        ]
        expected_pull_requests = [
            [
                "REPO_URL", "REPO_NAME", "REPO_OWNER", "PULL_REQUEST_NUMBER", "PULL_REQUEST_TITLE",
                "PULL_REQUEST_AUTHOR", "PULL_REQUEST_CREATION_DATE", "PULL_REQUEST_URL",
                "PULL_REQUEST_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL",
                "COMMENT_TEXT"
            ],
            [
                "https://github.com/meyersbs/gedit-text-stats", "gedit-text-stats", "meyersbs", "2",
                "2021-08-25T18:50:19Z", "meyersbs", "Update README.md",
                "https://github.com/meyersbs/gedit-text-stats/pull/2", "", "", "", "", ""
            ]
        ]
        # Test
        load(input_hdf5_file, input_data_dir, input_append)
        f = h5py.File(input_hdf5_file, "r")
        actual_keys = list(f.keys())
        actual_issues = numpyByteArrayToStrList(f["issues"][:])
        actual_commits = numpyByteArrayToStrList(f["commits"][:])
        actual_pull_requests = numpyByteArrayToStrList(f["pull_requests"][:])
        actual_issues_attrs = dict(f["issues"].attrs)
        actual_commits_attrs = dict(f["commits"].attrs)
        actual_pull_requests_attrs = dict(f["pull_requests"].attrs)
        self.assertListEqual(expected_keys, actual_keys)
        self.assertListEqual(expected_issues, actual_issues)
        self.assertListEqual(expected_commits, actual_commits)
        self.assertListEqual(expected_pull_requests, actual_pull_requests)
        self.assertDictEqual(expected_issues_attrs, actual_issues_attrs)
        self.assertDictEqual(expected_commits_attrs, actual_commits_attrs)
        self.assertDictEqual(expected_pull_requests_attrs, actual_pull_requests_attrs)
        # Cleanup
        shutil.rmtree(input_data_dir)
        h5py.File.close(f)
        os.remove(input_hdf5_file)


class TestSearch(unittest.TestCase):
    """
    Test cases for function in src.search.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test_search(self):
        """
        Test src.search:search().
        """
        #### Case 1 -- term="cherrypie", language="None", stars=0, total=10, save=False
        # Setup
        input_term = "cherrypie"
        input_stars = 0
        input_language = "None"
        input_total = 10
        input_save = False
        input_results = None
        # Test
        actual = search(input_term, input_stars, input_language, input_total, input_save, input_results, verbose=False)
        # With stars=0, the order that results are returned is not guaranteed. So, we can only test:
        self.assertEqual(10, len(actual))
        for element in actual:
            self.assertEqual(3, len(element))

        #### Case 2 -- term="cherrypie", language="Python", stars=0, total=0, save=False
        # Setup
        input_term = "cherrypie"
        input_stars = 0
        input_language = "Python"
        input_total = 0
        input_save = False
        input_results = None
        expected = [
            ["https://github.com/cherrypie623/CherryPie-Addon-Repository", 2, "Python"],
            ["https://github.com/zhengjiwen/cherrypie", 1, "Python"],
            ["https://github.com/further-i-go-less-i-know/cherrypie-ssl-errors", 0, "Python"]
        ]
        # Test
        actual = search(input_term, input_stars, input_language, input_total, input_save, input_results, verbose=False)
        self.assertListEqual(expected, actual)

        #### Case 3 -- term="cherrypie", language=Python, stars=1, total=0, save=False
        input_term = "cherrypie"
        input_stars = 1
        input_language = "Python"
        input_total = 0
        input_save = False
        input_results = None
        expected = [
            ["https://github.com/cherrypie623/CherryPie-Addon-Repository", 2, "Python"],
            ["https://github.com/zhengjiwen/cherrypie", 1, "Python"]
        ]
        # Test
        actual = search(input_term, input_stars, input_language, input_total, input_save, input_results, verbose=False)
        self.assertListEqual(expected, actual)

        #### Case 4 -- term="", language="", stars=20000, total=5, save=True
        input_term = ""
        input_stars = 20000
        input_language = ""
        input_total = 5
        input_save = True
        input_results = os.path.join(CWD, "search_results.txt")
        expected = [
            ["https://github.com/freeCodeCamp/freeCodeCamp", 329259, "JavaScript"],
            ["https://github.com/996icu/996.ICU", 258523, "Rust"],
            ["https://github.com/EbookFoundation/free-programming-books", 201274, "None"],
            ["https://github.com/jwasham/coding-interview-university", 190585, "None"],
            ["https://github.com/vuejs/vue", 187493, "JavaScript"]
        ]
        expected_saved_results = [
            "https://github.com/freeCodeCamp/freeCodeCamp",
            "https://github.com/996icu/996.ICU",
            "https://github.com/EbookFoundation/free-programming-books",
            "https://github.com/jwasham/coding-interview-university",
            "https://github.com/vuejs/vue"
        ]
        # Test
        actual = search(input_term, input_stars, input_language, input_total, input_save, input_results, verbose=False)
        # Number of stars might change, but top 5 repos probably won't. We need to test this way:
        exp = sorted(expected)
        act = sorted(actual)
        for i in range(0, 5):
            self.assertEqual(exp[i][0], act[i][0])
            self.assertEqual(exp[i][2], act[i][2])
        actual_saved_results = list()
        with open(input_results, "r") as f:
            for line in f:
                actual_saved_results.append(line.rstrip())
        self.assertListEqual(expected_saved_results, actual_saved_results)
        # Cleanup
        os.remove(input_results)


    def test_topRepos(self):
        """
        Test src.search:topRepos().
        """
        #### Case 1 -- languages="test", stars=30000
        # Setup
        input_languages = "test"
        input_stars = 30000
        input_results = os.path.join(CWD, "test_repo_urls.txt")
        input_verbose = False
        expected = [
            "https://github.com/torvalds/linux", "https://github.com/netdata/netdata",
            "https://github.com/Genymobile/scrcpy", "https://github.com/redis/redis",
            "https://github.com/git/git", "https://github.com/php/php-src",
            "https://github.com/obsproject/obs-studio", "https://github.com/wg/wrk",
            "https://github.com/tensorflow/tensorflow", "https://github.com/electron/electron",
            "https://github.com/microsoft/terminal", "https://github.com/apple/swift",
            "https://github.com/bitcoin/bitcoin", "https://github.com/opencv/opencv",
            "https://github.com/pytorch/pytorch", "https://github.com/protocolbuffers/protobuf",
            "https://github.com/godotengine/godot", "https://github.com/tesseract-ocr/tesseract",
            "https://github.com/x64dbg/x64dbg", "https://github.com/BVLC/caffe",
            "https://github.com/grpc/grpc", "https://github.com/ocornut/imgui",
            "https://github.com/microsoft/PowerToys", "https://github.com/shadowsocks/shadowsocks-windows",
            "https://github.com/CyC2018/CS-Notes", "https://github.com/Snailclimb/JavaGuide",
            "https://github.com/iluwatar/java-design-patterns", "https://github.com/MisterBooo/LeetCodeAnimation",
            "https://github.com/spring-projects/spring-boot", "https://github.com/doocs/advanced-java",
            "https://github.com/elastic/elasticsearch", "https://github.com/kdn251/interviews",
            "https://github.com/macrozheng/mall", "https://github.com/ReactiveX/RxJava",
            "https://github.com/spring-projects/spring-framework", "https://github.com/google/guava",
            "https://github.com/TheAlgorithms/Java", "https://github.com/square/retrofit",
            "https://github.com/kon9chunkit/GitHub-Chinese-Top-Charts", "https://github.com/apache/dubbo",
            "https://github.com/PhilJay/MPAndroidChart", "https://github.com/airbnb/lottie-android",
            "https://github.com/bumptech/glide", "https://github.com/freeCodeCamp/freeCodeCamp",
            "https://github.com/vuejs/vue", "https://github.com/facebook/react",
            "https://github.com/twbs/bootstrap", "https://github.com/trekhleb/javascript-algorithms",
            "https://github.com/airbnb/javascript", "https://github.com/d3/d3",
            "https://github.com/facebook/react-native", "https://github.com/facebook/create-react-app",
            "https://github.com/axios/axios", "https://github.com/30-seconds/30-seconds-of-code",
            "https://github.com/nodejs/node", "https://github.com/mrdoob/three.js",
            "https://github.com/vercel/next.js", "https://github.com/mui-org/material-ui",
            "https://github.com/goldbergyoni/nodebestpractices", "https://github.com/FortAwesome/Font-Awesome",
            "https://github.com/awesome-selfhosted/awesome-selfhosted", "https://github.com/angular/angular.js",
            "https://github.com/webpack/webpack", "https://github.com/hakimel/reveal.js",
            "https://github.com/yangshun/tech-interview-handbook", "https://github.com/typicode/json-server",
            "https://github.com/ryanmcdermott/clean-code-javascript", "https://github.com/atom/atom",
            "https://github.com/jquery/jquery", "https://github.com/chartjs/Chart.js",
            "https://github.com/socketio/socket.io", "https://github.com/expressjs/express",
            "https://github.com/adam-p/markdown-here", "https://github.com/h5bp/html5-boilerplate",
            "https://github.com/gatsbyjs/gatsby", "https://github.com/lodash/lodash",
            "https://github.com/resume/resume.github.com", "https://github.com/Semantic-Org/Semantic-UI",
            "https://github.com/tailwindlabs/tailwindcss", "https://github.com/moment/moment",
            "https://github.com/scutan90/DeepLearning-500-questions", "https://github.com/jaywcjlove/awesome-mac",
            "https://github.com/remix-run/react-router", "https://github.com/azl397985856/leetcode",
            "https://github.com/leonardomso/33-js-concepts", "https://github.com/meteor/meteor",
            "https://github.com/NARKOZ/hacker-scripts", "https://github.com/serverless/serverless",
            "https://github.com/prettier/prettier", "https://github.com/juliangarnier/anime",
            "https://github.com/yarnpkg/yarn", "https://github.com/babel/babel",
            "https://github.com/ColorlibHQ/AdminLTE", "https://github.com/strapi/strapi",
            "https://github.com/parcel-bundler/parcel", "https://github.com/iptv-org/iptv",
            "https://github.com/Dogfalo/materialize", "https://github.com/nwjs/nw.js",
            "https://github.com/TryGhost/Ghost", "https://github.com/nuxt/nuxt.js",
            "https://github.com/mermaid-js/mermaid", "https://github.com/impress/impress.js",
            "https://github.com/iamkun/dayjs", "https://github.com/mozilla/pdf.js",
            "https://github.com/Unitech/pm2", "https://github.com/algorithm-visualizer/algorithm-visualizer",
            "https://github.com/microsoft/Web-Dev-For-Beginners", "https://github.com/chinese-poetry/chinese-poetry",
            "https://github.com/adobe/brackets", "https://github.com/GitSquared/edex-ui",
            "https://github.com/Marak/faker.js", "https://github.com/hexojs/hexo",
            "https://github.com/dcloudio/uni-app", "https://github.com/cypress-io/cypress",
            "https://github.com/alvarotrigo/fullPage.js", "https://github.com/gulpjs/gulp",
            "https://github.com/sahat/hackathon-starter", "https://github.com/videojs/video.js",
            "https://github.com/Leaflet/Leaflet", "https://github.com/koajs/koa",
            "https://github.com/yangshun/front-end-interview-handbook", "https://github.com/zenorocha/clipboard.js",
            "https://github.com/quilljs/quill", "https://github.com/RocketChat/Rocket.Chat",
            "https://github.com/photonstorm/phaser", "https://github.com/jondot/awesome-react-native",
            "https://github.com/laravel/laravel", "https://github.com/danielmiessler/SecLists",
            "https://github.com/blueimp/jQuery-File-Upload", "https://github.com/public-apis/public-apis",
            "https://github.com/donnemartin/system-design-primer", "https://github.com/TheAlgorithms/Python",
            "https://github.com/jackfrued/Python-100-Days", "https://github.com/vinta/awesome-python",
            "https://github.com/ytdl-org/youtube-dl", "https://github.com/tensorflow/models",
            "https://github.com/nvbn/thefuck", "https://github.com/django/django",
            "https://github.com/pallets/flask", "https://github.com/keras-team/keras",
            "https://github.com/httpie/httpie", "https://github.com/josephmisiti/awesome-machine-learning",
            "https://github.com/huggingface/transformers", "https://github.com/ansible/ansible",
            "https://github.com/scikit-learn/scikit-learn", "https://github.com/521xueweihan/HelloGitHub",
            "https://github.com/psf/requests", "https://github.com/home-assistant/core",
            "https://github.com/soimort/you-get", "https://github.com/scrapy/scrapy",
            "https://github.com/ageitgey/face_recognition", "https://github.com/minimaxir/big-list-of-naughty-strings",
            "https://github.com/apache/superset", "https://github.com/python/cpython",
            "https://github.com/deepfakes/faceswap", "https://github.com/3b1b/manim",
            "https://github.com/tiangolo/fastapi", "https://github.com/localstack/localstack",
            "https://github.com/fighting41love/funNLP", "https://github.com/shadowsocks/shadowsocks",
            "https://github.com/0voice/interview_internal_reference", "https://github.com/isocpp/CppCoreGuidelines",
            "https://github.com/apachecn/AiLearning", "https://github.com/pandas-dev/pandas",
            "https://github.com/XX-net/XX-Net", "https://github.com/floodsung/Deep-Learning-Papers-Reading-Roadmap",
            "https://github.com/testerSunshine/12306", "https://github.com/rails/rails",
            "https://github.com/jekyll/jekyll", "https://github.com/discourse/discourse",
            "https://github.com/fastlane/fastlane", "https://github.com/huginn/huginn",
            "https://github.com/ohmyzsh/ohmyzsh", "https://github.com/gothinkster/realworld",
            "https://github.com/nvm-sh/nvm", "https://github.com/papers-we-love/papers-we-love",
            "https://github.com/pi-hole/pi-hole", "https://github.com/microsoft/vscode",
            "https://github.com/angular/angular", "https://github.com/ant-design/ant-design",
            "https://github.com/microsoft/TypeScript", "https://github.com/puppeteer/puppeteer",
            "https://github.com/storybookjs/storybook", "https://github.com/reduxjs/redux",
            "https://github.com/sveltejs/svelte", "https://github.com/apache/echarts",
            "https://github.com/cdr/code-server", "https://github.com/ionic-team/ionic-framework",
            "https://github.com/grafana/grafana", "https://github.com/nestjs/nest",
            "https://github.com/vercel/hyper", "https://github.com/facebook/jest",
            "https://github.com/DefinitelyTyped/DefinitelyTyped",
            "https://github.com/styled-components/styled-components", "https://github.com/pixijs/pixijs",
            "https://github.com/vuetifyjs/vuetify", "https://github.com/immutable-js/immutable-js",
            "https://github.com/vitejs/vite", "https://github.com/ant-design/ant-design-pro",
            "https://github.com/anuraghazra/github-readme-stats", 'https://github.com/open-guides/og-aws',
            'https://github.com/CorentinJ/Real-Time-Voice-Cloning',
            'https://github.com/swisskyrepo/PayloadsAllTheThings'
        ]
        # Test
        actual = topRepos(input_languages, input_stars, input_results, input_verbose)
        # This changes sometimes, so I'm leaving these debug statements to help figure out what
        # changed
        #print(len(expected))
        #print(len(actual))
        #print(sorted(expected))
        #print(sorted(actual))
        #print(set(expected).difference(set(actual)))
        #print(set(actual).difference(set(expected)))
        self.assertListEqual(sorted(expected), sorted(actual))


class TestPreprocess(unittest.TestCase):
    """
    Test cases for function in src.preprocess.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass


    def test__stripNonWords(self):
        """
        Test src.preprocess:_stripNonWords().
        """
        # Setup
        test_cases = [
            "apples!", "oranges?", "Bananas; pears: plums", "carrots, celery, and\n beets",
            "onions,  CUCUMBERS,   and    peppers."
        ]
        expected = [
            "apples", "oranges", "bananas pears plums", "carrots celery and beets",
            "onions cucumbers and peppers"
        ]
        actual = list()
        # Test
        for case in test_cases:
            actual.append(_stripNonWords(case))
        self.assertListEqual(expected, actual)


    def test__lemmatize(self):
        """
        Test src.preprocess:_lemmatize().
        """
        # Setup
        test_cases = [
            "the quick brown fox jumps over the lazy dog",
            "i'm sorry if you're offended",
            "you wouldn't download a pizza would you",
            "only you can prevent forest fires",
            "don't forget to be awesome"
        ]
        expected = [
            "the quick brown fox jump over the lazy dog",
            "I be sorry if you be offend",
            "you would n't download a pizza would you",
            "only you can prevent forest fire",
            "do n't forget to be awesome"
        ]
        actual = list()
        # Test
        for case in test_cases:
            actual.append(_lemmatize(case))
        self.assertListEqual(expected, actual)


    def test_preprocess(self):
        """
        Test src.preprocess:preprocess().
        """
        #### Case 1 -- num_procs=1
        # Setup
        input_hdf5_file = os.path.join(CWD, "test_files/test2.hdf5")
        input_num_procs = 1
        data_dir = os.path.join(CWD, "test_files/test_data2/")
        append = False
        expected_issue_lemmas = [
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16",
            "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
            "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44",
            "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58",
            "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72",
            "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86",
            "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100",
            "101", "dummy comment", "sorry but I figure I 'd add a data point sorrynotsorry"
        ]
        expected_commit_lemmas = [
            "", "", "", "", "", "", "", "", "", "", "", "dummy commit comment", "1", "2", "3", "4",
            "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
            "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
            "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47",
            "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61",
            "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75",
            "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
            "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "", "", "",
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
        ]
        expected_pull_request_lemmas = [
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16",
            "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
            "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44",
            "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58",
            "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72",
            "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86",
            "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100",
            "101", ""
        ]
        load(input_hdf5_file, data_dir, append)
        # Test data before write
        actual = preprocess(input_hdf5_file, input_num_procs)
        actual_issue_lemmas = list(actual[0])
        actual_commit_lemmas = list(actual[1])
        actual_pull_request_lemmas = list(actual[2])
        self.assertListEqual(expected_issue_lemmas, actual_issue_lemmas)
        self.assertListEqual(expected_commit_lemmas, actual_commit_lemmas)
        self.assertListEqual(expected_pull_request_lemmas, actual_pull_request_lemmas)
        # Test data after write
        f = h5py.File(input_hdf5_file)
        actual_issue_lemmas = numpyByteArrayToStrList(f["issues"][...][:, -1])[1:]
        self.assertListEqual(expected_issue_lemmas, actual_issue_lemmas)
        actual_commit_lemmas = numpyByteArrayToStrList(f["commits"][...][:, -1])[1:]
        self.assertListEqual(expected_commit_lemmas, actual_commit_lemmas)
        actual_pull_request_lemmas = numpyByteArrayToStrList(f["pull_requests"][...][:, -1])[1:]
        self.assertListEqual(expected_pull_request_lemmas, actual_pull_request_lemmas)
        # Cleanup
        h5py.File.close(f)
        os.remove(input_hdf5_file)


class TestApologies(unittest.TestCase):
    """
    Test cases for function in src.apologies.
    """
    def setUp(self):
        """
        Necessary setup for test cases.
        """
        pass

    
    def test__countApologies(self):
        """
        Test src.apologies:_countApologies().
        """
        # Setup
        test_cases = [
            "I need to apologize for accidentally drive my car into your house",
            "sorry I forget how to use the brake",
            "pardon the interruption",
            "I be mistaken that should have be + = not =",
            "I 'll take the blame for this",
            "who write this spaghetti code",
            "oops that should have be delete",
            "that be my fault for not unit testing",
            "I apologize I be so sorry about this",
            "I do nothing wrong it work as intend"
        ]
        expected_apologies = [
            "1", "1", "1", "1", "1", "0", "1", "1", "2", "0"
        ]
        actual_apologies = list()
        # Test
        for case in test_cases:
            actual_apologies.append(_countApologies(case))
        self.assertListEqual(expected_apologies, actual_apologies)


    def test_classify(self):
        """
        Test src.apologies:classify().
        """
        # Setup
        input_hdf5_file = os.path.join(CWD, "test_files/test2.hdf5")
        input_num_procs = 1
        data_dir = os.path.join(CWD, "test_files/test_data2/")
        append = False
        expected_issue_apologies = [
            "NUM_APOLOGY_LEMMAS", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "1"
        ]
        expected_commit_apologies = [
            "NUM_APOLOGY_LEMMAS", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0"
        ]
        expected_pull_request_apologies = [
            "NUM_APOLOGY_LEMMAS", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"
        ]
        load(input_hdf5_file, data_dir, append)
        preprocess(input_hdf5_file, input_num_procs)
        # Test data before write
        actual = classify(input_hdf5_file, input_num_procs)
        actual_issue_apologies = list(actual[0])
        actual_commit_apologies = list(actual[1])
        actual_pull_request_apologies = list(actual[2])
        self.assertListEqual(expected_issue_apologies, actual_issue_apologies)
        self.assertListEqual(expected_commit_apologies, actual_commit_apologies)
        self.assertListEqual(expected_pull_request_apologies, actual_pull_request_apologies)
        # Test data after write
        f = h5py.File(input_hdf5_file)
        actual_issue_apologies = numpyByteArrayToStrList(f["issues"][...][:, -1])
        actual_commit_apologies = numpyByteArrayToStrList(f["commits"][...][:, -1])
        actual_pull_request_apologies = numpyByteArrayToStrList(f["pull_requests"][...][:, -1])
        self.assertListEqual(expected_issue_apologies, actual_issue_apologies)
        self.assertListEqual(expected_commit_apologies, actual_commit_apologies)
        self.assertListEqual(expected_pull_request_apologies, actual_pull_request_apologies)
        # Cleanup
        h5py.File.close(f)
        os.remove(input_hdf5_file)


#### MAIN ##########################################################################################
if __name__ == "__main__":
    unittest.main(warnings="ignore")
