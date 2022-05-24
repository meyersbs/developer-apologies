#!/usr/bin/env python3


#### IMPORTS #######################################################################################
import csv
import sys
from sklearn.metrics import cohen_kappa_score


#### GLOBALS #######################################################################################


#### FUNCTIONS #####################################################################################
def readData(filepath):
    annotator_1 = list()
    annotator_2 = list()
    labels = ["Yes", "No"]

    with open(filepath, "r") as f:
        csv_reader = csv.reader(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)

        next(csv_reader)

        for line in csv_reader:
            annotator_1.append(line[2])
            annotator_2.append(line[3])

    return [annotator_1, annotator_2, labels]


#### MAIN ##########################################################################################
if __name__ == "__main__":
    args = sys.argv[1:]
    filepath = args[0]
    annotator_1, annotator_2, labels = readData(filepath)
    cohens_kappa = cohen_kappa_score(annotator_1, annotator_2, labels, None, None)
    print(cohens_kappa)

