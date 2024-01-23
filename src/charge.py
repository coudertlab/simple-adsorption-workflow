import EQeq
import os,glob

def run_EQeq(cif_dir,output_type="files",**kwargs):
    '''
    Compute the partial charges of framework using the EQeq method (10.1021/jz3008485). The new CIF 
    files in the directory are located in the same directory as the original CIF files.

    Parameters:
        cif_dir (str) : the directory path where CIF are stored.
        output_type (str): the type of output among "cif","mol","pdb","list","json" and "file";
                           default : "files", all possible are created
        kwargs : other arguments (see documentation at https://github.com/ahardiag/EQeq)

    Returns:
        None
    '''
    # Run EQeq with defaults parameters
    for file in glob.glob(f"{cif_dir}/*.cif"):
        if "EQeq" not in file:
            _ = EQeq.run(file, output_type=output_type, method="ewald")
    # Delete other format
    for file in glob.glob(f'{cif_dir}/*'):
        if not file.endswith('.cif'):
            os.remove(file)