#!/usr/bin/env bash


for repeatNum in {1..30}; do
    python3 -c "from experiments import run_experiments_MA; run_experiments_MA($repeatNum, 'Lv2', N_g=50, N_p=50, N_o=40, p_c=0.5, p_m=0.5)" &
done
