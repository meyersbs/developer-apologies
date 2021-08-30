#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import sys


#### PACKAGE IMPORTS ###############################################################################


#### GLOBALS #######################################################################################
SEARCH_REPOS_1 = """
{
    search(query: "FILTERS", type:REPOSITORY, first:100) {
        edges {
            node {
                ... on Repository {
                    url
                    stargazerCount
                    primaryLanguage { name }
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
"""
SEARCH_REPOS_2 = """
{
    search(query: "FILTERS", type:REPOSITORY, first:100, after:"AFTER") {
        edges {
            node {
                ... on Repository {
                    url
                    stargazerCount
                    primaryLanguage { name }
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
"""
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
QUERY_COMMITS_1 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        defaultBranchRef {
            target {
                ... on Commit {
                    history(first:100) {
                        edges {
                            node {
                                oid
                                author {
                                    user { login }
                                }
                                additions
                                deletions
                                committedDate
                                url
                                messageHeadline
                                messageBody
                                comments(first:100) {
                                    totalCount
                                    edges { 
                                        node {
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
        }
    }
}
"""
QUERY_COMMITS_2 = """
query {
    repository(owner:"OWNER", name:"NAME") {
        name
        owner { login }
        defaultBranchRef {
            target {
                ... on Commit {
                    history(first:100, after:"AFTER") {
                        edges {
                            node {
                                oid
                                author {
                                    user { login }
                                }
                                additions
                                deletions
                                committedDate
                                url
                                messageHeadline
                                messageBody
                                comments(first:100) {
                                    totalCount
                                    edges { 
                                        node {
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
        }
    }
}
"""
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
QUERY_COMMENTS_BY_COMMIT_OID = """
query {
    repository(owner:"OWNER", name:"NAME") {
        object(oid:"OID") {
            ... on Commit {
                comments(first:100, after:"AFTER") {
                    totalCount
                    edges { 
                        node {
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
}
"""


#### FUNCTIONS #####################################################################################


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
