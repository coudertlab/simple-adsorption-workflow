from deepdiff import DeepDiff
import traceback
import os
from src.wraspa2 import *
from src.input_parser import *
from src.convert_data import *
from src.zeopp import *
from src.plot import *
from src.charge import *

def run_test_isotherms_csv(args):
    """
    Run a test that launch the whole workflow and reconstruct isotherms using CSV output files.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print(f"------------------------ Running tests ------------------------\n")
    try:
        if not args.input_file : args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_isotherms_csv/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
        run_simulations(args,sim_dir_names)                     # STEP 2
        reconstruct_isotherms_to_csv(args,sim_dir_names)        # STEP 3
        test_isotherms(args)
        get_geometrical_features(args,cif_names)                # STEP 4
        test_zeopp(args)
        print("Tests succeeded")
    except Exception as e:
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
        if not args.input_file : args.input_file  = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/input.json"
        output_test_file = f"{os.getenv('PACKAGE_DIR')}/tests/test_output_json/run398c565d.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names = prepare_input_files(args)    # STEP 1
        run_simulations(args,sim_dir_names)                     # STEP 2
        export_simulation_result_to_json(args,sim_dir_names,verbose=False)    # STEP 3
        compare_json_subtrees(f"{glob.glob(f'{args.output_dir}/simulations/run*json')[0]}",output_test_file,"results")
        output_isotherms_to_json(args,f"{glob.glob(f'{args.output_dir}/simulations/run*json')[0]}")
        print("Tests succeeded")
    except Exception as e:
        print(traceback.format_exc())
        print("Tests NOT succeeded")
    print(f"------------------------ End of tests ------------------------\n")
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
    print(f"------------------------ Running tests ------------------------\n")
    try:
        json1,json2 =  glob.glob(f"{os.getenv('PACKAGE_DIR')}/tests/test_merge_json/simulations/*")
        merged_json = merge_json(args,json1,json2)
        jsons = {'isotherms from json 1':json1,'isotherms from json 2':json2, 'Isotherms from merged JSON':merged_json}
        for suptitle,file in jsons.items():
            basename = os.path.basename(file)
            nb_isotherms = output_isotherms_to_json(args,file,isotherm_filename=f'isotherms_{basename}')
            plot_isotherm(f'{args.output_dir}/isotherms/isotherms_{basename}',suptitle=suptitle)
        assert nb_isotherms == 10,'The number of isotherms after the merge must be 10.'
        print("Found 10 isotherms (< 12  = total number of isotherms in separated JSON files.)")
        print("Tests succeeded")
    except Exception as e:
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
        print(unique_key_names)
        raise ValueError(f"The '{subtree}' section differs between files {file1} and file {file2}.")

def run_test_charges(args):
    """
    Run a test that parse the JSON file, and run EQeq calculations on all structures.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """

    print(f"------------------------ Running tests ------------------------\n")
    try:
        if not args.input_file : args.input_file      = f"{os.getenv('PACKAGE_DIR')}/tests/test_isotherms_csv/input.json"
        print(f"Reading input file in {args.input_file}")
        cif_names, sim_dir_names = prepare_input_files(args)
        run_EQeq(args.output_dir+'/cif')
        print("Tests succeeded")
    except Exception as e:
        print(traceback.format_exc())
        print("Tests NOT succeeded")
    print(f"------------------------ End of tests ------------------------\n")
    exit(0)