import json
from itertools import product
import sys
import os,glob
from mofdb_client import fetch
from ase.io import read
from math import ceil
import pandas as pd
import secrets
import warnings
from src.charge import *
import numpy as np
from pathlib import Path
import shutil
import fnmatch

# Careful with these lines, since bugs might appear with C++ shared library call
#try:
#    from ccdc import io
#    from ccdc.search import TextNumericSearch
#except Exception as e:
#    print(e)

# Allowed keywords for charge method
CHARGE_METHOD = ["EQeq","None","",None,"QMOF","pacmof2"]

def parse_json_to_list(filename):#,cifnames):
    """
    Parse a JSON file containing default values and parameters, and generate combinations of parameter values.

    Args:
        filename (str): The name of the JSON file to parse.
        cifnames (list): A subset of CIF filenames (useful when we want select 
                         the CIFs post-processed in the workflow, e.g. with charges)

    Returns:
        l_dict_parameters (list): A list of dictionaries, each representing a combination of parameter values.
    """

    with open(filename, 'r') as f:
        data = json.load(f)
    dict_default = data["defaults"]
    dict_parameters = data["parameters"]

    # Check if 'pressure' has exactly two values
    if len(dict_parameters['pressure']) != 2:
        raise ValueError("Invalid number of pressure values. Expected 2.")
    Pmin, Pmax = dict_parameters["pressure"]
    npoints = dict_parameters["npoints"]
    dict_parameters["pressure"] = [Pmin + (Pmax - Pmin) * i / (npoints - 1) for i in range(npoints)]

    # Check consistency of RASPA inputs
    check_input_raspa(dict_parameters["molecule_name"])

    # Generate combinations
    combinations = list(product(*(value if isinstance(value, list) else [value] for value in dict_parameters.values())))

    # Create dictionaries for each combination
    l_dict_parameters = []
    for combo in combinations:
        dictionary = {key: value for key, value in zip(dict_parameters.keys(), combo)}
        dictionary.update(data['defaults'])
        # Add defaults parameters for RASPA
        for key,value in dict_default.items():
            dictionary[key] = value
        l_dict_parameters.append(dictionary)
    return l_dict_parameters

def check_input_raspa(molecule_name_list):
    '''
    Look for the presence of parameters for the molecule in the ExampleDefinitions force field.
    '''
    basenames = ([os.path.basename(filename).split('.def')[0] for filename in os.listdir(f"{os.environ.get('RASPA_DIR')}/share/raspa/molecules/ExampleDefinitions/")])
    for molecule_name in molecule_name_list: 
        assert molecule_name in basenames, f'The molecule {molecule_name} is not found in ExampleDefinitions.'

def parse_json_to_dict(filename):
    """
    Parse a JSON file containing specific workflow parameters and defaut parameters for the other programs.

    Args:
        filename (str): The name of the JSON file to parse.
    Returns:
        list: A list of dictionaries, each representing a combination of parameter values.
    """

    with open(filename, 'r') as f:
        data = json.load(f)
    data_flat = data["parameters"]
    data_flat.update(data["defaults"])
    return data_flat

def get_cifs(l_dict_parameters, data_dir, database='mofxdb', verbose=False,**kwargs):
    """
    Generate CIF files from a JSON file containing structures.

    Args:
        l_dict_parameters (list) : a list of dictionaries containing each set of simulation parameters.
        data_dir (str) : the root path for outputs
        database (str, optional): Database name. Default is 'mofxdb'. Possible values : {'moxdb','local'}.
        **kwargs: Additional keyword arguments passed to cif_from_mofxdb.

    Raises:
        ValueError: If an invalid database name is provided.

    Returns:
        cifnames_database (list) : a list of structure names from the database
        l_dict_parameters (list) : a list of dictionaries containing each the set of simulation parameters
    """

    # Create directory where CIF files are stored
    cif_dir = f"{data_dir}/cif/"
    os.makedirs(cif_dir,exist_ok=True)

    # Get all CIF names and assign charge method if not
    structures = []
    for dict_params in l_dict_parameters:
        structures.append(dict_params["structure"])
        try :
            _ = dict_params["charge_method"]
        except Exception as e:
            dict_params["charge_method"]=None
    structures = set(structures)

    # Download CIF files from databases
    cifnames_nested = []
    for structure in structures:
        if database == 'mofxdb':
            cifnames_nested.append(cif_from_mofxdb(structure, data_dir, **kwargs))
        elif database == 'local':
            cifnames_nested.append(cif_from_local_directory(structure, data_dir))
        elif database == 'mixed':
            local_cifs = []
            mofxdb_cifs = []
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                local_cifs = cif_from_local_directory(structure, data_dir)
                mofxdb_cifs = cif_from_mofxdb(structure, data_dir, **kwargs)
            if not local_cifs and not mofxdb_cifs:
                warnings.warn(f"{structure} not found in both local directory and MOFXDB.")
            # By default we take the local CIFs
            if local_cifs:
                cifnames_nested.append(local_cifs)
            else:
                cifnames_nested.append(mofxdb_cifs)
        else:
            raise ValueError("Invalid database name. Expected 'mofxdb', 'local', or 'mixed'.")
    # Flat lists
    cifnames_database = [item for sublist in cifnames_nested for item in sublist]

    # Stdout
    print(f"\nCIF files fetched from {database} : ")
    for cif in [cif for cif in _get_basename(cifnames_database)]:
        print(cif)

    # Charge assignment : first get all charge methods, then compute charges if charges are needed
    charge_methods = []
    for dict_params in l_dict_parameters:
        charge_methods.append(dict_params["charge_method"])
    charge_methods = set(charge_methods)

    cifnames_modified = cifnames_database
    for charge_method in charge_methods :
        if charge_method not in ["None","",None]:
            cifnames_modified = cif_with_charges(cif_dir=cif_dir,cifnames_input=cifnames_database,
                                 method=charge_method,verbose=verbose)

    # Assign the correct CIF file depending on the charge method
    for dict_params in l_dict_parameters:
        charge_method = dict_params["charge_method"]
        structure = dict_params["structure"]
        if charge_method not in ["None","",None]:
            # CIF name from charge assignment
            dict_params["structure"] = _get_cifname_matching(cif_dir,
                                                             f"*{structure}*{charge_method}*.cif")
        else:
            # CIF name from the original database
            exclude_list = [el for el in CHARGE_METHOD if el not in ["None","",None]]
            exclude_list.append("openbabel")
            dict_params["structure"] = _get_cifname_matching(cif_dir,f"*{structure}*.cif",
                                                             exclude_pattern=exclude_list)
    cifnames_database = _get_basename(cifnames_database)
    cifnames_modified = _get_basename(cifnames_modified)
    return cifnames_modified,l_dict_parameters

def _get_cifname_matching(cif_dir, pattern, exclude_pattern=None):
    """
    Retrieve a single CIF filename from cif_dir that matches the given pattern 
    applied only to the filename (not the directory path). Optionally exclude 
    filenames containing exclude_pattern(s).
    
    Args:
        cif_dir (str): Directory containing CIF files.
        pattern (str): Glob pattern to match filenames.
        exclude_pattern (str or list, optional): Pattern(s) to exclude from matching.
    
    Returns:
        str: The matched CIF filename.
    
    Raises:
        AssertionError: If no files match or if multiple files match the criteria.
    """
    # List all files in the directory
    all_files = glob.glob(os.path.join(cif_dir, '*'))
    
    # Filter files where the basename matches the pattern
    cifs_matched = [
        f for f in all_files 
        if fnmatch.fnmatch(os.path.basename(f), pattern)
    ]
    
    # Apply exclusion patterns if provided
    if exclude_pattern is not None:
        if isinstance(exclude_pattern, str):
            exclude_patterns = [exclude_pattern]
        elif isinstance(exclude_pattern, list):
            exclude_patterns = exclude_pattern
        else:
            raise TypeError("exclude_pattern must be a string or a list of strings")
        
        cifs_matched = [
            f for f in cifs_matched 
            if not any(excl in os.path.basename(f) for excl in exclude_patterns)
        ]
    
    # Ensure exactly one match is found
    assert len(cifs_matched) == 1, (
        f"CIF name with pattern '{pattern}'"
        + (f" and exclusion pattern(s) {exclude_patterns}" if exclude_pattern else "")
        + " does not exist or is not unique"
    )
    
    # Extract and return the basename of the matched file
    return _get_basename(cifs_matched)[0]

def _get_basename(filenames):
    '''
    Get basename of a list of files without path and extension.
    '''
    return [os.path.splitext(os.path.basename(path))[0] for path in filenames]

def cif_from_mofxdb(structure, data_dir, substring = "coremof-2019", verbose=False):
    """
    Generate CIF files from MOFX-DB based on a given structure name.

    Args:
        structure (str): Name of the structure.
        data_dir (str): Parent directory.

    Returns:
        cifnames (list) : A list of cif names with absolute path fetched from the database.
    """

    cifnames = []
    for mof in fetch(name=structure):
        cifname = os.path.join(f"{data_dir}/cif/{mof.name}_{mof.database.lower().replace(' ', '-')}.cif")

        # Filter using original database key
        if substring in cifname:
            with open(cifname, 'w') as f:
                print(mof.cif, file=f)
                if verbose : print(f'Cif has been written in {cifname}.')
            cifnames.append(cifname)

            # Indicate the number of isotherms found in MOFXDB (can be used for reproducibility purposes)
            if verbose:
                print(f"Mof with name {mof.name} from {mof.database} has already {len(mof.isotherms)} isotherms stored in MOFX-DB.")

    # Add a warning for the structure has no entry in the structural databases
    if len(cifnames)==0:
        warnings.warn(f"{structure} not found in MOFXDB subset {substring}")

    return cifnames

def cif_with_charges(cif_dir,cifnames_input,method='EQeq',verbose=False):

    '''
    Returns only the subset of cif filenames containing partial charges.

    Args:
        cif_dir (str): The absolute path of the directory where CIFs are stored
        method (str) : A keyword to select the charge assignment method;
                        possible values : 'EQeq',"pacmof2"
    Returns:
        cifnames (list): A list CIF absolute filenames
    '''
    if method == 'EQeq':
        cifnames = run_EQeq(cif_dir,cifnames_input,verbose=verbose)
    elif method == 'QMOF':
        cifnames = fetch_QMOF(cifnames_input,verbose=verbose)
    elif method == 'pacmof2':
        cifnames = run_pacmof(cif_dir,cifnames_input,verbose=verbose)
    else:
        raise ValueError(f'Invalid charge method keyword. Expected values : {[el for el in CHARGE_METHOD]}')
    return cifnames

def cif_from_local_directory(structure, data_dir):
    """Use CIF files provided by the user in a local path

    Args:
        structure (str): Name of the structure (CIF basename).
        data_dir (str): Parent directory.
    """
    current_dir = Path.cwd()
    target_directory = f"{data_dir}/cif"
    
    # Search for the file in the 'cifs' subdirectory
    cifs_dir = current_dir / 'cif'
    found_files = list(cifs_dir.rglob(f'{structure}.cif'))

    # Raise warning if structure file is not found
    if not found_files:
        warn_message = f"{structure}.cif does not exist in the directory ./cif"
        warnings.warn(warn_message)
    
    # Copy the file into the output directory
    target_cifnames = []
    for file_path in found_files:
        try:
            # Define the destination path
            destination = f'{target_directory}/{file_path.name}'
            shutil.copy2(file_path, destination)  # copy2 preserves metadata
            target_cifnames.append(destination)
        except Exception as e:
            warnings.warn(f"Failed to copy '{file_path}': {e}")
    return target_cifnames

def get_minimal_unit_cells(cif_path_filename,cutoff=12):
    """
    Get the minimal supercell to avoid pbc artifacts in energy calculations.
    By default, the cutoff is 12 Angstroms. 
    
    TODO : change the cutoff if specified in JSON input. 
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, message="crystal system 'triclinic' is not interpreted")
        atoms = read(cif_path_filename)
    a, b, c, alpha, beta, gamma = atoms.cell.cellpar()
    mat = mat_from_parameters(a, b, c, alpha, beta, gamma)
    
    cx,cy,cz = perpendicular_lengths(mat[0],mat[1],mat[2])
    nx = ceil(cutoff*2/ cx)
    ny = ceil(cutoff*2/ cy)
    nz = ceil(cutoff*2/ cz)
    return nx,ny,nz

def mat_from_parameters(a, b, c, alpha, beta, gamma):
    cos_alpha = np.cos(np.radians(alpha))
    cos_beta = np.cos(np.radians(beta))
    sin_gamma = np.sin(np.radians(gamma))
    cos_gamma = np.cos(np.radians(gamma))
    
    omega = np.sqrt(1 - cos_alpha**2 - cos_beta**2 - cos_gamma**2 + 2*cos_alpha*cos_beta*cos_gamma)
    
    matrix = np.array([
        [a, 0, 0],
        [b*cos_gamma, b*sin_gamma, 0],
        [c*cos_beta, c*(cos_alpha - cos_beta*cos_gamma)/sin_gamma, c*omega/sin_gamma]
    ])
    
    return matrix

def perpendicular_lengths(a, b, c):
    axb1 = a[1]*b[2] - a[2]*b[1]
    axb2 = a[2]*b[0] - a[0]*b[2]
    axb3 = a[0]*b[1] - a[1]*b[0]
    axb = np.array([axb1, axb2, axb3])
    
    bxc1 = b[1]*c[2] - b[2]*c[1]
    bxc2 = b[2]*c[0] - b[0]*c[2]
    bxc3 = b[0]*c[1] - b[1]*c[0]
    bxc = np.array([bxc1, bxc2, bxc3])
    
    cxa1 = c[1]*a[2] - c[2]*a[1]
    cxa2 = c[2]*a[0] - c[0]*a[2]
    cxa3 = c[0]*a[1] - c[1]*a[0]
    cxa = np.array([cxa1, cxa2, cxa3])
    
    volume = np.abs(np.dot(a, bxc))
    cx = volume / np.linalg.norm(bxc)
    cy = volume / np.linalg.norm(cxa)
    cz = volume / np.linalg.norm(axb)
    
    return [cx, cy, cz]

def create_dir(dict_parameters,data_dir,simulation_name_length=4,verbose=False):
    """
    Create a new directory for simulations and update the index file.

    Parameters:
        dict_parameters (dict): A dictionary containing the simulation parameters.
        data_dir (str) : The path to data directory.

    Returns:
        str: The path to the newly created directory.
    """
    os.makedirs(f'{data_dir}/gcmc/',exist_ok=True)
    dict_parameters["simkey"] = "sim" + secrets.token_hex(simulation_name_length)
    work_dir = f'{data_dir}/gcmc/{dict_parameters["simkey"]}'
    os.makedirs(work_dir,exist_ok=True)
    index_file = f"{data_dir}/gcmc/index.csv"

    df = pd.DataFrame()
    
    # Convert dict_parameters to a DataFrame
    new_row = pd.Series(dict_parameters).to_frame().T  # Create a DataFrame from the Series

    if os.path.isfile(index_file):
        # Read existing DataFrame from CSV
        df = pd.read_csv(index_file)
        
        # Concatenate the new row to the existing DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Write back to CSV
        df.to_csv(index_file, index=False)
        if verbose:
            print(f"Row appended to '{index_file}'.")
    else:
        # Create a new CSV file with the new DataFrame
        df = new_row  # Start with the new row as the DataFrame
        df.to_csv(index_file, index=False)
        if verbose:
            print(f"New file '{index_file}' created.")
    return work_dir
