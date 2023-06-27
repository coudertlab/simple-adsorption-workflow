from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
import os,shutil

# Define paths
data_dir  = os.environ.get("DATA_DIR")
input_dir = os.environ.get("INPUT_DIR")
json_path = f"{input_dir}/input.json"


### STEP 1 ###

# Get CIF files from the structures provided in the json files
cif_from_json(json_path)

# Select a subset of structures, e.g. only in one database
structures_subset = get_cifnames(substring="coremof-2019")

# Load json file and returns a list of dictionaries with input parameters
l_dict_parameters = parse_json(json_path,cifnames=structures_subset)

# Create inputs for RASPA for each set of parameters
for i,dict_parameters in enumerate(l_dict_parameters):
    # Get CIF 
    cif_path = f'{data_dir}/cif/{dict_parameters["structure"]}.cif'

    # Correct unit cell to avoid bias from pbc
    dict_parameters["unit_cells"] = get_minimal_unit_cells(cif_path)

    # Create working directory and add CIF file
    work_dir = create_dir(dict_parameters,index_file=f'{data_dir}/simulations/index.csv')
    shutil.copy(cif_path,work_dir)

    # Create input script
    create_script(**dict_parameters,save=True,filename=f'{work_dir}/simulation.input')

    # Create running file
    create_run_script(path=work_dir,save=True)


### STEP 2 ###

# Run the adsorption simulations
create_job_script(path=data_dir)
os.system(f"{data_dir}/job.sh > sim.log 2>&1")

# TODO : call here a function that use the HPC job manager (e.g. SLURM)

# Check RASPA outputs
check_simulations(verbose=False)


### STEP 3 ###

# Extract isotherms and write CSV files
output_isotherms_to_csv()

# Plot isotherms
# e.g. : jupyter notebook plot_isotherms.ipynb
