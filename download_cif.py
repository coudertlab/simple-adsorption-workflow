#!/usr/bin/env python
import sys
NAME = sys.argv[1]
CIFDIR = './cifs'

from mofdb_client import fetch
for mof in fetch(name=NAME):
    print(f"Mof with name {mof.name} from {mof.database} has {len(mof.isotherms)} isotherms stored in MOFX-DB.")
    cifname = CIFDIR + '/'+ mof.name +'_' + mof.database.replace(" ", "-")+'.cif'
    with open(cifname, 'w') as f:
        print(f'Cif has been written in {CIFDIR}/{cifname}.')
        print(mof.cif, file=f)