#!/usr/bin/env bash

for i in {0..5}; do
    python3 -c "from dataProcessing import preprocess_rawTraj; preprocess_rawTraj(2, 'Lv4', $i)" &
done

for i in {0..5}; do
    python3 -c "from dataProcessing import preprocess_rawTraj; preprocess_rawTraj(3, 'Lv4', $i)" &
done