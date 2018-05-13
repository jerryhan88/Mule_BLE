#!/usr/bin/env bash


for repeatNum in {1..30}; do
    python3 -c "from experiments import run_experiments_MA; run_experiments_MA($repeatNum, 1, 'Lv4', N_g=50, N_p=100, N_o=80, p_c=0.5, p_m=0.5, randomSolCoice=False)" &
done
