#!/usr/bin/env bash

#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv2', $i)" &
#done
#
#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv4', $i)" &
#done

#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv2', $i)" &
#done
#
#for i in {0..4}; do
#    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv4', $i)" &
#done

for i in {0..4}; do
    for j in {9..17}; do
        python3 -c "from dataProcessing import get_mTraj; get_mTraj(3, 'Lv2', $i, $j)" &
    done
done
