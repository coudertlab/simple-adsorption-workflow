import os,glob

def check_simulations(verbose=False,
                      path=f'{os.environ.get("DATA_DIR")}/simulations'):
    dir_no_outputs=[]
    dir_many_outputs=[]
    warnings_one_output={}
    errors_one_output={}
    for dir in os.listdir(path):
        l_data_files = glob.glob(f'{path}/{dir}/Output/System_0/*.data')
        if len(l_data_files)==1:
            filename = l_data_files[0]
            warnings_one_output[filename] = get_lines_with_match('WARNING',filename)
            errors_one_output[filename] = get_lines_with_match('ERROR',filename)
        elif len(l_data_files)>1:
            dir_many_outputs.append(dir)
        else :
            dir_no_outputs.append(dir)
            print("bad")

    non_empty_warnings = {key:value for key,value in warnings_one_output.items() if isinstance(value, list) and len(value) > 0}
    non_empty_errors = {key:value for key,value in errors_one_output.items() if isinstance(value, list) and len(value) > 0}
    print(f'{len(os.listdir(path))} directories found in {path}:')
    print(f"No       outputs found in {len(dir_no_outputs):5d} directories.")
    print(f"Multiple outputs found in {len(dir_many_outputs):5d} directories.")
    print(f"Warnings         found in {len(non_empty_warnings):5d} directories.")
    if verbose is True : print_dict(non_empty_warnings)
    print(f"Errors           found in {sum(non_empty_errors):5d} directories.")
    if verbose is True : print_dict(non_empty_errors)

def get_lines_with_match(string,filename):
    lines = []
    with open(filename, 'r') as file:
        for line in file:
            if string in line:
                lines.append(line.strip())
    return list(set(lines))

def print_dict(d):
    for key, elements in d.items():
        print(f"{key}:")
        for element in elements:
            print(element)
        print()