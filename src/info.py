#!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import h5py
import numpy as np
import sys
from collections import OrderedDict
from pprint import PrettyPrinter


#### PACKAGE IMPORTS ###############################################################################
from src.helpers import getFileSizeMB, getFileCreationTime, getFileModifiedTime


#### GLOBALS #######################################################################################
PP = PrettyPrinter(width=120)

#### FUNCTIONS #####################################################################################
def infoHDF5(hdf5_file, verbose=True):
    """
    Display useful information about the HDF5 file and its contents.

    GIVEN:
      hdf5_file (str) -- absolute path to an HDF5 file
      verbose (bool) -- flag to turn off printing during unit testing

    RETURN:
      metadata (OrderedDict) -- metadata for the HDF5 file
    """
    # Open the file
    f = h5py.File(hdf5_file, "r")

    # Get metadata
    metadata = OrderedDict()
    metadata.update({"filepath": hdf5_file})
    metadata.update({"keys": list(f.keys())})
    metadata.update({"filesize": "{} MB".format(round(getFileSizeMB(hdf5_file), 2))})
    metadata.update({"creation": getFileCreationTime(hdf5_file)})
    metadata.update({"modified": getFileModifiedTime(hdf5_file)})
    for dataset in list(f.keys()):
        ds_len = f[dataset][:].shape[0]
        ds_description = dict(f[dataset].attrs)["description"]
        if ds_len == 0:
            ds_repos = 0
        else:
            df = f[dataset][:]
            df = df[1:, ]
            repo_urls = df[:, 0]
            ds_repos = len(np.unique(repo_urls))
        metadata.update({
            dataset: OrderedDict({
                "num_items": ds_len,
                "num_repos": ds_repos,
                "description": ds_description
            })
        })

    # Cleanup
    h5py.File.close(f)

    # Display
    if verbose: # pragma: no cover
        PP.pprint(metadata)

    return metadata


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
