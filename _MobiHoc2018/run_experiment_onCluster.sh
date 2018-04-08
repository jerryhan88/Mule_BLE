#!/usr/bin/env bash
for i in {1..20}; do
    qsub _cluster_run.sh $i
done