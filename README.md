# simple-adsorption-workflow

## User input

- A six-letter CSD code identifying the material (example: `KAXQIL`)
- A choice of guest molecule (example: CH4)
- Temperature
- Pressure range (Pmin, Pmax)
- Number of points to be calculated on the isotherm

In this workflow, there are restrictions to make simulations simple (strict assumptions):

- the material is available in the CoreMOF database
- the guest molecule is a rare gas (Ar, Xe) or has a spherical model (N2, CH4, SF6)
- no electrostatic interactions are considered

## Workflow output

An adsorption isotherm, i.e., a series of (pressure, loading) values.
