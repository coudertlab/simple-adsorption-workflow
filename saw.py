import glob
from src.parse import *
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.plot import *
from src.zeopp import *
from src.test import *
from src.gui import *

def main():
    """
    Main function to execute a gas adsorption workflow in porous crystals.

    This workflow comprises the following steps:
    0. Create input file for this workflow.
    1. Prepare input files for all simulation codes.
    2. Run simulations with RASPA.
    3. Convert outputs, check errors and process isotherms.
    4. Compute geometrical features with Zeo++.

    Usage:
        Run the script to execute the workflow based on provided input arguments.
    """
    args = parse_arguments()

    # Run a Graphical User Interface for generating workflow input
    if args.command == "input":
        run_gui_input()

    # Run simulations
    if args.command == "run": 
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)                                  # 1.
        run_simulations(args,sim_dir_names,grid_use=grid_use)                                           # 2.
        output_isotherms_to_csv(args,sim_dir_names)                                                     # 3.
        export_simulation_result_to_json(args,sim_dir_names,verbose=False)
        output_isotherms_to_json(args,f"{glob.glob(f'{args.output_dir}/gcmc/run*json')[0]}")
        get_geometrical_features(args,cif_names)                                                        # 4.

    # Merge workflow outputs
    elif args.command == "merge":
        merged_json = merge_json(args,args.input_files)
        nb_isotherms = output_isotherms_to_json(args,f'{args.output_dir}/run_merged.json',
                                                isotherm_filename=f'isotherms.json',
                                                isotherm_dir=f'{args.output_dir}')

if __name__ == "__main__":
    main()
