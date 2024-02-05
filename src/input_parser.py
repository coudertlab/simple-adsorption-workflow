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

# Careful with these lines, since bugs might appear with C++ shared library call
#try:
#    from ccdc import io
#    from ccdc.search import TextNumericSearch
#except Exception as e:
#    print(e)

# Allowed keywords for charge method
CHARGE_METHOD = ["EQeq","None","",None,"QMOF"]

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
        assert molecule_name in basenames, 'The molecule {molecule_name} is not found in ExampleDefinitions.'

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

def cif_from_json(filename, data_dir, database='mofxdb', **kwargs):
    """
    DEPRECATED.

    Generate CIF files from a JSON file containing structures.

    Args:
        filename (str): Path to the JSON file.
        database (str, optional): Database name. Default is 'mofxdb'. Possible values : {'moxdb','csd'}.
        **kwargs: Additional keyword arguments passed to cif_from_mofxdb or cif_from_csd.

    Raises:
        ValueError: If an invalid database name is provided.

    Returns:
        cif_names (list) : A list of CIF filenames.
    """

    # Get structure names from json parsing
    with open(filename, 'r') as f:
        data = json.load(f)
    structures = data["parameters"]["structure"]
    
    # Create directory where CIF files are stored
    cif_dir = f"{data_dir}/cif/"
    os.makedirs(cif_dir,exist_ok=True)

    # Download CIF files from databases
    cifnames_nested = []
    for structure in structures:
        if database == 'mofxdb':
            cifnames_nested.append(cif_from_mofxdb(structure, data_dir, **kwargs))
        elif database == 'csd':
            cifnames_nested.append(cif_from_csd(structure, data_dir, **kwargs))
        else:
            raise ValueError("Invalid database name. Expected 'mofxdb' or 'csd'.")

def get_cifs(l_dict_parameters, data_dir, database='mofxdb', verbose=False,**kwargs):
    """
    Generate CIF files from a JSON file containing structures.

    Args:
        l_dict_parameters (list) : a list of dictionaries containing each set of simulation parameters.
        data_dir (str) : the root path for outputs
        database (str, optional): Database name. Default is 'mofxdb'. Possible values : {'moxdb','csd'}.
        **kwargs: Additional keyword arguments passed to cif_from_mofxdb or cif_from_csd.

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
        elif database == 'csd':
            cifnames_nested.append(cif_from_csd(structure, data_dir, **kwargs))
        else:
            raise ValueError("Invalid database name. Expected 'mofxdb' or 'csd'.")

    # Flat lists
    cifnames_database = [item for sublist in cifnames_nested for item in sublist]

    # Stdout
    print(f"Cif files fetched from {database}")
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

def _get_cifname_matching(cif_dir,pattern,exclude_pattern=None):
    """
    Sample of a list using match and exclusion terms.
    """
    cifs_matched =glob.glob(f'{cif_dir}/{pattern}')
    if exclude_pattern is None:
        assert len(cifs_matched) == 1, f'cif name with pattern {pattern} is not unique'
    elif isinstance(exclude_pattern, str):
        cifs_matched = [cif for cif in cifs_matched if exclude_pattern not in cif]
        assert len(cifs_matched) == 1, f'cif name with pattern {exclude_pattern} and exclusion pattern {exclude_pattern} is not unique'
    elif isinstance(exclude_pattern, list):
        cifs_matched = [cif for cif in cifs_matched if not any(pattern in cif for pattern in exclude_pattern)]
        assert len(cifs_matched) == 1, f'cif name with pattern {exclude_pattern} and exclusion patterns {exclude_pattern} is not unique'
    cifs_matched = _get_basename(cifs_matched)
    return cifs_matched[0]

def _get_basename(filenames):
    '''
    Get basename of a list of files without path and extension.
    '''
    return [os.path.splitext(path)[0].split('/')[-1] for path in filenames]

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
        raise ValueError(f"{structure} not found in MOFXDB subset {substring}")

    return cifnames

def cif_with_charges(cif_dir,cifnames_input,method='EQeq',verbose=True):

    '''
    Returns only the subset of cif filenames containing partial charges.

    Args:
        cif_dir (str): The absolute path of the directory where CIFs are stored
        method (str) : A keyword to select the charge assignment method;
                        possible values : 'EQeq'
    Returns:
        cifnames (list): A list CIF absolute filenames
    '''
    if method == 'EQeq':
        cifnames = run_EQeq(cif_dir,cifnames_input,verbose=verbose)
    elif method == 'QMOF':
        cifnames = fetch_QMOF(cifnames_input,verbose=verbose)
    else:
        raise ValueError(f'Invalid charge method keyword. Expected values : {[el for el in CHARGE_METHOD]}')
    return cifnames

def cif_from_csd(structure, data_dir, search_by="identifier"):
    """
    Generate CIF files from the Cambridge Structural Database (CSD) based on a given structure name.

    Args:
        structure (str): Name of the structure.
        data_dir (str): Parent directory
        search_by (str, optional): Search criteria. Default is "identifier".

    Raises:
        ValueError: If an invalid search criteria is provided or no entries found for the given search criteria.

    Returns:
        cifnames (list) : A list of cif names fetched from the database.
    """

    search = TextNumericSearch()

    if search_by == "identifier":
        search.add_identifier(structure)
    elif search_by == "compound":
        search.add_compound_name(structure)
    else:
        raise ValueError("Invalid search criteria. Expected 'compound' or 'identifier'.")

    entries = search.search()

    if len(entries) == 0:
        raise ValueError("No entries found for the given search criteria.")

    cifnames = []
    for entry in entries:
        cif_string = entry.crystal.to_string('cif')
        cifname = os.path.join(f"{data_dir}/cif/{entry.identifier}_csd.cif")

        with open(cifname, 'w') as cif_file:
            cif_file.write(cif_string)
            print(f'Cif has been written in {cifname}.')
        cifnames.append(cifname)
    return cifnames

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
    
    if os.path.isfile(index_file):
        # Append the DataFrame to the existing CSV file
        df = df.append(pd.Series(dict_parameters), ignore_index=True)
        df.to_csv(index_file, mode='a', header= False, index=False)
        if verbose:
            print(f"Row appended to '{index_file}'.")
    else:
        # Create a new CSV file with the DataFrame
        df = df.append(pd.Series(dict_parameters), ignore_index=True)
        df.to_csv(index_file, index=False)
        if verbose:
            print(f"New file '{index_file}' created.")
    return work_dir
