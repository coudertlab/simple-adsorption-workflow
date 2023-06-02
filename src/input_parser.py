import json
from itertools import product
import sys
import os
from mofdb_client import fetch
from ase.io import read
from math import ceil

try:
    from ccdc import io
    from ccdc.search import TextNumericSearch
except ImportError:
    pass

CIFDIR = f"{os.environ.get('DATA_DIR')}/cif"
os.makedirs(CIFDIR, exist_ok=True)


def parse_json(filename, cifnames=None):
    """
    Parse a JSON file containing default values and parameters, and generate combinations of parameter values.

    Args:
        filename (str): The name of the JSON file to parse.
        cifnames (list, optional): List of CIF names. Defaults to None.

    Returns:
        list: A list of dictionaries, each representing a combination of parameter values.
    """

    with open(filename, 'r') as f:
        data = json.load(f)
    dict_default = data["defaults"]
    dict_parameters = data["parameters"]

    # Correct structure names to be compatible with the cif search
    if cifnames is None:
        cifnames = [material + '_clean_coremof-2019' for material in dict_parameters["structure"]]
    dict_parameters["structure"] = cifnames

    # Check if 'pressure' has exactly two values
    if len(dict_parameters['pressure']) != 2:
        raise ValueError("Invalid number of pressure values. Expected 2.")
    Pmin, Pmax = dict_parameters["pressure"]
    npoints = dict_parameters["npoints"]
    dict_parameters["pressure"] = [Pmin + (Pmax - Pmin) * i / (npoints - 1) for i in range(npoints)]

    # Generate combinations
    combinations = list(product(*(value if isinstance(value, list) else [value] for value in dict_parameters.values())))

    # Create dictionaries for each combination
    l_dict_parameters = []
    for combo in combinations:
        dictionary = {key: value for key, value in zip(dict_parameters.keys(), combo)}
        dictionary.update(data['defaults'])
        l_dict_parameters.append(dictionary)
    return l_dict_parameters


def cif_from_json(filename, database='mofxdb', **kwargs):
    """
    Generate CIF files from a JSON file containing structures.

    Args:
        filename (str): Path to the JSON file.
        database (str, optional): Database name. Default is 'mofxdb'.
        **kwargs: Additional keyword arguments passed to cif_from_mofxdb or cif_from_csd.

    Raises:
        ValueError: If an invalid database name is provided.

    Returns:
        None
    """

    with open(filename, 'r') as f:
        data = json.load(f)

    structures = data["parameters"]["structure"]

    for structure in structures:
        if database == 'mofxdb':
            cif_from_mofxdb(structure, **kwargs)
        elif database == 'csd':
            cif_from_csd(structure, **kwargs)
        else:
            raise ValueError("Invalid database name. Expected 'mofxdb' or 'csd'.")


def cif_from_mofxdb(structure):
    """
    Generate CIF files from MOFX-DB based on a given structure name.

    Args:
        structure (str): Name of the structure.

    Returns:
        None
    """

    for mof in fetch(name=structure):
        print(f"Mof with name {mof.name} from {mof.database} has {len(mof.isotherms)} isotherms stored in MOFX-DB.")
        cifname = os.path.join(CIFDIR, f"{mof.name}_{mof.database.lower().replace(' ', '-')}.cif")

        with open(cifname, 'w') as f:
            print(f'Cif has been written in {cifname}.')
            print(mof.cif, file=f)


def cif_from_csd(structure, search_by="identifier"):
    """
    Generate CIF files from the Cambridge Structural Database (CSD) based on a given structure name.

    Args:
        structure (str): Name of the structure.
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

    for entry in entries:
        cif_string = entry.crystal.to_string('cif')
        cifname = os.path.join(CIFDIR, f"{entry.identifier}_csd.cif")

        with open(cifname, 'w') as cif_file:
            cif_file.write(cif_string)
            print(f'Cif has been written in {cifname}.')


def get_cifnames(directory=CIFDIR, substring=""):
    """
    Get a list of CIF filenames in a directory that match a given substring.

    Args:
        directory (str, optional): Directory path. Default is CIFDIR.
        substring (str, optional): Substring to match in the filenames. Default is an empty string.

    Returns:
        list: A list of CIF filenames.
    """

    cif_filenames = []
    for filename in os.listdir(directory):
        if filename.endswith('.cif') and substring in filename:
            cif_filenames.append(os.path.splitext(filename)[0])
    return cif_filenames


def get_minimal_unit_cells(cif_path):
    """
    Get the minimal supercell multipliers to avoid periodic boundary conditions bias.
    This is an approximate method that is only valid rigorous for the rectangular cell.
    TODO : implement the extended method for triclinic box, using the output of RASPA simulation with 0 steps.
    """
    atoms = read(cif_path)
    a, b, c, _,_,_ = atoms.cell.cellpar()
    n_a = ceil(24/ a)
    n_b = ceil(24/ b)
    n_c = ceil(24/ c)
    return [n_a,n_b,n_c]