#!/bin/bash
#SBATCH --account=liaison 
#SBATCH --mem=82000      # RAM in MB
#SBATCH --tmp=10000     # local scratch disk in MB
#SBATCH --time=00:10:00
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --cpus-per-task=5
#SBATCH --qos=high

SECONDS=0
echo $1

DIR="/home/tghosh/celavi/"
JOBDIR="/scratch/tghosh/celavi/jobdirsubmit$1"
DIR1="/home/tghosh/celavi/results$1"


rm -r $JOBDIR
mkdir $JOBDIR


rm -r $DIR1
mkdir $DIR1



cd $DIR
cp * $JOBDIR

cd $JOBDIR
date
echo tjisrunningcode

python main.py $1 $3
#python electricityMIX.py $1
#python direct_lca_calculator_automated.py $1 $2
date


duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."

cp eco* $DIR1

cd .. 
#rm -r $JOBDIR
cd $DIR
cp output.$3.$1.$2.txt error.$3.$1.$2.txt $DIR1
rm output.$3.$1.$2.txt error.$3.$1.$2.txt
