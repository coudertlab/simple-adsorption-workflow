from src.wraspa2 import *
from src.input_parser import *
import os,shutil

# Define paths
data_dir  = os.environ.get("DATA_DIR")
input_dir = os.environ.get("INPUT_DIR")
json_path = f"{input_dir}/input.json"

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
    #work_dir = f'{data_dir}/simulations/{"_".join(str(value) if not isinstance(value, list) else "_".join(str(v) for v in value) for value in dict_parameters.values())}'
    #os.makedirs(work_dir,exist_ok=True)
    work_dir = create_dir(dict_parameters,index_file=f'{data_dir}/simulations/index.csv')
    shutil.copy(cif_path,work_dir)

    # Create input script
    create_script(**dict_parameters,save=True,filename=f'{work_dir}/simulation.input')

    # Create running file
    create_run_script(path=work_dir,save=True)

# TODO : write below a code to launch the calculations depending on the node architecture

# Check RASPA outputs
from src.convert_data import *
check_simulations(verbose=False)

# Extract isotherms and write CSV files
#convert_to_csv(path=f'{data_dir}/simulations')

# TODO : write below a code to generate isotherms in a CSV format
# Plot example : see notebook example_plot.ipynb