from src.wraspa2 import *
import os,shutil

# Create a input script for RASPA
data_dir = os.environ.get('DATA_DIR')
raspa_dir_cifs = f'{os.environ.get("RASPA_PARENT")}/share/raspa/structures/cif'

os.makedirs(f'{data_dir}/input',exist_ok=True)
structure = 'KAXQIL_clean_coremof-2019'
gas = 'CO2'
string_input = create_script(structure=structure,
                             molecule_name=gas,
                             temperature=298.15,
                             pressure=10,
                             unit_cells=(1,1,2),
                             forcefield='GenericMOFs')
name = 'test'
filename = f'{data_dir}/input/{name}.input'
with open(filename,'w') as f:
    f.write(string_input)

# Copy the cif file in the directory visible by RASPA
shutil.copy(f'{data_dir}/cif/{structure}.cif',raspa_dir_cifs)

# Run the script
os.chdir('./data')
result = run_script(filename, structure=None, stream=False)
sys.exit()
# Parse output
uptakes = result["Number of molecules"][gas]["Average loading absolute [cm^3 (STP)/cm^3 framework]"][0]
print(uptakes)