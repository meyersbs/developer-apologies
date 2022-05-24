#!/bin/bash -l

# Job Name
# Format: -J <job_name>
#SBATCH -J devap51

# Standard Out
# Format: -o <file_name>
#SBATCH -o dev_apologies5.stdout

# Standard Error
# Format: -e <file_name>
#SBATCH -e dev_apologies5.stderr

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
#SBATCH --mem=200g

# Environment Settings
echo "Loading environment"
#spacktivate mistakes-21091601
spack env activate mistakes-21091601

# Job Script
# To execute this file, simply run: `sbatch rc-slurm.sh`
declare -a Files=("co_ABAP.csv" "co_Assembly.csv" "co_C.csv" "co_Clojure.csv" "co_COBOL.csv" "co_CoffeeScript.csv" "co_C-PlusPlus.csv" "co_C-Sharp.csv" "co_CSS.csv" "co_Dart.csv" "co_D.csv" "co_DM.csv" "co_Elixir.csv" "co_Fortran.csv" "co_F-Sharp.csv" "co_Go.csv" "co_Groovy.csv" "co_HTML.csv" "co_Java.csv" "co_JavaScript.csv" "co_Julia.csv" "co_Kotlin.csv" "co_Lisp.csv" "co_Lua.csv" "co_MATLAB.csv" "co_Nim.csv" "co_Objective-C.csv" "co_Pascal.csv" "co_Perl.csv" "co_PHP.csv" "co_PowerShell.csv" "co_Prolog.csv" "co_Python.csv" "co_R.csv" "co_Ruby.csv" "co_Rust.csv" "co_Scala.csv" "co_Scheme.csv" "co_Scratch.csv" "co_Shell.csv" "co_Swift.csv" "co_TSQL.csv" "co_TypeScript.csv" "co_VBScript.csv" "co_VHDL.csv" "is_ABAP.csv" "is_Assembly.csv" "is_C.csv" "is_Clojure.csv" "is_COBOL.csv" "is_CoffeeScript.csv" "is_C-PlusPlus.csv" "is_C-Sharp.csv" "is_CSS.csv" "is_Dart.csv" "is_D.csv" "is_DM.csv" "is_Elixir.csv" "is_Fortran.csv" "is_F-Sharp.csv" "is_Go.csv" "is_Groovy.csv" "is_HTML.csv" "is_Java.csv" "is_JavaScript.csv" "is_Julia.csv" "is_Kotlin.csv" "is_Lisp.csv" "is_Lua.csv" "is_MATLAB.csv" "is_Nim.csv" "is_Objective-C.csv" "is_Pascal.csv" "is_Perl.csv" "is_PHP.csv" "is_PowerShell.csv" "is_Prolog.csv" "is_Python.csv" "is_R.csv" "is_Ruby.csv" "is_Rust.csv" "is_Scala.csv" "is_Scheme.csv" "is_Scratch.csv" "is_Shell.csv" "is_Swift.csv" "is_TSQL.csv" "is_TypeScript.csv" "is_VBScript.csv" "is_VHDL.csv" "pr_ABAP.csv" "pr_Assembly.csv" "pr_C.csv" "pr_Clojure.csv" "pr_COBOL.csv" "pr_CoffeeScript.csv" "pr_C-PlusPlus.csv" "pr_C-Sharp.csv" "pr_CSS.csv" "pr_Dart.csv" "pr_D.csv" "pr_DM.csv" "pr_Elixir.csv" "pr_Fortran.csv" "pr_F-Sharp.csv" "pr_Go.csv" "pr_Groovy.csv" "pr_HTML.csv" "pr_Java.csv" "pr_JavaScript.csv" "pr_Julia.csv" "pr_Kotlin.csv" "pr_Lisp.csv" "pr_Lua.csv" "pr_MATLAB.csv" "pr_Nim.csv" "pr_Objective-C.csv" "pr_Pascal.csv" "pr_Perl.csv" "pr_PHP.csv" "pr_PowerShell.csv" "pr_Prolog.csv" "pr_Python.csv" "pr_R.csv" "pr_Ruby.csv" "pr_Rust.csv" "pr_Scala.csv" "pr_Scheme.csv" "pr_Scratch.csv" "pr_Shell.csv" "pr_Swift.csv" "pr_TSQL.csv" "pr_TypeScript.csv" "pr_VBScript.csv" "pr_VHDL.csv")

#for val in ${Files[@]}; do
#    time python3 -u scripts/prepare_for_zenodo.py data_for_zenodo/$val;
#done

time zip -9 -r zenodo.zip zenodo/


