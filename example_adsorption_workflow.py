import os,shutil
import sys
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.zeopp import *
import argparse
import time

def main():
    """
    Main function to execute a gas adsorption workflow in porous crystals.

    This workflow comprises the following steps:
    1. Prepare input files.
    2. Run simulations.
    3. Check and process isotherms.

    Usage:
        Run the script to execute the workflow based on provided input arguments.
    """
    args = parse_arguments()
    cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
    run_simulations(args,sim_dir_names)                     # STEP 2
    check_isotherms(args,sim_dir_names)                     # STEP 3
    get_geometrical_features(args,cif_names)                # STEP 4

def parse_arguments():
    """
    Parse command-line arguments. Tests are run from here.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Simple workflow to calculate gas adsorption in porous crystals.")
    parser.add_argument("-t","--tests", action="store_true", help="run tests")
    parser.add_argument("-o", "--output-dir", default=f"{os.environ.get('HOME')}/data", help="output directory path")
    parser.add_argument("-i", "--input-file", default=f"{os.environ.get('HOME')}/data/input.json", help="full path of a json input file")

    args = parser.parse_args()
    if args.tests:
        run_test(args)
    elif not os.path.exists(args.input_file):
        print(f"Input file '{args.input_file}' does not exist. Provide a correct input file using -i option.")
        parser.print_help()
        exit(1)
    return args

def run_test(args):
    """
    Run test cases and verify the gas adsorption workflow.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    if args.output_dir ==  f"{os.environ.get('HOME')}/data":
        args.output_dir = f"{os.environ.get('HOME')}/tests"
        args.input_file      = f"{os.environ.get('PACKAGE')}/tests/test_isotherms/input.json"
    args.input_file      = f"{os.environ.get('PACKAGE')}/tests/test_isotherms/input.json"
    print(f"------------------------ Running tests ------------------------\n")
    try:
        cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
        run_simulations(args,sim_dir_names)          # STEP 2
        check_isotherms(args,sim_dir_names)          # STEP 3
        test_isotherms(args)
        get_geometrical_features(args,cif_names)               # STEP 4
        test_zeopp(args)
        print("Tests succeeded")
    except Exception as e:
        print(e)
        print("Tests NOT succeeded")
    print(f"------------------------ End of tests ------------------------\n")
    exit(0)

def test_zeopp(args):
    """
    Count the number of lines in the output csv files with surface 
    areas and compare to the targeted values.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    target_file  = os.path.abspath(f"{os.environ.get('PACKAGE')}/tests/test_zeopp_asa/results_zeopp.csv")
    test_file    = os.path.abspath(f"{os.environ.get('HOME')}/tests/zeopp_asa/results_zeopp.csv")
    with open(target_file, 'rb') as file1, open(test_file, 'rb') as file2:
        content1 = file1.read()
        content2 = file2.read()
        if content1 != content2:
            raise Exception("Error : Results with Zeo++ test are different from expected.")

def test_isotherms(args):
    """
    Count the number of isotherms and the number of lines in each file
    and compare to the targeted values.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    target_files  = os.listdir(f"{os.environ.get('PACKAGE')}/tests/test_isotherms/isotherms")
    test_files    = os.listdir(f"{os.environ.get('HOME')}/tests/isotherms")
    if len(target_files) !=  len(test_files):
        raise Exception("Error : Number of isotherms do not match. Remove ~/tests repository before running tests.")
    else :
        for filename in [ isoname for isoname in test_files if isoname[:3] == 'iso']:
            line_count = 0
            with open(f"{os.environ.get('HOME')}/tests/isotherms/{filename}", "r") as file:
                for line in file:
                    line_count += 1
            if line_count != 6: # 5 points + header
                raise Exception(f"Error : Number of lines in isotherms files do not match. ")

def prepare_input_files(args):
    """
    Prepare input files for gas adsorption simulations and generate simulation directories.

    This function creates the necessary input files and directories for running gas adsorption simulations
    using RASPA. It performs the following steps:
    1. Creates the output directory if it doesn't exist.
    2. Retrieves CIF files from the structures provided in the JSON input file.
    3. Parses the JSON input file and extracts input parameters for simulations.
    4. Generates simulation directories, copies CIF files, and creates input scripts for RASPA.
    5. Creates job scripts for running simulations on multiple CPUs.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        list: List of simulation directory names.
    """
    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Storing data in {args.output_dir}\n")

    # Get CIF files from the structures provided in the JSON file
    cif_names = cif_from_json(args.input_file, args.output_dir,
                             database='mofxdb', substring="coremof-2019",
                             verbose=False)

    # Parse the JSON file and extract input parameters
    l_dict_parameters = parse_json(args.input_file, cifnames=cif_names)

    # Create inputs for RASPA for each set of parameters
    sim_dir_names = []
    for dict_parameters in l_dict_parameters:
        # Get CIF name
        cif_path_filename = f'{args.output_dir}/cif/{dict_parameters["structure"]}.cif'

        # Correct unit cell to avoid bias from periodic boundary conditions
        dict_parameters["unit_cells"] = get_minimal_unit_cells(cif_path_filename)

        # Create a working directory, add CIF file, and generate input script
        work_dir = create_dir(dict_parameters, args.output_dir)
        sim_dir_names.append(dict_parameters["simkey"])
        shutil.copy(cif_path_filename, work_dir)
        create_script(**dict_parameters, save=True, filename=f'{work_dir}/simulation.input')
        create_run_script(path=work_dir, save=True)

    # Create a job script for all simulations (each using 1 CPU)
    create_job_script(args.output_dir, sim_dir_names)

    return cif_names, sim_dir_names

def run_simulations(args,sim_dir_names):
    """
    Run gas adsorption simulations using prepared input files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        sim_dir_names (list): List of simulation directory names.
    """
    print(f"Running simulations on {len(sim_dir_names)} cpus ...")
    os.chdir(args.output_dir)
    start_time = time.time()
    os.system("./job.sh > sim.log 2>&1")
    execution_time = time.time()- start_time
    print(f"Simulations completed in {execution_time:.2f} seconds.")

def check_isotherms(args,sim_dir_names=None):
    """
    Check and process the results of gas adsorption simulations.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        sim_dir_names (list, optional): List of simulation directory names.
    """
    check_simulations(args.output_dir,sim_dir_names, verbose=False)
    output_isotherms_to_csv(args.output_dir,sim_dir_names,args.tests)

def get_geometrical_features(args,cif_names):
    """
    Calculate geometrical features of the porous crystals using Zeo++.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    run_zeopp_asa(args.output_dir,
                cif_files=[f'{args.output_dir}/cif/{structure}.cif' for structure in cif_names])

if __name__ == "__main__":
    main()
