#!/usr/bin/env python
import sys
from mofdb_client import fetch
CIFDIR = './cifs'

substring_identifier = sys.argv[1]
for mof in fetch(name=substring_identifier):
    print(f"Mof with name {mof.name} from {mof.database} has {len(mof.isotherms)} isotherms stored in MOFX-DB.")
    cifname = CIFDIR + '/'+ mof.name +'_' + mof.database.lower().replace(" ", "-")+'.cif'
    with open(cifname, 'w') as f:
        print(f'Cif has been written in {CIFDIR}/{cifname}.')
        print(mof.cif, file=f)