#!/bin/bash

for dir in $(ls -d simulations/*); do
cd $dir
./run.sh &
cd ../..
done
wait  # Wait for all background jobs to finish
echo "All jobs completed"
