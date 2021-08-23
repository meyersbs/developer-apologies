# Developer Apologies

## Description

Scripts to facilitate discovery and analysis of developer apologies in GitHub issues and pull-requests.

## Motivation

Identifying apologies is a way to identify self-admitted **mistakes**. Once identified, we can catalog developer mistakes into one of two taxonomies:

1. Human Error Taxonmy: Slips, Lapses, Errors.
2. Errors of Omission, Commission, and Realization.

Cataloging developer mistakes yields a knowledge-base to help developers learn from their mistakes.

## Dependencies

- PostgreSQL 9.6+
- More coming soon!

## Setup

### (1) Download Data

``` bash
    # Warning: This is just shy of 103 GB
    wget http://ghtorrent-downloads.ewi.tudelft.nl/mysql/mysql-2019-06-01.tar.gz
    tar -zxvf mysql-2019-06-01.tar.gz
```

### (2) Configure Postgres

``` psql
    # Use whatever values for 'ghtdb', 'ghtuser', and 'ghtpass' you want
    CREATE DATABASE ghtdb;
    CREATE USER ghtuser WITH PASSWORD 'ghtpass';
    GRANT ALL PRIVILEGES ON DATABASE ghtdb to ghtuser;
    ALTER USER ghtuser WITH SUPERUSER;
```

### (3) Import Data to Postgres

``` bash
    cd mysql-2019-06-01/
    chmod +x ght-retore-pg
    ./ght-restore-pg -u ghtuser -d ghtdb -p ghtpass .
```

**NOTE:** The script [ght-restore-pg](ght-restore-pg) was copied from [this repository](https://github.com/gousiosg/github-mirror/tree/master/sql).

### (4) Analysis Setup

Coming soon!

## Usage

Coming soon!

## License

[MIT License](LICENSE).

## Contact

- Benjamin S. Meyers <<bsm9339@rit.edu>>
