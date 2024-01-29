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
    2. Run simulations with RASPA.
    3. Convert outputs, check errors and process isotherms.
    4. Compute geometrical features with Zeo++.

    Usage:
        Run the script to execute the workflow based on provided input arguments.
    """
    args = parse_arguments()

    # Run simulations
    if args.command == "run": 
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)
        run_simulations(args,sim_dir_names,grid_use=grid_use)                                           # 1.
        output_isotherms_to_json(args,f"{glob.glob(f'{args.output_dir}/simulations/run*json')[0]}")     # 2.
        output_isotherms_to_csv(args,sim_dir_names)                                                     # 3.
        export_simulation_result_to_json(args,sim_dir_names,verbose=False)
        get_geometrical_features(args,cif_names)                                                        # 4.

    # Merge workflow outputs
    elif args.command == "merge":
        merged_json = merge_json(args,args.input_files[0],args.input_files[1])
        nb_isotherms = output_isotherms_to_json(args,f'{args.output_dir}/run_merged.json',
                                                isotherm_filename=f'isotherms.json',
                                                isotherm_dir='./')

if __name__ == "__main__":
    main()
