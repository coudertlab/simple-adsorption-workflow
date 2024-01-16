import os
import argparse
import time,datetime
from src.test import *

ENV_VAR_LIST = ["RASPA_PARENT_DIR","RASPA_DIR","DYLD_LIBRARY_PATH","LD_LIBRARY_PATH","ZEO_DIR","PACKAGE_DIR"]

def parse_arguments():
    """
    Parse command-line arguments. Tests are run from here.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    default_directory = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_data"
    parser = argparse.ArgumentParser(description="Simple workflow to calculate gas adsorption in porous crystals.")
    parser.add_argument("-i", "--input-file", help="path to a json input file") #default=f"{default_directory}/input.json",
    parser.add_argument("-o", "--output-dir", default=default_directory, help="output directory path")
    
    # Tests
    parser.add_argument("-t", "--test-isotherms-csv", action="store_true", help="run test to create isotherms in CSV format")
    parser.add_argument("-t2","--test-output-json"  , action="store_true", help="run test to create JSON outputs")
    parser.add_argument("-t3","--test-merge-json"   , action="store_true", help="run test to merge json databases")

    # Check package and dependencies install paths 
    check_environment_variables(ENV_VAR_LIST)

    args = parser.parse_args()

    # Create a dictionary mapping flags to test functions
    test_functions = {
        'test_isotherms_csv': run_test_isotherms_csv,
        'test_output_json':   run_test_output_json,
        'test_merge_json':    run_test_merge_json
    }

    # Input file tests
    if (args.input_file is not None and not os.path.exists(args.input_file)):
        print(f"Input file '{args.input_file}' does not exist. Provide a correct input file using -i option.")
        parser.print_help()
        exit(1)
    if args.input_file is not None and not os.path.isabs(args.input_file):
        args.input_file = os.path.abspath(args.input_file)

    # Test with no input files
    if args.input_file == None:
        nb_tests = 0
        for arg_name, test_func in test_functions.items():
            if getattr(args, arg_name):
                nb_tests+=1
        if nb_tests == 0 :
            print(f"Input file not provided. Provide a correct input file using -i option.")
            parser.print_help()
            exit(1)

    # Execute corresponding tests
    for arg_name, test_func in test_functions.items():
        if getattr(args, arg_name):
            # Change the name of the output directory to identify a test
            if args.output_dir == default_directory:
                args.output_dir = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{arg_name}"
            test_func(args)
            nb_test+=1

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
