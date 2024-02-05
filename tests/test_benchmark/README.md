# List of input files for benchmarking

## More than one node in GRICAD needed to be efficient
input_128.json      : an input for 128 GCMC simulations
input_128_test.json : same input with a few MC cycles for testing
input_128_grid.json : same input but using grid calculation

## One node with 32 threads in GRICAD
The following inputs are equivalent to input_128.json but the tasks are divided into 4 independent workflow runs.

input_32-1.json
input_32-2.json
input_32-3.json
input_32-4.json
