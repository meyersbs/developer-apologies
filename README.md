# Developer Apologies

## Description

Scripts to facilitate discovery and analysis of developer apologies in GitHub issues, commits, and pull requests.

## Motivation

To better understand the lead-up to a vulnerability, we are exploring the concept of "mistakes". While the research world has taxonomies of technical, software weaknesses, we lack a robust understanding of human mistakes. Behind every vulnerability is a set of mistakes, and one way to identify mistakes are when people apologize. These _self-admitted mistakes_ allow us to cluster and discover the many different types of mistakes in software development. We are developing an "apology miner" that uses natural language processing techniques to identify apology sentences in GitHub comments from issues, pull requests, and commits. Our miner will build this corpus of apologies, and then we will use word embedding to identify similarly-phrased clusters of apology phrases. We will take those clusters and map them to existing taxonomies of human error in the field of psychology.

## Dependencies

### System Dependencies

**NOTE:** This code has been implemented and tested on Ubuntu 20.04.2 LTS. It should run on any Linux system. We cannot make any guarantees for Windows.

- libhdf5-dev 1.10.4+
- Python 3.6+

### Python Dependencies

To install python dependencies, run: `pip3 install -r requirements.txt`.

## Setup

### GitHub API Token

To run this code, you need to acquire a GitHub API Token by following [these directions](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token).

For scope, do not select any checkboxes.

Copy your API Token into `github_api_token.txt`.

## Testing

To run unit tests, execute `./test.sh` from the root directory of the repository.

**NOTE:** You may need to make `test.sh` executable: `chmod ug+x test.sh`.

## Usage

``` bash
usage: main.py [-h] {download,load,delete,info_data,info_hdf5,info_rate_limit} ...

Scripts to facilitate downloading data from GitHub, loading it into an HDF5 file, and analyzing the data.

positional arguments:
  {download,load,delete,info_data,info_hdf5,info_rate_limit}
                        Available commands.
    download            Download data from GitHub repositories using the GraphQL API.
    load                Load downloaded data into an HDF5 file.
    delete              Delete local CSV data from disk. This command cannot be used to delete the HDF5 file.
    info_data           Display info about the downloaded data.
    info_hdf5           Display info about the data loaded into HDF5.
    info_rate_limit     Display rate limiting info from GitHub's GraphQL API.

optional arguments:
  -h, --help            show this help message and exit
```

### Download Command

This command downloads the specified data and saves it in CSV format to disk (in the specified data_dir). This command is a prerequisite for the load command.

``` bash
usage: main.py download [-h] repo_file {issues,pull_requests,commits,all} data_dir

positional arguments:
  repo_file             The path for a file containing GitHub repository URLs to download data from. This file should contain a single repo URL per line. Relative paths will be canonicalized.
  {issues,pull_requests,commits,all}
                        The type of data to download from the given repositories. All of the relevant metadata, including comments will be downloaded for whichever option is given.
  data_dir              The path for a directory to save the downloaded data to. Relative paths will be canonicalized. Downloaded data will be in the form of a CSV file and placed in a subdirectory, e.g. data_dir/issues/.

optional arguments:
  -h, --help            show this help message and exit
```

### Load Command

This command loads data from the specified data_dir into the specified HDF5 file.

**NOTE:** This command is not yet implemented.

``` bash
usage: main.py load [-h] hdf5_file data_dir

positional arguments:
  hdf5_file   The path/name of the HDF5 file to create and load with data. Relative paths will be canonicalized.
  data_dir    The path to a directory where data is downloaded and ready to be loaded. Relative paths will be canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Delete Command

This command deletes CSV data from the specified data_dir.

``` bash
usage: main.py delete [-h] data_dir

positional arguments:
  data_dir    The path for a directory containing downloaded data. Relative paths will be canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Info_Data Command

This command prints useful information about the downloaded CSV data.

**NOTE:** This command is not yet implemented.

``` bash
usage: main.py info_data [-h] data_dir

positional arguments:
  data_dir    The path for a directory containing downloaded data. Relative paths will be canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Info_HDF5 Command

This command prints useful information about the data loaded into the HDF5 file.

**NOTE:** This command is not yet implemented.

``` bash
usage: main.py info_hdf5 [-h] hdf5_file

positional arguments:
  hdf5_file   The path/name of an HDF5 file. Relative paths will be canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Info_Rate_Limit Command

This command prints out rate limit information for GitHub's GraphQL API.

``` bash
usage: main.py info_rate_limit [-h]

optional arguments:
  -h, --help  show this help message and exit
```

## License

[MIT License](LICENSE).

## Contact

- Benjamin S. Meyers <<bsm9339@rit.edu>>
