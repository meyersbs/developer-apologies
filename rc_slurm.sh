#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J dev_apologies

# Standard Out
# Format: -o <file_name>
#SBATCH -o dev_apologies.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e dev_apologies.stderr

# Email for Notifications
# Format: --mail-user=<email@email.com>
#SBATCH --mail-user=bsm9339@rit.edu

# States to Trigger Emails
# Format: --mail-type=<BEGIN,END,FAIL,ALL>
#SBATCH --mail-type=ALL

# Job Duration
# Format: -t DD-HH:MM:SS
#SBATCH -t 1-0:0:0

# Job Account, Job Tier, Number of Cores
# Format: -A <account_name> -p <onboard, tier1, tier2, tier3> -n <num_cpus>
#SBATCH -A dev_mistakes -p tier3 -n 4

# Job Memory
# Format: --mem=<num><k,m,g,t> (KB, MB, GB, TB)
#SBATCH --mem=20g

# Environment Settings
# TODO

# Job Script
# To execute this file, simply run: `sbatch rc-slurm.sh`

# Step 1: Download data
./main.py download repo_lists/repos_850stars_2021_09_07_09-03-45.txt all data_850_stars/

# Step 2: Load data into HDF5
./main.py load 850_stars.hdf5 data_850_stars/

# Step 3: Preprocess data
./main.py preprocess 850_stars.hdf5 0

# Step 4: Classify apologies
./main.py classify 850_stars.hdf5 0
