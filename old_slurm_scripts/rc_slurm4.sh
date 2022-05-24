#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J devaps4

# Standard Out
# Format: -o <file_name>
#SBATCH -o dev_apologies4.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e dev_apologies4.stderr

# Email for Notifications
# Format: --mail-user=<email@email.com>
#SBATCH --mail-user=bsm9339@rit.edu

# States to Trigger Emails
# Format: --mail-type=<BEGIN,END,FAIL,ALL>
#SBATCH --mail-type=ALL

# Job Duration
# Format: -t DD-HH:MM:SS
#SBATCH -t 0-6:00:00

# Job Account, Job Tier, Number of Cores
# Format: -A <account_name> -p <onboard, tier1, tier2, tier3> -n <num_cpus>
#SBATCH -A mistakes -p tier3 -n 8

# Job Memory
# Format: --mem=<num><k,m,g,t> (KB, MB, GB, TB)
#SBATCH --mem=300g

# Environment Settings
echo "Loading environment"
#spacktivate mistakes-21091601
spack env activate mistakes-21091601

# Job Script
# To execute this file, simply run: `sbatch rc-slurm.sh`

echo "Installing pip"
python3 -m ensurepip --upgrade

echo "Installing coverage"
pip3 install --user coverage

echo "Installing spacy model"
python3 -m spacy download en_core_web_sm

# Check data
#echo "Checking Java..."
#date
#time python3 -u main.py info_data data_850_stars/Java/

# Preprocess Data
echo "Preprocessing Data..."
date
time python3 -u main.py preprocess experiment.hdf5 0
time python3 -u main.py info_hdf5 experiment.hdf5

date
