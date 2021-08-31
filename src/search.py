#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import re


#### PACKAGE IMPORTS ###############################################################################
from src.graphql import searchRepos


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


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
