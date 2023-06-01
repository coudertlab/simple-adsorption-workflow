from src.wraspa2 import *
import os,shutil
import numpy as np
from ase.io import read
from math import ceil

########################## USER INTERFACE ###########################
PMIN = 10 # 10 Pa
PMAX = 1000000.0 # 10 bar
NPOINTS = 5
ADSORBATE = 'KAXQIL_clean_coremof-2019'
TEMP = 298.15
FF = 'GenericMOFs'
GAS = ['N2','methane']
######################################################################

# Range of variables
pressures = np.linspace(PMIN, PMAX, NPOINTS)
l_dict_var  = [{'molecule_name': molecule_name, 'pressure': pressure} for molecule_name in GAS for pressure in pressures]
dict_input = {'structure':ADSORBATE,
              'temperature':TEMP,
              'unit_cells':(1,1,1),
              'forcefield':FF
}

# Default data directory
data_dir=os.environ.get("DATA_DIR")

# Inputs
for i,dict_var in enumerate(l_dict_var):
    # Create directory
    work_dir = f'{data_dir}/{"_".join(str(value) for value in dict_var.values())}'
    os.makedirs(work_dir,exist_ok=True)
    
    # Copy cif
    cif_path = f'{data_dir}/cif/{dict_input["structure"]}.cif'
    shutil.copy(cif_path,work_dir)

    # Correct the unit cell to avoid bias from pbc
    atoms = read(cif_path)
    a, b, c, _,_,_ = atoms.cell.cellpar()
    n_a = ceil(24/ a)
    n_b = ceil(24/ b)
    n_c = ceil(24/ c)
    dict_input['unit_cells'] = (n_a,n_b,n_c)

    # Create input
    filename = f'{work_dir}/simulation.input'
    with open(filename,'w') as f:
        string_input = create_script(**dict_var,**dict_input)
        f.write(string_input)
        print(f'Raspa input file {filename} created.')
    
    # Create running file
    create_run_script(path=work_dir,save=True)