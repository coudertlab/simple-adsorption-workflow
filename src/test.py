from deepdiff import DeepDiff
import traceback
import os,glob,json
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.zeopp import *
from src.plot import *
from src.charge import *
from pathlib import Path

def run_test_isotherms_csv(args):
    """
    Run a test that launch the whole workflow and reconstruct isotherms using CSV output files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        if not args.input_file : args.input_file = f"{os.getenv('PACKAGE_DIR')}/tests/test_isotherms_csv/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)
        run_simulations(args,sim_dir_names)
        reconstruct_isotherms_to_csv(args.output_dir,sim_dir_names)
        test_isotherms(args)
        get_geometrical_features(args,cif_names)
        test_zeopp(args)
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)

def run_test_output_json(args):
    """
    Run a test that launch the whole workflow and reconstruct isotherms using JSON output files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        if not args.input_file : args.input_file  = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/input.json"
        output_test_file = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/runtest.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)
        run_simulations(args,sim_dir_names)
        reconstruct_isotherms_to_csv(args.output_dir,sim_dir_names)
        export_simulation_result_to_json(args.input_file,args.output_dir,sim_dir_names,verbose=False)
        output_isotherms_to_json(args.output_dir,f"{glob.glob(f'{args.output_dir}/gcmc/run*json')[0]}")
        compare_csv_json(args)
        compare_json_subtrees(f"{glob.glob(f'{args.output_dir}/gcmc/run*json')[0]}",output_test_file,"results")
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)

def run_test_merge_json(args):
    """
    Run a test that merge two json from independent workflow runs and reconstruct isotherms from :
    - the first output
    - the second output
    - the merged output

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        root_test_dir = f"{os.getenv('PACKAGE_DIR')}/tests/test_merge_json"
        json_files =  glob.glob(f"{root_test_dir}/gcmc/*")
        merged_json = merge_json(args.output_dir,json_files)
        jsons = {f'Isotherms from json {i+1}': file for i,file in enumerate(json_files)}
        jsons['Isotherms from merged JSON'] = merged_json
        nb_isotherms_sum = 0
        for suptitle,file in jsons.items():
            basename = os.path.basename(file)
            nb_isotherms = output_isotherms_to_json(args.output_dir,file,isotherm_filename=f'isotherms_{basename}')
            if suptitle != 'Isotherms from merged JSON':
                nb_isotherms_sum+=nb_isotherms
            plot_isotherm(f'{root_test_dir}/isotherms/isotherms/isotherms_{basename}',suptitle=suptitle,block=True) # set block to True to keep opened each plot for visual check
        assert nb_isotherms == 5,f'The number of isotherms after the merge must be 5.'
        print(f"Found {nb_isotherms} isotherms (< {nb_isotherms_sum}  = total number of isotherms in separated JSON files.)")
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
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
    result = DeepDiff(data1_subtree,data2_subtree,)

    # Extract unique keywords from the "values_changed" section
    unique_key_names = set()
    for key in result["values_changed"]:
        key_split = key.split("[")[2].split("]")[0]  # Extract the key name between square brackets
        unique_key_names.add(key_split)

    # Return an error if keywords differ from the expected set
    expected_features_set = {"'uptake(cm^3 (STP)/cm^3 framework)'","'simkey'"} 
    if unique_key_names != expected_features_set:
        print(f"\nKeywords which differs from the expected set: {unique_key_names.difference(expected_features_set)}\n")
        raise ValueError(f"The '{subtree}' section differs between files {file1} and file {file2}.")

def compare_csv_json(args):
    """
    Check that teh number of isotherms in CSV formats matches with the number of isotherms listed in the JSON output.
    """
    df = pd.read_csv(f'{args.output_dir}/isotherms/index.csv')
    n_csv = df.shape[0]
    with open((f'{args.output_dir}/isotherms/isotherms.json'), 'r') as json_file:
        data = json.load(json_file)
    n_json = len([isot for isot in data["isotherms"]])
    assert n_json == n_csv, "Test error: The number of isotherms in CSV and JSON outputs must be equal."

def run_test_charges(args):
    """
    Run a test that parse the JSON file, and run EQeq calculations on all structures.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        if not args.input_file : args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_charges/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args,verbose=True)
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)

def run_test_charges_pacmof(args):
    """
    Run a test that parse the JSON file, and run the PACMOF2 code to generate a set of partial charges.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        if not args.input_file : args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_charges_pacmof/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args,verbose=True)
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)
    
def run_test_grids(args):
    """
    Run a test that parse the JSON file, generate input files for creating grid in RASPA,
    compute the grid and return .

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        if not args.input_file : args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_grids/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)
        run_simulations(args,sim_dir_names,grid_use = grid_use)
        #export_simulation_result_to_json(args,sim_dir_names,verbose=False)
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)
    
def run_test_cif_local_directory(args):
    """
    Run a test that parse the JSON file with a parameter `database='local'` to load CIF files from a local directory (any directory and subdirectory in the current path).

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running test ---------------------------\n")
    try:
        input_directory_test = f"{os.getenv('PACKAGE_DIR')}/tests/test_cif_local_directory/"
        shutil.copytree(f"{input_directory_test}/cif",Path.cwd() / 'cif')
        args.input_file = f"{input_directory_test}/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names, grid_use = prepare_input_files(args)
        run_simulations(args,sim_dir_names,grid_use = grid_use)
        #export_simulation_result_to_json(args,sim_dir_names,verbose=False)
        print("\nTest successful :)")
    except Exception as e:
        print(traceback.format_exc())
        print("\nTest NOT successful :(")
    print(f"------------------------ End of the test ------------------------\n")
    exit(0)