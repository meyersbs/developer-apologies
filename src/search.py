#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import re
import sys


#### PACKAGE IMPORTS ###############################################################################
from src.graphql import searchRepos
from src.helpers import TIOBE_INDEX_TOP_50_AUG_2021, GITHUB_POPULAR_AUG_2021, COMBINED_LANGUAGES, \
    TEST_LANGUAGES


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def search(term, stars, language, total, save, results_file, verbose=True):
    """
    Search for GitHub repositories based on the given filters.

    GIVEN:
      term (str) -- return results matching this search term
      stars (int) -- return results with at least this many stars
      language (str) -- return results matching this language
      total (int) -- return this many repositories
      save (bool) -- whether or not to save the results to disk
      verbose (bool) -- flag to turn off printing for unit testing
      results_file (str) -- path to save results to if save==True

    RETURN:
      results (list) -- returned search results
    """
    # Format filters
    filters = "{} {} {}"
    element_1 = ""
    element_2 = ""
    element_3 = ""
    if term != "":
        element_1 = term
    if stars != 0:
        element_2 = "stars:>={}".format(stars)
    if language != "None":
        element_3 = "language:{}".format(language)

    filters = filters.format(element_1, element_2, element_3)

    # Clean up extra whitespace
    filters = filters.strip()
    filters = re.sub(r" +", " ", filters)
    
    # Get results
    results = searchRepos(filters, total)

    # Print results
    if verbose: # pragma: no cover
        print(results)

    # Save results
    if save:
        with open(results_file, "w") as f:
            for element in results:
                f.write(element[0] + "\n")
        print("Search results saved to '{}'.".format(results_file))
    
    # Return results
    return results


def topRepos(languages, stars, results_file, verbose=True):
    """
    Download the top 1000 repo URLs for each of the specified languages.

    GIVEN:
      languages (str) -- which list of languages to use; one of ["tiobe_index", "github_popular",
                        "combined"]
      stars (int) -- return results with at least this many stars
      results_file (str) -- path to save results to
    """
    repo_list = list()
    language_list = list()

    # Determine languages to use
    # Pragmas here because the unittest library is confused
    if languages == "tiobe_index": # pragma: no cover
        language_list = TIOBE_INDEX_TOP_50_AUG_2021
    elif languages == "github_popular": # pragma: no cover
        language_list = GITHUB_POPULAR_AUG_2021
    elif languages == "combined": # pragma: no cover
        language_list = COMBINED_LANGUAGES
    elif languages == "test": # pragma: no cover
        language_list = TEST_LANGUAGES
    else: # pragma: no cover
        pass # This should never happen

    # Grab results for each language
    for language in language_list:
        results = search("", stars, language, 1000, False, None, verbose=False)
        if verbose: # pragma: no cover
            print("Language: '{}', Repos: '{}'".format(language, len(results)))
        # Get just the repo URLs
        for element in results:
            repo_list.append(element[0])

    # Write results to disk
    with open(results_file, "w") as f:
        for element in repo_list:
            f.write(element + "\n")
    print("Repository URLs saved to '{}'.".format(results_file))

    # Return repos
    return repo_list
   

#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
