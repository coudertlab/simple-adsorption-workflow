# simple-adsorption-workflow

## Install

### Environments 
Use a conda environment with python 3.
```bash
conda create -n simple-adsorption-workflow python=3
```

Install requirements in the conda environment
```bash
conda activate simple-adsorption-workflow
pip install -r requirements.txt
```
## User input (JSON file)

```
{
    "parameters":
        {
        "structure":["KAXQIL"],
        "molecule_name": ["N2", "methane"],
        "pressure": [10,1E6],
        "npoints":5,
        "temperature": [298.15]
        }
        ,
    "defaults":
        {
            "unit_cells":[1,1,1],
            "FF":"GenericMOFs"
        }
}
```
In this example, the user can modify parameters and default parameters for RASPA simulations. The required specifications are as follows:

- A six-letter CSD code to identify the material (e.g., `KAXQIL`).
- Selection of a guest molecule using molecule_name (e.g., `methane`).
- Setting the temperature (`temperature`).
- Specifying a pressure range with two values (`pressures`): minimum and maximum pressure.
- Determining the number of points to calculate on the isotherm (`npoints`).

It's important to note that if there are multiple entries for any parameter (e.g., multiple materials), the program will generate simulation folders for each unique combination of parameters.

In this workflow, there are certain restrictions in order to keep the simulations simple and make some assumptions:
- The material must be available in the CoreMOF database, accessible through the MOFXDB database (https://github.com/n8ta/mofdb-client).
- The guest molecule should be a rare gas such as argon (Ar) or xenon (Xe), or it should have a spherical model, like nitrogen (N2), methane (CH4), or sulfur hexafluoride (SF6).
- No electrostatic interactions are considered in the simulations.

These restrictions and assumptions aim to streamline the simulations and simplify the modeling process.

## Workflow outputs

- [x] step 1 : It first returns a set of directories with input and running files for RASPA. 
Default directory : `./data/simulations/`.
Internally, the program will search for the CIF files corresponding to the material name(s) in the MOFXDB database, and will choose the version corresponding to CoRE MOF 2019. 
Default directory : `./data/cif/`

- [ ] step 2 : One need details about the node architecture to launch in parallel all simulations.

- [ ] step 3 : It plots a single isotherm, i.e., a series of (pressure, loading) values and/or check consistency of RASPA outputs.
Default directory : `./data/plots/`.

## To do (Priority)
- [x] Find the cif file(s) in CoRE MOF from its six-letter CSD code
e.g : `python src/download_cif_from_mofxdb.py KAXQIL`

> Note : The search is fetched using the MOFX-DB API, it returns all mofs for which part of the name matches with the input keyword.
- [x] Create a simple workflow in a python script `example-workflow-adsorption.py` based on RASPA2 python wrapper
- [x] Create a json input file and document its format
- [x] Parse the json input in the workflow and check the creation of the input files for RASPA
- [x] Merge the two scripts that download for cif files and include them in the main program `example-workflow-adsorption.py`
- [x] Put the calculation of the minimal supercell in a function.
- [x] Add an option to `src.wraspas2.create_script()` to write the result directly in a file 
- [x] Python notebook for plotting an isotherm
- [x] Add a simple analysis script to check RASPA outputs
- [ ] Add an index file created with the data directories, in order to store the parameters of each simulation
- [ ] Add a script to store isotherms in CSV format

## To do (Optional)

- [x] Optional : Download cif directly from the CSD database. It requires the installation of the CSD API in the environment.
- [ ] Download all cifs files given a material name
- [ ] Add to the workflow a step to select the minimum unit cell in order to avoid the bias from periodic boundary conditions. In practice, one runs a RASPA simulation with all defaults parameters and 0 steps, it then returns some basic information, like the perpendicular lengths which could be used to define the minimal supercell. 
- [ ] Link the workflow ot a job manager that runs a single RASPA simulation for each available CPU (to discuss with SIMAP group).

## For future development

### CSD Python API

> Note : A local installation of the CSD Python API (under license) is needed to go further. One need first to log in at :
https://www.ccdc.cam.ac.uk/support-and-resources/csdsdownloads/
then download the CSD Python API.

The following commands allow to access the CSD API to the current python environment.


Source : https://fd-test.ccdc.cam.ac.uk/media/Documentation/1DBA2AB9-9DC7-423C-8EC9-9291D9C220DA/2020_CSD_Python_API_installation.pdf
* Add the `conda-forge` channel
* Install using the absolute path where the ccdc API is located (downloaded through the entire suite as mentioned above)
* Let your system read the installation paths
```Bash
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install -c <PATH_TO_PYTHON_API> simple-adsorption-workflow #e.g.:/opt/CCDC/Python_API_2022/ccdc_conda_channel simple-adsorption-workflow
conda env config vars set CSDHOME=<PATH_TO_CSD> #e.g.:/opt/CCDC/CSD_2022
```

> NOTE : solving the environment can take a few minutes due to the number of dependencies to satisfy.