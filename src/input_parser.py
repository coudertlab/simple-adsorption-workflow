import json
from itertools import product

def parse_json(filename):
    with open(filename,'r') as f:
        data = json.load(f)
    dict_default = data["defaults"]
    dict_parameters = data["parameters"]

    # Correct structure names to be compatible with the cif search
    dict_parameters["structure"] = [material+'_clean_coremof-2019' for material in dict_parameters["structure"]]

    # Check if 'pressure' has exactly two values
    if len(dict_parameters['pressure']) != 2:
        raise ValueError("Invalid number of pressure values. Expected 2.")
    (Pmin, Pmax) , npoints = dict_parameters["pressure"], dict_parameters["npoints"]
    dict_parameters["pressure"] = [Pmin + (Pmax - Pmin) * i / (npoints - 1) for i in range(npoints)]

        # Generate combinations
    combinations = list(product(*(value if isinstance(value, list) else [value] for value in dict_parameters.values())))
    
    # Create dictionaries for each combination
    l_dict_parameters = []
    for combo in combinations:
        dictionary = {key: value for key, value in zip(dict_parameters.keys(), combo)}
        dictionary.update(data['defaults'])
        l_dict_parameters.append(dictionary)
    print(l_dict_parameters[0])
    return l_dict_parameters
