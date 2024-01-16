import glob
from src.parse import *
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.plot import *
from src.zeopp import *
from src.test import *

def main():
    """
    Main function to execute a gas adsorption workflow in porous crystals.

    This workflow comprises the following steps:
    1. Prepare input files.
    2. Run simulations.
    3. Check and process isotherms.def plot_isotherm(isotherm_json,suptitle=None)
    4. Compute geometrical features

    Usage:
        Run the script to execute the workflow based on provided input arguments.
    """
    args = parse_arguments()
    cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
    run_simulations(args,sim_dir_names)                     # STEP 2
    output_isotherms_to_csv(args,sim_dir_names)             # STEP 3
    export_simulation_result_to_json(args,sim_dir_names,verbose=False)
    output_isotherms_to_json(args,f"{glob.glob(f'{args.output_dir}/simulations/run*json')[0]}")
    get_geometrical_features(args,cif_names)                # STEP 4

if __name__ == "__main__":
    main()
