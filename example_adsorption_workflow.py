import os,shutil,glob
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.zeopp import *
import argparse
import time,datetime
import traceback
from deepdiff import DeepDiff

#PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__)) # package root directory
ENV_VAR_LIST = ["RASPA_PARENT_DIR","RASPA_DIR","DYLD_LIBRARY_PATH","LD_LIBRARY_PATH","ZEO_DIR","PACKAGE_DIR"]

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
    output_isotherms_to_csv(args,sim_dir_names)             # STEP 3
    get_geometrical_features(args,cif_names)                # STEP 4

def parse_arguments():
    """
    Parse command-line arguments. Tests are run from here.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    default_directory = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_data"
    parser = argparse.ArgumentParser(description="Simple workflow to calculate gas adsorption in porous crystals.")
    parser.add_argument("-i", "--input-file", default=f"{default_directory}/input.json", help="path to a json input file")
    parser.add_argument("-o", "--output-dir", default=default_directory, help="output directory path")
    
    # Tests
    parser.add_argument("-t", "--test-isotherms-csv", action="store_true", help="run test to create isotherms in CSV format")
    parser.add_argument("-t2","--test-output-json"  , action="store_true", help="run test to create JSON outputs (without isotherms)")

    # Check package and dependencies install paths 
    check_environment_variables(ENV_VAR_LIST)

    ## Test runs start here

    # Create a dictionary mapping flags to test functions
    test_functions = {
        'test_isotherms_csv': run_test_isotherms_csv,
        'test_output_json': run_test_output_json,
    }
    args = parser.parse_args()

    # Execute corresponding tests
    nb_test=0
    for arg_name, test_func in test_functions.items():
        if getattr(args, arg_name):
            # Change the name of the output directory to identify a test
            if args.output_dir == default_directory:
                args.output_dir = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{arg_name}"
            test_func(args)
            nb_test+=1

    # Input file test
    if nb_test == 0 and not os.path.exists(args.input_file):
        print(f"Input file '{args.input_file}' does not exist. Provide a correct input file using -i option.")
        parser.print_help()
        exit(1)

    ## Test runs end here
    return args

def check_environment_variables(env_var_list):
    """
    Check if all required environment variables exist.

    Args:
        ENV_VAR_LIST (list): A list of required environment variable names.

    Returns:
        None: If all required variables exist.
        Exception: Raises an exception if any required variable is missing.
    """
    missing_variables = [var for var in env_var_list if var not in os.environ]
    if missing_variables:
        raise EnvironmentError(f"The following required environment variables are missing: {', '.join(missing_variables)}")

def run_test_isotherms_csv(args):
    """
    Run a test that launch the whole workflow and reconstruct isotherms using CSV output files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running tests ------------------------\n")
    try:
        args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_isotherms_csv/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
        run_simulations(args,sim_dir_names)                     # STEP 2
        reconstruct_isotherms_to_csv(args,sim_dir_names)        # STEP 3
        test_isotherms(args)
        get_geometrical_features(args,cif_names)                # STEP 4
        test_zeopp(args)
        print("Tests succeeded")
    except Exception as e:
        #print(e)
        print(traceback.format_exc())
        print("Tests NOT succeeded")
    print(f"------------------------ End of tests ------------------------\n")
    exit(0)

def run_test_output_json(args):
    """
    Run a test that launch the whole workflow and reconstruct isotherms using JSON output files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running tests ------------------------\n")
    try:
        args.input_file  = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/input.json"
        output_test_file = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/run398c565d.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
        run_simulations(args,sim_dir_names)                     # STEP 2
        export_simulation_result_to_json(args,sim_dir_names,verbose=False)    # STEP 3
        compare_json_subtrees(f"{glob.glob(f'{args.output_dir}/simulations/run*json')[0]}",output_test_file,"results")
        get_geometrical_features(args,cif_names)                # STEP 4
        test_zeopp(args)
        print("Tests succeeded")
    except Exception as e:
        #print(e)
        print(traceback.format_exc())
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
    target_file  = os.path.abspath(f"{os.getenv('PACKAGE_DIR')}/tests/test_zeopp_asa/results_zeopp.csv")
    test_file    = os.path.abspath(f"{args.output_dir}/zeopp_asa/results_zeopp.csv")
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
    target_files  = os.listdir(f"{os.getenv('PACKAGE_DIR')}/tests/test_isotherms_csv/isotherms")
    test_files    = os.listdir(f"{args.output_dir}/isotherms")
    if len(target_files) !=  len(test_files):
        raise Exception("Error : Number of isotherms do not match. Remove ~/tests repository before running tests.")
    else :
        for filename in [ isoname for isoname in test_files if isoname[:3] == 'iso']:
            line_count = 0
            with open(f"{args.output_dir}/isotherms/{filename}", "r") as file:
                for line in file:
                    line_count += 1
            if line_count != 6: # 5 points + header
                raise Exception(f"Error : Number of lines in isotherms files do not match. ")

def compare_json_subtrees(file1, file2, subtree):
    """
    Compare the output json with the reference one in the tests repository given a common key.

    Args:
        file1 (str)  : path to a JSON file.
        file2 (str)  : path to a JSON file.
        subtree (str): first-level key of JSON object. Must be in shared by both JSON files.
    """
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        json_data1 = json.load(f1)
        json_data2 = json.load(f2)

    # Extract the specific subtree from JSON data
    data1_subtree = json_data1.get(subtree, {})
    data2_subtree = json_data2.get(subtree, {})

    # Use DeepDiff to get a dictionary with changed and deleted values
    result = DeepDiff(data1_subtree,data2_subtree)

    # Extract unique key names from the "values_changed" section
    unique_key_names = set()
    for key in result["values_changed"]:
        key_split = key.split("[")[2].split("]")[0]  # Extract the key name between square brackets
        unique_key_names.add(key_split)

    # Return an error if the unique keys are different from the ones expected.
    if unique_key_names != {"'uptake(cm^3 (STP)/cm^3 framework)'","'simkey'"}:
        raise ValueError(f"The '{subtree}' section differs between files {file1} and file {file2}.")

#    print(json.dumps(result, indent=4))
    # Compare the subtrees
    #if data1_subtree != data2_subtree:
    #    raise ValueError(f"The '{subtree}' subtrees are different between files {file1} and file {file2}.")

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
    try:
        os.makedirs(args.output_dir, exist_ok=False)
    except FileExistsError as e :
        print("The existing folder cannot be overwritten!")
        raise(e)
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

def reconstruct_isotherms_to_csv(args,sim_dir_names=None):
    """
    Check and process the results of gas adsorption simulations.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        sim_dir_names (list, optional): List of simulation directory names.
    """
    check_simulations(args.output_dir,sim_dir_names, verbose=False)
    output_isotherms_to_csv(args,sim_dir_names)

def export_simulation_result_to_json(args,sim_dir_names=None,**kwargs):
    """
    Check and process the results of gas adsorption simulations.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        sim_dir_names (list, optional): List of simulation directory names.
    """
    check_simulations(args.output_dir,sim_dir_names,**kwargs)
    output_to_json(args,sim_dir_names,**kwargs)

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
