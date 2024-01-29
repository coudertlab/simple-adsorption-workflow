import os
import argparse
import time,datetime
from src.test import *

ENV_VAR_LIST = ["RASPA_DIR","DYLD_LIBRARY_PATH","LD_LIBRARY_PATH","ZEO_DIR","PACKAGE_DIR"]

def parse_arguments():
    """
    Parse command-line arguments. Tests are run from here.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    default_directory = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_data"
    parser = argparse.ArgumentParser(description="Simple workflow to calculate gas adsorption in porous crystals.")
    subparsers = parser.add_subparsers(dest='command')

    # create the parser for the run command
    parser_run = subparsers.add_parser('run', help='Run molecular simulations.')
    parser_run.add_argument("-i", "--input-file", help="path to a json input file") #default=f"{default_directory}/input.json",
    parser_run.add_argument("-o", "--output-dir", default=default_directory, help="output directory path")
    parser_run.add_argument("-t", "--test-isotherms-csv", action="store_true", help="run test to create isotherms in CSV format")
    parser_run.add_argument("-t2","--test-output-json", action="store_true", help="run test to create JSON outputs")
    parser_run.add_argument("-t4","--test-charges", action="store_true", help="run test to create CIFs with EQeq partial charges")
    parser_run.add_argument("-t5","--test-grids", action="store_true", help="run test with GCMC calculation on grids")

    # create the parser for the merge command
    parser_merge = subparsers.add_parser('merge', help='Merge workflow outputs.')
    parser_merge.add_argument("-i", "--input-files", nargs=2, help="path to two JSON workflow outputs")
    parser_merge.add_argument("-o", "--output-dir", default=default_directory, help="output directory path")
    parser_merge.add_argument("-t3","--test-merge-json", action="store_true", help="run test to merge json databases")

    # Check package and dependencies install paths 
    check_environment_variables(ENV_VAR_LIST)

    # Parse the command-line arguments
    args = parser.parse_args()

    # Create a dictionary mapping flags to test functions
    test_functions = {
        'test_isotherms_csv': run_test_isotherms_csv,
        'test_output_json':   run_test_output_json,
        'test_merge_json':    run_test_merge_json,
        'test_charges'   :    run_test_charges,
        'test_grids'   :      run_test_grids,
    }

    # Execute tests
    for arg_name,value in vars(args).items():
        if arg_name in test_functions.keys() and value==True:
            # Check if input file exists; if no inputs provided, default ones are defined in each test
            try:
                if args.input_file is not None :
                    _check_input_file(parser,args)
            except Exception as e:
                pass
            # Change the name of the output directory to identify a test
            if args.output_dir == default_directory:
                args.output_dir = f"{os.getcwd()}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{arg_name}"
            test_functions[arg_name](args)

    # Check if the input file exists
    _check_input_file(parser,args)

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

def _check_input_file(parser,args):
    # Check input files
    if args.command=='run' and args.input_file is not None and not os.path.exists(args.input_file):
        print(f"Input file '{args.input_file}' does not exist. Provide a correct input file using -i option.")
        parser.print_help()
        exit(1)

    # Change relative paths to absolute paths
    if args.command=='run' and args.input_file is not None:  # run
        args.input_file = os.path.abspath(args.input_file)
    elif args.command=='merge' and args.input_files is not None: # merge
        for i in range(len(args.input_files)):
            args.input_files[i] = os.path.abspath(args.input_files[i])
    else :
        print(f"Input file not provided. Provide a correct input file using -i option.")
        parser.print_help()
        exit(1)