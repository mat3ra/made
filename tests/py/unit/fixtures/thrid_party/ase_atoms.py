from ase.build import bulk, molecule

BULK_SI_LATTICE_A = 3.8395
BULK_SI_LATTICE_ALPHA = 60
BULK_SI_LABELS = [{"id": 0, "value": 0}, {"id": 1, "value": 1}]

atoms = bulk("Si")
atoms.set_tags([0, 1])
ASE_BULK_Si = atoms

atoms = molecule("H2O")
atoms.set_pbc(False)
ASE_MOLECULE_H2O = atoms
