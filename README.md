# simple-adsorption-workflow

## Install

### Environments 
Use a conda environment with python 3.
```bash
conda create -n simple-adsorption-workflow python=3
```

Install requirements in the conda environment
```bash
conda activate simple-adsorption-workflow
pip install -r requirements.txt
```


## User input

- A six-letter CSD code identifying the material (example: `KAXQIL`)
- A choice of guest molecule `ADSORBATE` (example: CH4)
- Temperature `TEMPERATURE`
- Pressure range (`PMIN`, `PMAX`)
- Number of points to be calculated on the isotherm `POINTS`

In this workflow, there are restrictions to make simulations simple (strict assumptions):

- the material is available in the CoreMOF database (through MOFXDB database)
 https://github.com/n8ta/mofdb-client
- the guest molecule is a rare gas (Ar, Xe) or has a spherical model (N2, CH4, SF6)
- no electrostatic interactions are considered

## Workflow output

An adsorption isotherm, i.e., a series of (pressure, loading) values.

## To do 
- [x] Find the cif file(s) in CoRE MOF from its six-letter CSD code
e.g : `python download_cif.py KAXQIL`
> Note : The search is fetched using the MOFX-DB API, it returns all mofs for which part of the name matches with the input keyword.

- [ ] Generate all inputs files for RASPA with a set of parameters `ADSORBATE`,`PMIN`,`PMAX`,`NPOINTS` and `T`

- [ ] Write sections Install
- [ ] Write a run file
- [ ] Give a simple example for plotting (python notebook)