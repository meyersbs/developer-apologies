# Developer Apologies

## Description

Scripts to facilitate discovery and analysis of developer apologies in GitHub issues, commits, and pull requests.

## Motivation

To better understand the lead-up to a vulnerability, we are exploring the concept of "mistakes". While the research world has taxonomies of technical, software weaknesses, we lack a robust understanding of human mistakes. Behind every vulnerability is a set of mistakes, and one way to identify mistakes are when people apologize. These _self-admitted mistakes_ allow us to cluster and discover the many different types of mistakes in software development. We are developing an "apology miner" that uses natural language processing techniques to identify apology sentences in GitHub comments from issues, pull requests, and commits. Our miner will build this corpus of apologies, and then we will use word embedding to identify similarly-phrased clusters of apology phrases. We will take those clusters and map them to existing taxonomies of human error in the field of psychology.

## Background

### NLP Concepts

- **Lemmatization:** Lemmatization uses the context that a word appears in (the words on either side of it) to convert words into meaningful base forms (called **lemmas**). For example, the words *apology*, *apologies*, *apologize*, and *apologized* may all be converted to the same lemma (*apology*) depending on their context in a sentence.

### Apologies

Coming soon...

### Human Error Taxonomies

Coming soon...

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
usage: main.py [-h] {download,load,delete,search,info_data,info_hdf5,info_rate_limit} ...

Scripts to facilitate downloading data from GitHub, loading it into an HDF5 file, and analyzing
the data.

positional arguments:
  {download,load,delete,search,info_data,info_hdf5,info_rate_limit}
                        Available commands.
    download            Download data from GitHub repositories using the GraphQL API.
    load                Load downloaded data into an HDF5 file.
    delete              Delete local CSV data from disk. This command cannot be used to delete
                        the HDF5 file.
    search              Search GitHub for a list of repositories based on provided criteria.
    top_repos           Download the top 1000 repo URLs for each of the languages specified.
    preprocess          For each dataset in the given HDF5 file, append a
                        'COMMENT_TEXT_LEMMATIZED' column that contains the comment text that
                        (1) is lowercased, (2) has punctuation removed, (3) has non-space
                        whitespace removed, and (4) is lemmatized.
    classify            For each dataset in the given HDF5 file, append a 'NUM_POLOGY_LEMMAS'
                        column that contains the total number of apology lemmas in the
                        'COMMENT_TEXT_LEMMATIZED' column.
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
  repo_file             The path for a file containing GitHub repository URLs to download
                        data from. This file should contain a single repo URL per line.
                        Relative paths will be canonicalized.
  {issues,pull_requests,commits,all}
                        The type of data to download from the given repositories. All of
                        the relevant metadata, including comments will be downloaded for
                        whichever option is given.
  data_dir              The path for a directory to save the downloaded data to. Relative
                        paths will be canonicalized. Downloaded data will be in the form
                        of a CSV file and placed in a subdirectory, e.g. data_dir/issues/.

optional arguments:
  -h, --help            show this help message and exit
```

### Load Command

This command loads data from the specified data_dir into the specified HDF5 file.

``` bash
usage: main.py load [-h] hdf5_file data_dir

positional arguments:
  hdf5_file   The path/name of the HDF5 file to create and load with data. Relative paths
              will be canonicalized.
  data_dir    The path to a directory where data is downloaded and ready to be loaded.
              Relative paths will be canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Delete Command

This command deletes CSV data from the specified data_dir.

``` bash
usage: main.py delete [-h] data_dir

positional arguments:
  data_dir    The path for a directory containing downloaded data. Relative paths will be
              canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Search Command

This command searches GitHub for repositories based on provided criteria.

``` bash
usage: main.py search [-h] term stars total {language} save

positional arguments:
  term        Filter results to only include those that match this search term. Enter ''
              to remove this filter. Note that this cannot be empty when 'stars'=0 and
              'languages'='None' due to a limitation in the API.
  stars       Filter out repositories with less than this number of stars. Enter '0' to
              remove this filter.
  total       Return this many repositories (or less if filters are restrictive. Enter
              '0' to remove this filter. Note that the maximum number of results that
              can be returned is 1000 due to a limitation in the API.
  {language}  Filter results to only include repositories using this language. Enter
              'None' to remove this filter.

optional arguments:
  -h, --help  show this help message and exit
  --save      Whether or not to save the list of repositories to disk.
  --results_file RESULTS_FILE
              The name of the file to save results to. Relative paths will be
              canonicalized. This option is ignored when --save=False.
```

**NOTE:** Due to limitations in the API, only one language (or no language) can be specified.

**NOTE:** Any language that you can specify in the GitHub search bar is a valid option here. For a full list, see `GITHUB_LANGUAGES` in `src/helpers.py`.:

### Top_Repos Command

This command downloads 1000 repository URLs for each of the specified languages.

``` bash
usage: main.py top_repos [-h] {tiobe_index,github_popular,combined} stars results_file

positional arguments:
  {tiobe_index,github_popular,combined}
                        The list of languages to get repo URLs for. Either the top 50
                        from the TIOBE Index, the most popular from GitHub, or the
                        combined set of languages from both.
  stars                 Filter out repositories with less than this number of stars.
                        Enter '0' to remove this filter.
  results_file          The name of the file to save URLs to. Relative paths will be
                        canonicalized.

optional arguments:
  -h, --help            show this help message and exit

```

**NOTE:** This may download less than 1000 repo URLs for a language if there are not 1000 repos for that language with at least as many stars as specified.

### Preprocess Command

This command cleans up the comment text by lowercasing, removing punctuation and non-space whitespace, and lemmatizing.

``` bash
usage: main.py preprocess [-h] hdf5_file num_procs

positional arguments:
  hdf5_file   The path/name of an HDF5 file that has already been populated using the
              'load' command. Relative paths will be canonicalized.
  num_procs   Number of processes (CPUs) to use for multiprocessing.

optional arguments:
  -h, --help  show this help message and exit
```

**NOTE:** This command modifies the specified HDF5 file by adding a new column with the lemmatized text.

### Classify Command

This command counts the number of apology lemmas in the lemmatized comment text.

``` bash
usage: main.py classify [-h] hdf5_file num_procs

positional arguments:
  hdf5_file   The path/name of an HDF5 file that has already been populated using the
              'load' and 'preprocess' commands. Relative paths will be canonicalized.
  num_procs   Number of processes (CPUs) to use for multiprocessing. Enter '0' to use
              all available CPUs.

optional arguments:
  -h, --help  show this help message and exit
```

**NOTE:** This command modifies the specified HDF5 file by adding a new column with the number of apology lemmas.

### Info_Data Command

This command prints useful information about the downloaded CSV data.

**NOTE:** This command is not yet implemented.

``` bash
usage: main.py info_data [-h] data_dir

positional arguments:
  data_dir    The path for a directory containing downloaded data. Relative paths will be
              canonicalized.

optional arguments:
  -h, --help  show this help message and exit
```

### Info_HDF5 Command

This command prints useful information about the data loaded into the HDF5 file.

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
