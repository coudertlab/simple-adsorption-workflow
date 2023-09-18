import re
import pandas as pd
import glob,os

zeopp_dir = os.environ.get('ZEO_DIR')

def run_zeopp_asa(data_dir,
                  cif_files=None,
                  chan_radius=1.2,
                  probe_radius = 1.2,
                  num_samples_per_atom = 2000,
                  verbose=False):

    # Run Zeo++ on all selected cifs files or found in the default directory
    print(f"Running Zeo++ to compute accessible surface area...")
    if cif_files is not None:
        assert isinstance(cif_files, list), 'Argument cif_files must be a list.'
        for file in cif_files:
            assert os.path.exists(file) == True, f'File {file} not found'
    else:
        cif_files=glob.glob(f'{data_dir}/cif/*cif')

    zeopp_output_dir = f"{data_dir}/zeopp_asa/"
    os.makedirs(zeopp_output_dir,exist_ok=True)
    for cif_file in cif_files:
        basename = os.path.basename(cif_file)
        cif_basename, extension = os.path.splitext(basename)
        os.system(f'{zeopp_dir}/network -ha -sa {chan_radius} {probe_radius} {num_samples_per_atom} {zeopp_output_dir}/{cif_basename}.sa {data_dir}/cif/{cif_basename}.cif >> {data_dir}/zeopp.log 2>&1')

    # Define the regular expression patterns for extracting data
    unitcell_volume_pattern = r"Unitcell_volume:\s([\d.]+)"
    density_pattern = r"Density:\s([\d.]+)"
    asa_pattern = r"ASA_A\^2:\s([\d.]+)\sASA_m\^2/cm\^3:\s([\d.]+)\sASA_m\^2/g:\s([\d.]+)"
    nasa_pattern = r"NASA_A\^2:\s([\d.]+)\sNASA_m\^2/cm\^3:\s([\d.]+)\sNASA_m\^2/g:\s([\d.]+)"
    #channels_pattern = r"Number_of_channels:\s(\d+)\sChannel_surface_area_A\^2:\s([\d.]+)\s([\d.]+)"
    channel_pattern = r"Number_of_channels: (\d+) Channel_surface_area_A\^2: ([\d\s.]+)"
    pockets_pattern = r"Number_of_pockets:\s(\d+)\sPocket_surface_area_A\^2: ([\d\s.]+)"

    # Initialize an empty dictionary to store the parsed data
    data = {
        'Name': [],
        'Unitcell_volume': [],
        'Density': [],
        'ASA_A^2': [],
        'ASA_m^2/cm^3': [],
        'ASA_m^2/g': [],
        'NASA_A^2': [],
        'NASA_m^2/cm^3': [],
        'NASA_m^2/g': [],
        'Number_of_channels': [],
        'Channel_surface_area_A^2': [],
        'Number_of_pockets': [],
        'Pocket_surface_area_A^2': []
    }

    folder = glob.glob(f'{zeopp_output_dir}/*.sa')
    for filename in folder :
        basename = os.path.basename(filename)
        name, extension = os.path.splitext(basename)
        with open(filename,"r") as f:
            output_string = f.read().strip()

        unitcell_volume = re.findall(unitcell_volume_pattern, output_string)
        density = re.findall(density_pattern, output_string)
        asa = re.findall(asa_pattern, output_string)
        nasa = re.findall(nasa_pattern, output_string)
        channels = re.findall(channel_pattern, output_string)
        pockets = re.findall(pockets_pattern, output_string)

        # Add the parsed data to the dictionary
        data['Name'].extend([name])
        data['Unitcell_volume'].extend(unitcell_volume)
        data['Density'].extend(density)
        data['ASA_A^2'].extend([asa[0][0]])
        data['ASA_m^2/cm^3'].extend([asa[0][1]])
        data['ASA_m^2/g'].extend([asa[0][2]])
        data['NASA_A^2'].extend([nasa[0][0]])
        data['NASA_m^2/cm^3'].extend([nasa[0][1]])
        data['NASA_m^2/g'].extend([nasa[0][2]])
        data['Number_of_channels'].extend([int(channels[0][0]) if channels != [] else 0 ])
        data['Channel_surface_area_A^2'].extend([str(channels[0][1]).strip() if channels != [] else "" ])
        data['Number_of_pockets'].extend([int(pockets[0][0]) if pockets != [] else 0])
        data['Pocket_surface_area_A^2'].extend([str(pockets[0][1]).strip() if pockets != [] else ""])

    # Add parameters of Zeo++
    data['chan_radius'] = chan_radius
    data['probe_radius'] = probe_radius
    data['num_samples_per_atom'] = num_samples_per_atom

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data)
    df.sort_values('Name')
    result_filename = f'{zeopp_output_dir}/results_zeopp.csv'
    df.to_csv(result_filename,index=False)
    print(f"Results stored in results_zeopp.csv.")
    if verbose :
        print(f"All data extracted from Zeo++ in {zeopp_output_dir} have been stored in {result_filename}.")