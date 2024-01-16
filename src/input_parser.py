import json
from itertools import product
import sys
import os
from mofdb_client import fetch
from ase.io import read
from math import ceil
import pandas as pd
import secrets
import warnings

try:
    from ccdc import io
    from ccdc.search import TextNumericSearch
except Exception as e:
    print(e)

def parse_json(filename,cifnames):
    """
    Parse a JSON file containing default values and parameters, and generate combinations of parameter values.

    Args:
        filename (str): The name of the JSON file to parse.
        cifnames (list): List of CIF names. For a input structure in the input file, one can find several CIFs in a database.

    Returns:
        list: A list of dictionaries, each representing a combination of parameter values.
    """

    with open(filename, 'r') as f:
        data = json.load(f)
    dict_default = data["defaults"]
    dict_parameters = data["parameters"]

    # Correct structure names to be compatible with the cif search
    dict_parameters["structure"] = cifnames

    # Check if 'pressure' has exactly two values
    if len(dict_parameters['pressure']) != 2:
        raise ValueError("Invalid number of pressure values. Expected 2.")
    Pmin, Pmax = dict_parameters["pressure"]
    npoints = dict_parameters["npoints"]
    dict_parameters["pressure"] = [Pmin + (Pmax - Pmin) * i / (npoints - 1) for i in range(npoints)]

    # Check conistency of RASPA inputs
    check_input_raspa(dict_parameters["molecule_name"])    
    
    # Generate combinations
    combinations = list(product(*(value if isinstance(value, list) else [value] for value in dict_parameters.values())))

    # Create dictionaries for each combination
    l_dict_parameters = []
    for combo in combinations:
        dictionary = {key: value for key, value in zip(dict_parameters.keys(), combo)}
        dictionary.update(data['defaults'])
        l_dict_parameters.append(dictionary)
    return l_dict_parameters

def check_input_raspa(molecule_name_list):
    '''
    Look for the precence of parameters for the molecule in the TrAPPE force field.
    '''
    basenames = ([os.path.basename(filename).split('.def')[0] for filename in os.listdir(f"{os.environ.get('RASPA_PARENT_DIR')}/share/raspa/molecules/TraPPE/")])
    for molecule_name in molecule_name_list: 
        assert molecule_name in basenames, 'The molecule {molecule_name} is not found in TraPPE.'

def parse_json_2(filename):
    """
    Parse a JSON file containing default values and parameters, and generate combinations of parameter values.

    Args:
        filename (str): The name of the JSON file to parse.
    Returns:
        list: A list of dictionaries, each representing a combination of parameter values.
    """

    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def cif_from_json(filename, data_dir, database='mofxdb', **kwargs):
    """
    Generate CIF files from a JSON file containing structures.

    Args:
        filename (str): Path to the JSON file.
        database (str, optional): Database name. Default is 'mofxdb'. Possible values : {'moxdb','csd'}.
        **kwargs: Additional keyword arguments passed to cif_from_mofxdb or cif_from_csd.

    Raises:
        ValueError: If an invalid database name is provided.

    Returns:
        None
    """

    # Get structure names from json parsing
    with open(filename, 'r') as f:
        data = json.load(f)
    structures = data["parameters"]["structure"]
    
    # Create directory where CIF files are stored
    os.makedirs(f"{data_dir}/cif/",exist_ok=True)

    # Download CIF files from databases
    cifnames_nested = []
    for structure in structures:
        if database == 'mofxdb':
            cifnames_nested.append(cif_from_mofxdb(structure, data_dir, **kwargs))
        elif database == 'csd':
            cifnames_nested.append(cif_from_csd(structure, data_dir, **kwargs))
        else:
            raise ValueError("Invalid database name. Expected 'mofxdb' or 'csd'.")

    # Get only the basename of CIF files
    cifnames = [item for sublist in cifnames_nested for item in sublist]
    cifnames = [path.split('/')[-1].split('.cif')[0] for path in cifnames]
    return cifnames

def cif_from_mofxdb(structure, data_dir, substring = "coremof-2019", verbose=False):
    """
    Generate CIF files from MOFX-DB based on a given structure name.

    Args:
        structure (str): Name of the structure.
        data_dir (str): Parent directory

    Returns:
        None
    """

    cifnames = []
    for mof in fetch(name=structure):
        cifname = os.path.join(f"{data_dir}/cif/{mof.name}_{mof.database.lower().replace(' ', '-')}.cif")

        # Filter using original database key
        if substring in cifname:
            with open(cifname, 'w') as f:
                print(mof.cif, file=f)
                print(f'Cif has been written in {cifname}.')
            cifnames.append(cifname)

            # Indicate the number of isotherms found in MOFXDB (can be used for reproducibility purposes)
            if verbose:
                print(f"Mof with name {mof.name} from {mof.database} has already {len(mof.isotherms)} isotherms stored in MOFX-DB.")

    # Add a warning for the structure has no entry in the structural databases
    if len(cifnames)==0:
        warnings.warn(f"{structure} not found in MOFXDB subset {substring}")

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
        None
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

def get_cifnames(data_dir, substring=""):
    """
    Get a list of CIF filenames in a data_dir that match a given substring.

    Args:
        data_dir (str, optional): Parent directory.
        substring (str, optional): Substring to match in the filenames. Default is an empty string.

    Returns:
        list: A list of CIF filenames.
    """
    cif_filenames = []
    for filename in os.listdir(f"{data_dir}/cif/"):
        if filename.endswith('.cif') and substring in filename:
            cif_filenames.append(os.path.splitext(filename)[0])
    return cif_filenames

def get_minimal_unit_cells(cif_path_filename):
    """
    Get the minimal supercell multipliers to avoid periodic boundary conditions bias.
    This is an approximate method that is only valid for the rectangular cell.
    TODO : implement the extended method for triclinic box, using the output of RASPA simulation with 0 steps.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, message="crystal system 'triclinic' is not interpreted")
        atoms = read(cif_path_filename)
    a, b, c, _,_,_ = atoms.cell.cellpar()
    n_a = ceil(24/ a)
    n_b = ceil(24/ b)
    n_c = ceil(24/ c)
    return [n_a,n_b,n_c]

def create_dir(dict_parameters,data_dir,simulation_name_length=4,verbose=False):
    """
    Create a new directory for simulations and update the index file.

    Parameters:
        dict_parameters (dict): A dictionary containing the simulation parameters.
        data_dir (str) : The path to data directory.

    Returns:
        str: The path to the newly created directory.
    """
    os.makedirs(f'{data_dir}/simulations/',exist_ok=True)
    dict_parameters["simkey"] = "sim" + secrets.token_hex(simulation_name_length)
    work_dir = f'{data_dir}/simulations/{dict_parameters["simkey"]}'
    os.makedirs(work_dir,exist_ok=True)
    index_file = f"{data_dir}/simulations/index.csv"

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
