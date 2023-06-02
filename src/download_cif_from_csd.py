#!/usr/bin/env python
import sys,os
from ccdc import io

CIFDIR = f"{os.environ.get('DATA_DIR')}/cif"
os.makedirs(CIFDIR,exist_ok=True)

# Entry identifier of the desired entry
entry_identifier = sys.argv[1]

# Create a CSD Python API EntryReader object
csd = io.EntryReader('CSD')

# Read the entry using the entry identifier
entry = csd.entry(entry_identifier)

# Get the crystal structure
crystal = entry.crystal

# Get the CIF representation of the crystal structure
cif_string = crystal.to_string('cif')

# Save the CIF string to a CIF file
cifname = f'{CIFDIR}/{entry_identifier}_csd.cif'
with open(cifname, 'w') as cif_file:
    cif_file.write(cif_string)
    print(f'Cif has been written in {cifname} .')


