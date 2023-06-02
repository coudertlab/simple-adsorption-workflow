#!/bin/bash

export RASPA_DIR=/opt/.conda/envs/simple-adsorption-workflow/lib/python3.9/site-packages/RASPA2/simulations
export DYLD_LIBRARY_PATH=/opt/.conda/envs/simple-adsorption-workflow/lib/python3.9/site-packages/RASPA2/simulations/lib
export LD_LIBRARY_PATH=/opt/.conda/envs/simple-adsorption-workflow/lib/python3.9/site-packages/RASPA2/simulations/lib

$(which simulate) 'simulation.input'