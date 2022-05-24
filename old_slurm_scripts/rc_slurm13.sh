#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J devaps14

# Standard Out
# Format: -o <file_name>
#SBATCH -o dev_apologies14.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e dev_apologies14.stderr

# Email for Notifications
# Format: --mail-user=<email@email.com>
#SBATCH --mail-user=bsm9339@rit.edu

# States to Trigger Emails
# Format: --mail-type=<BEGIN,END,FAIL,ALL>
#SBATCH --mail-type=ALL

# Job Duration
# Format: -t DD-HH:MM:SS
#SBATCH -t 3-00:00:00

# Job Account, Job Tier, Number of Cores
# Format: -A <account_name> -p <onboard, tier1, tier2, tier3> -n <num_cpus>
#SBATCH -A mistakes -p tier3 --nodes=1 --ntasks-per-node=32 --cpus-per-task=1

# Job Memory
# Format: --mem=<num><k,m,g,t> (KB, MB, GB, TB)
#SBATCH --mem=200g

# Environment Settings
echo "Loading environment"
#spacktivate mistakes-21091601
spack env activate mistakes-21091601

# Job Script
# To execute this file, simply run: `sbatch rc-slurm.sh`

#echo "Installing pip"
#python3 -m ensurepip --upgrade
#date

#echo "Installing spacy model"
#python3 -m spacy download en_core_web_sm
#date

echo "Doing stuff..."
time python3 -u main.py apology_stats data_aps/ 32
date
