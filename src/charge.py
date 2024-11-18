import os,glob,sys,shutil
from io import StringIO

from openbabel import openbabel
from pyeqeq import run_on_cif
from pacmof2 import pacmof2


def run_EQeq(cif_dir,cifnames,verbose=False,output_type="files",**kwargs):
    '''
    Compute the partial charges of framework using the EQeq method (10.1021/jz3008485). 

    The new CIF files are located in the same directory as the original CIF files.

    Parameters:
        cifnames (str) : Absolute paths for cif input files.
        verbose (bool) : if True, print the stdout/stderr from EQeq C++ code
        output_type (str): the type of output among "cif","mol","pdb","list","json" and "file";
                           default : "files", all possible are created
        kwargs : other arguments (see documentation at https://github.com/lsmo-epfl/EQeq)

    Returns:
        cifnames_new (list) : the list of CIF filenames with partial charges
    '''
    print('Running EQeq calculations ...')

    # Capture current stdout
    if verbose == False :
        original_stdout,original_stderr = sys.stdout,sys.stderr
        captured_output,captured_error = StringIO(),StringIO()
        sys.stdout,sys.stderr = captured_output,captured_error

    # Input filenames must be absolute
    cifnames = [ _to_absolute_path(cif_dir,cifname,'.cif') for cifname in cifnames]
    
    # Run EQeq with defaults parameters
    for file in cifnames:
        if "EQeq" not in file and "openbabel" not in file:
            if verbose : print(f"Converting file {file} into Openbabel CIF standard format and running charge equilibration.")
            new_cif = _convert_cif_standard_format(file)
            _ = run_on_cif(new_cif, output_type="files", method="ewald")
    # Clean the directory
    _clean_cif_directory(cif_dir)

    cifnames_new = glob.glob(f"{cif_dir}/*EQeq*.cif")
    print(f'Partial charges with method EQeq have been calculated for {len(cifnames)} structures.')

    # Restore stdout
    if verbose == False:
        sys.stdout,sys.stderr = original_stdout,original_stderr
        output_text,error_text = captured_output.getvalue(),captured_error.getvalue()
#        print(output_text,error_text)

    return cifnames_new

def run_pacmof(cif_dir,cifnames,verbose=False,**kwargs):
    '''
    Compute the partial charges of framework using the PACMOF method (10.1021/acs.jpcc.4c04879). 

    The new CIF files are located in the same directory as the original CIF files.

    Parameters:
        cifnames (str) : Absolute paths for cif input files.
        verbose (bool) : if True, print the stdout/stderr PACMOF code

    Returns:
        cifnames_new (list) : the list of CIF filenames with partial charges
    '''
    print('Predicting partial charges from PACMOF2 ...')

    # Capture current stdout
    if verbose == False :
        original_stdout,original_stderr = sys.stdout,sys.stderr
        captured_output,captured_error = StringIO(),StringIO()
        sys.stdout,sys.stderr = captured_output,captured_error

    # Input filenames must be absolute
    cifnames = [ _to_absolute_path(cif_dir,cifname,'.cif') for cifname in cifnames]
    
    # Run EQeq with defaults parameters
    for file in cifnames:
        if "EQeq" not in file and "openbabel" not in file:
            pacmof2.get_charges(file, cif_dir, identifier="_pacmof2")
    
    # Clean the directory
    #_clean_cif_directory(cif_dir)

    cifnames_new = glob.glob(f"{cif_dir}/*_pacmof*.cif")
    print(f'Partial charges with PACMOF2 method have been calculated for {len(cifnames)} structures.')

    # Restore stdout
    if verbose == False:
        sys.stdout,sys.stderr = original_stdout,original_stderr
        output_text,error_text = captured_output.getvalue(),captured_error.getvalue()
#        print(output_text,error_text)

    return cifnames_new

def fetch_QMOF(cifnames,verbose=False):
    '''
    Fetch the structure in QMOF which corresponds to the same CIF as in COREMOF 
    and download the new structures with DDED partial charges partial charges .

    The new CIF files are located in the same directory as the original CIF files.

    Parameters:
        cifnames (str) : Absolute paths for cif input files.

    Returns:
        cifnames_new (list) : the list of CIF filenames with partial charges.
    '''
    print('\n\nWARNING : Access to QMOF partial charges not implemented yet, in the current test loop, it only creates copies of the original cif files from the database !')
    cifnames_new = []
    for cifname in cifnames:
        cifname_qmof = f'{cifname}_QMOF.cif'
        shutil.copyfile(cifname,cifname_qmof)
        print(f"File {cifname_qmof} created.")
        cifnames_new.append(cifname_qmof)
    print("\n")
    return cifnames_new

def _convert_cif_standard_format(input_cif,output_type="file"):
    '''
    A local function to convert a CIF file using Obenbabel CIF standard format.
    '''
    print(input_cif)
    conv = openbabel.OBConversion()
    conv.SetInAndOutFormats("cif", "cif")
    mol = openbabel.OBMol()
    conv.ReadFile(mol, input_cif)
    if output_type == "stream" :
        return conv.WriteString(mol).strip()
    elif output_type == "file":
        output_standard_format = f"{os.path.splitext(input_cif)[0]}_openbabel.cif"
        conv.WriteFile(mol,output_standard_format)
        return output_standard_format
    else :
        raise ValueError('Output type must be "file" or "stream".')
    
def _clean_cif_directory(cif_dir):
    '''
    A local function to remove files with extension different than '.cif'.
    '''
    for file in glob.glob(f'{cif_dir}/*'):
        if not file.endswith('.cif'):
            os.remove(file)

def _to_absolute_path(root_directory, file_path, extension):
    # Check if the file path is already absolute
    if os.path.isabs(file_path):
        return file_path

    # If not absolute, construct the absolute path
    base_name = os.path.basename(file_path)
    absolute_path = os.path.join(root_directory, base_name)

    # Add the extension if it's not already there
    if not absolute_path.endswith(extension):
        absolute_path += extension

    return absolute_path