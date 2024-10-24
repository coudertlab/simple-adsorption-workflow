# Containerisation via Apptainer

This directory contains minimal required information to build (if needed), get and run an `Apptainer` image of the workflow.

The only prerequisite is to have `Apptainer` installed on your machine.

## (Re)build the image

To rebuild the image, one needs to be located in the present directory and run
```
apptainer build simple-adsorption-workflow.sif simple-adsorption-workflow.def
```

If the image `simple-adsorption-workflow.sif` already exits, you will have to confirm the you want to override it. You can also choose another image name (eg. `simple-adsorption-workflow-new.sif`) if you prefer to keep the current image available.

## Get the image

As opposed to other container solutions like `Docker`, you don't need to install the `.sif` image anyhow, and you are also free to move it to the location you want. Hence, the only thing to do to get the image ready to use is to remember its location (whether it is the present directory and/or another).


## Run a container from the image

To execute the test script from the image, you need to run
```
apptainer run --containall simple-adsorption-workflow.sif
```
which is equivalent to
```
apptainer exec --containall simple-adsorption-workflow.sif python3 /home/app/saw.py -t -o /tmp/tests
```

If you want to access the files produced by the test, you need to bind the output from the container to the host machine (ie. yours). For instance, if you want to gather the output data into the existing `./tests` directory :
```
apptainer exec --containall --bind ./tests:/tmp/tests simple-adsorption-workflow.sif python3 /home/app/saw.py -t -o /tmp/tests
```

Eventually, it is also possible to enter the container as
```
apptainer shell --containall simple-adsorption-workflow.sif
```
From there you can run whatever command you want, and for instance run the example as
```
cd /home/app
python3 /home/app/saw.py -t -o /tmp/tests
```
or directly (from wherever you might be located in the container)
```
python3 /home/app/saw.py -t -o /tmp/tests
```

When you're done, you can exit the container with `exit` or using `Ctrl+D`.
