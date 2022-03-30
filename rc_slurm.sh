#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J devaps1

# Standard Out
# Format: -o <file_name>
#SBATCH -o devaps1.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e devaps1.stderr

# Email for Notifications
# Format: --mail-user=<email@email.com>
#SBATCH --mail-user=bsm9339@rit.edu

# States to Trigger Emails
# Format: --mail-type=<BEGIN,END,FAIL,ALL>
#SBATCH --mail-type=ALL

# Job Duration
# Format: -t DD-HH:MM:SS
#SBATCH -t 0-05:00:00

# Job Account, Job Tier, Number of Cores
# Format: -A <account_name> -p <onboard, tier1, tier2, tier3> -n <num_cpus>
#SBATCH -A mistakes -p tier3 -n 1

# Job Memory
# Format: --mem=<num><k,m,g,t> (KB, MB, GB, TB)
#SBATCH --mem=200g

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

# Step 0: Test Environment
#echo "Testing environment"
#rm test_output.txt
#time python3 -u main.py info_rate_limit
#time python3 -u tests.py >> test_output.txt

# Step 1: Download data
# echo "Downloading DM..."
# mkdir data_850_stars/DM/
# date
# time python3 -u main.py download repos.txt.DM all data_850_stars/DM/
# echo "Checking DM..."
# time python3 -u main.py info_data data_850_stars/DM/
# date

# Step 2: Load data into HDF5
# echo "Loading DM..."
# date
# time python3 -u main.py load experiment.hdf5 data_850_stars/DM/
# time python3 -u main.py info_hdf5 experiment.hdf5
# date

# Step 3: Preprocess data
# echo "Preprocessing data..."
# date
# time python3 -u main.py preprocess experiment.hdf5 0
# time python3 -u main.py info_hdf5 experiment.hdf5
# date

# Step 4: Classify apologies
# echo "Classifying apologies..."
# date
# time python3 -u main.py classify experiment.hdf5 0
# time python3 -u main.py info_hdf5 experiment.hdf5
# date

# Step X: Prepare data for release
# echo "Preparing data for release..."
# date
# cp -r -v data_850_stars/ zenodo/
# date
# mv zenodo/C++/ zenodo/C-PlusPlus/
# mv zenodo/C#/ zenodo/C-Sharp/
# mv zenodo/F#/ zenodo/F-Sharp/
# date
# time python3 -u scripts/prepare_data_for_zenodo.py zenodo/
# date
# mv zenodo/ 88_million_developer_comments/
# time zip -9 -r 88_million_developer_comments.zip 88_million_developer_comments/
# date
