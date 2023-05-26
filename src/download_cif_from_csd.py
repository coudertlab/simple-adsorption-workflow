#!/usr/bin/env python
import sys
from ccdc import io

CIFDIR = './cifs'

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
with open(f'{CIFDIR}/{entry_identifier}_csd.cif', 'w') as cif_file:
    cif_file.write(cif_string)
