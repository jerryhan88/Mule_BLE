#!/usr/bin/env bash

for i in {0..5}; do
    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv2', $i)" &
done

for i in {0..5}; do
    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv2', $i)" &
done

for i in {0..5}; do
    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(2, 'Lv4', $i)" &
done

for i in {0..5}; do
    python3 -c "from dataProcessing import aggregate_indiTrajectory; aggregate_indiTrajectory(3, 'Lv4', $i)" &
done