import os,glob
from src.output_parser import *
import pandas as pd
import secrets

data_dir = os.environ.get('DATA_DIR')
sim_dir = f'{data_dir}/simulations'
isotherm_dir =  f'{data_dir}/isotherms'
os.makedirs(isotherm_dir,exist_ok=True)

def check_simulations(verbose=False,
                      sim_dir=sim_dir):
    """
    Check the simulations in the specified directory.

    Parameters:
        verbose (bool): Whether to print detailed information. Default is False.
        sim_dir (str): The directory path containing the simulations.

    Returns:
        None
    """
    dir_no_outputs=[]
    dir_many_outputs=[]
    warnings_one_output={}
    errors_one_output={}
    all_dirs = [ name for name in os.listdir(sim_dir) if os.path.isdir(os.path.join(sim_dir, name))]
    for dir in all_dirs:
        l_data_files = glob.glob(f'{sim_dir}/{dir}/Output/System_0/*.data')
        if len(l_data_files)==1:
            filename = l_data_files[0]
            warnings_one_output[filename] = get_lines_with_match('WARNING',filename)
            errors_one_output[filename] = get_lines_with_match('ERROR',filename)
        elif len(l_data_files)>1:
            dir_many_outputs.append(dir)
        else :
            dir_no_outputs.append(dir)

    non_empty_warnings = {key:value for key,value in warnings_one_output.items() if isinstance(value, list) and len(value) > 0}
    non_empty_errors = {key:value for key,value in errors_one_output.items() if isinstance(value, list) and len(value) > 0}
    print(f'{len(all_dirs)} directories found in {sim_dir}:')
    print(f"No       outputs found in {len(dir_no_outputs):5d} directories.")
    if verbose is True : print(dir_no_outputs);print()
    
    print(f"Multiple outputs found in {len(dir_many_outputs):5d} directories.")
    print(f"Warnings         found in {len(non_empty_warnings):5d} directories.")
    if verbose is True : print_dict(non_empty_warnings)
    print(f"Errors           found in {sum(non_empty_errors):5d} directories.")
    if verbose is True : print_dict(non_empty_errors)

def get_lines_with_match(string,filename):
    """
    Get lines from a file that match a given string.

    Parameters:
        string (str): The string to match.
        filename (str): The path of the file to search.

    Returns:
        list: A list of lines that match the string.
    """
    lines = []
    with open(filename, 'r') as file:
        for line in file:
            if string in line:
                lines.append(line.strip())
    return list(set(lines))

def print_dict(d):
    """
    Print a dictionary with each key-value pair on a new line.

    Parameters:
        d (dict): The dictionary to print.

    Returns:
        None
    """
    for key, elements in d.items():
        print(f"{key}:")
        for element in elements:
            print(element)
        print()

def output_isotherms_to_csv(input_path=sim_dir,output_path=isotherm_dir):
    """
    Output isotherms to CSV files.

    Parameters:
        input_path (str): The path to the input directory containing simulation data.
        output_path (str): The path to the output directory for the generated CSV files.

    Returns:
        None
    """
    df = pd.read_csv(f'{sim_dir}/index.csv')
    param_columns = df.columns.difference(['pressure', 'simkey']).to_list()
    grouped = df.groupby(param_columns)

    # Create an index file for isotherms
    df_isot = pd.DataFrame()
    for group, data in grouped:
        simkeys = data["simkey"]
        series_metadata_isot = data.iloc[0].drop('simkey')
        series_metadata_isot["simkeys"] = simkeys.to_numpy()
        series_metadata_isot["isokey"] = secrets.token_hex(6)
        df_isot = df_isot.append(series_metadata_isot)
    df_isot.to_csv(f'{isotherm_dir}/isotherms.csv',index=False)
    print(f' File {isotherm_dir}/isotherms.csv have been created.\nAn isokey have been assigned to each isotherms.\n')
    
    # Create a CSV file for each isotherms
    df_isot = pd.read_csv(f'{isotherm_dir}/isotherms.csv', skipinitialspace=False)
    for index,row in df_isot.iterrows():
        results =[]
        simkeys = eval(row['simkeys'].replace(' ',','))
        paths = [f'{data_dir}/simulations/{simkey}/Output/System_0/' for simkey in simkeys]
        filenames = [os.listdir(path)[0] for path in paths]
        for filename,path in zip(filenames,paths):
            with open(os.path.join(path,filename),'r') as f:
                string_output = f.read() 
            results.append(parse(string_output))
        gas = row['molecule_name']
        uptakes = [[r['Thermo/Baro-stat NHC parameters']['External Pressure'][0],
                    r["Number of molecules"][gas]
                    ["Average loading absolute [cm^3 (STP)/cm^3 framework]"][0]]
                    for r in results]
        df_iso = pd.DataFrame(uptakes,columns=['pressure(bar)','uptake(cm^3 (STP)/cm^3 framework)']).sort_values(by='pressure(bar)')
        df_iso['pressure(bar)'] = df_iso['pressure(bar)']/100000
        file_out = f'{isotherm_dir}/{row["isokey"]}.csv'
        df_iso.to_csv(file_out,index=False)
    print(f'{df_isot.shape[0]} isotherms stored in CSV files.')