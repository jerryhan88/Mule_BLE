#!/usr/bin/env bash

for i in {0..4}; do
    python3 -c "from dataProcessing import gen_indiTrajectory; gen_indiTrajectory(2, 'Lv2', $i)" &
done

for i in {0..4}; do
    python3 -c "from dataProcessing import gen_indiTrajectory; gen_indiTrajectory(3, 'Lv2', $i)" &
done


#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv4', $i)" &
#done
#
#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv4', $i)" &
#done


#for i in {0..4}; do
#    for j in {9..17}; do
#        python3 -c "from dataProcessing import get_mTraj; get_mTraj('Lv4', $i, $j)" &
#    done
#done


#python3 -c "from dataProcessing import arrange_M3_muleTraj; arrange_M3_muleTraj('Lv2')" &

#python3 -c "from dataProcessing import arrange_M3_muleTraj; arrange_M3_muleTraj('Lv4')" &
