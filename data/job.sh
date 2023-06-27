#!/bin/bash

for dir in $(find simulations/ -mindepth 1 -type d); do
cd $dir
./run.sh &
cd ../..
done
wait  # Wait for all background jobs to finish
echo "All jobs completed"