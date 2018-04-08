#! /bin/sh

# 2 common options. You can leave these alone:-
#$ -j y
#$ -cwd
#$ -m e
#$ -M ckhan.2015@phdis.smu.edu.sg
##$ -q "express.q"
##$ -q "short.q"
#$ -q "long.q"

source ~/.bashrc
cd /scratch/ckhan.2015/research/Mule_BLE

repeatNum=$1

python3 -c "from experiments1 import run_experiments_MA; run_experiments_MA(0, 'Lv4', N_g=50, N_p=50, N_o=40, p_c=0.5, p_m=0.5)"

#python3 -c "from experiments1 import run_experiments_MA; run_experiments_MA($repeatNum, N_g=50, N_p=50, N_o=40, p_c=0.5, p_m=0.5)"