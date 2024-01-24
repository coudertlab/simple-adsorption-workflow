import os,glob,sys
from pyeqeq import run_on_cif
from io import StringIO

def run_EQeq(cif_dir,verbose=False,output_type="files",**kwargs):
    '''
    Compute the partial charges of framework using the EQeq method (10.1021/jz3008485). The new CIF 
    files in the directory are located in the same directory as the original CIF files.

    Parameters:
        cif_dir (str) : the directory path where CIF are stored.
        verbose (bool) : if True, print the stdout/stderr from EQeq C++ code
        output_type (str): the type of output among "cif","mol","pdb","list","json" and "file";
                           default : "files", all possible are created
        kwargs : other arguments (see documentation at https://github.com/lsmo-epfl/EQeq)

    Returns:
        None
    '''
    print('Running EQeq calculations ...')

    # Capture current stdout
    original_stdout,original_stderr = sys.stdout,sys.stderr
    captured_output,captured_error = StringIO(),StringIO()
    sys.stdout,sys.stderr = captured_output,captured_error

    # Run EQeq with defaults parameters
    for file in glob.glob(f"{cif_dir}/*.cif"):
        if "EQeq" not in file:
            _ = run_on_cif(file,output_type=output_type,method="ewald",**kwargs)

    # Delete other format
    for file in glob.glob(f'{cif_dir}/*'):
        if not file.endswith('.cif'):
            os.remove(file)
    cifnames = glob.glob(f"{cif_dir}/*EQeq*.cif")
    print(f'Partial charges with method EQeq have been calculated for {len(cifnames)} structures.')

    # Restore stdout
    sys.stdout,sys.stderr = original_stdout,original_stderr
    output_text,error_text = captured_output.getvalue(),captured_error.getvalue()

    if verbose == True :
        print(output_text,error_text)

    return cifnames