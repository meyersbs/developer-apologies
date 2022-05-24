#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J devaps2

# Standard Out
# Format: -o <file_name>
#SBATCH -o dev_apologies2.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e dev_apologies2.stderr

# Email for Notifications
# Format: --mail-user=<email@email.com>
#SBATCH --mail-user=bsm9339@rit.edu

# States to Trigger Emails
# Format: --mail-type=<BEGIN,END,FAIL,ALL>
#SBATCH --mail-type=ALL

# Job Duration
# Format: -t DD-HH:MM:SS
#SBATCH -t 0-4:00:00

# Job Account, Job Tier, Number of Cores
# Format: -A <account_name> -p <onboard, tier1, tier2, tier3> -n <num_cpus>
#SBATCH -A mistakes -p tier3 -n 1

# Job Memory
# Format: --mem=<num><k,m,g,t> (KB, MB, GB, TB)
#SBATCH --mem=50g

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

echo "Checking JavaScript..."
date
time python3 -u main.py info_data data_850_stars/JavaScript/

date

#echo "Downloading Python..."
#mkdir data_850_stars/Python/
#time ./main.py download repos.txt.Python all data_850_stars/Python/ >> main_output2.txt

# Step 1: Download data
#./main.py download repo_lists/repos_850stars_2021_09_07_09-03-45.txt all data_850_stars/

# Step 2: Load data into HDF5
#./main.py load 850_stars.hdf5 data_850_stars/

# Step 3: Preprocess data
#./main.py preprocess 850_stars.hdf5 0

# Step 4: Classify apologies
#./main.py classify 850_stars.hdf5 0
