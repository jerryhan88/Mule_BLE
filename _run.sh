#!/usr/bin/env bash

#for i in {0..4}; do
#    python3 -c "from dataProcessing import gen_indiTrajectory; gen_indiTrajectory(2, 'Lv2', $i)" &
#done
#
#for i in {0..4}; do
#    python3 -c "from dataProcessing import gen_indiTrajectory; gen_indiTrajectory(3, 'Lv2', $i)" &
#done

#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv2', $i)" &
#done
#
#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv2', $i)" &
#done

#for i in {0..4}; do
#    for j in {9..17}; do
#        python3 -c "from dataProcessing import get_p_kmbl; get_p_kmbl('Lv2', $i, $j)" &
#    done
#done


#python3 -c "from dataProcessing import arrange_M3_muleTraj; arrange_M3_muleTraj('Lv2')" &

#python3 -c "from dataProcessing import arrange_M3_muleTraj; arrange_M3_muleTraj('Lv4')" &


for repeatNum in {1..10}; do
    python3 -c "from experiments import run_experiments_MA; run_experiments_MA($repeatNum, 'Lv4', N_g=50, N_p=100, N_o=80, p_c=0.5, p_m=0.5)" &
done
