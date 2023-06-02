from src.wraspa2 import *
from src.input_parser import *
import os,shutil
from ase.io import read
from math import ceil

# Directories
data_dir=os.environ.get("DATA_DIR")
input_dir=os.environ.get("INPUT_DIR")

# Load json file and returns a list of dictionaries with input parameters
l_dict_parameters = parse_json(f"{input_dir}/input.json")

# Create input for RASPA
for i,dict_parameters in enumerate(l_dict_parameters):
    # Create directory
    work_dir = f'{data_dir}/simulations/{"_".join(str(value) if not isinstance(value, list) else "_".join(str(v) for v in value) for value in dict_parameters.values())}'
    os.makedirs(work_dir,exist_ok=True)
    
    # Copy cif
    cif_path = f'{data_dir}/cif/{dict_parameters["structure"]}.cif'
    shutil.copy(cif_path,work_dir)

    # Correct the unit cell to avoid bias from pbc
    atoms = read(cif_path)
    a, b, c, _,_,_ = atoms.cell.cellpar()
    n_a = ceil(24/ a)
    n_b = ceil(24/ b)
    n_c = ceil(24/ c)
    dict_parameters['unit_cells'] = (n_a,n_b,n_c)

    # Create input script
    filename = f'{work_dir}/simulation.input'
    with open(filename,'w') as f:
        string_input = create_script(**dict_parameters)
        f.write(string_input + '\n')
        print(f'Raspa input file {filename} created.')
    
    # Create running file
    create_run_script(path=work_dir,save=True)