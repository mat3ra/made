from typing import List, Optional, Union

import numpy as np
from mat3ra.made.material import Material

from ...convert import from_ase
from ...convert.interface_parts_enum import INTERFACE_LABELS_MAP, InterfacePartsEnum
from ...third_party import ASEAtoms, ASECalculator, ASEFixAtoms, ASEFixedPlane, ase_all_changes
from ..calculators import InterfaceMaterialCalculator, MaterialCalculator
from .constraints import RigidFilmXYInterfaceConstraint


def get_interface_part_indices(atoms: ASEAtoms, part: InterfacePartsEnum) -> List[int]:
    """
    Get the indices of the atoms in the interface part.

    Args:
        atoms (ASEAtoms): The ASE Atoms object.
        part (str): The interface part to get the indices of.

    Returns:
        List[int]: The indices of the atoms in the interface part.
    """
    return [i for i, tag in enumerate(atoms.get_tags()) if tag == INTERFACE_LABELS_MAP[part.name.lower()]]


class FilmSubstrateDistanceASECalculator(ASECalculator):
    """
    ASE calculator that calculates the interaction energy between a film and substrate in an interface material.

    Args:
        shadowing_radius (float): The radius for atom to shadow underlying from being considered surface, in Angstroms.
        force_constant (float): The force constant for the finite difference approximation of the forces.
        is_substrate_fixed (bool): Whether to fix the substrate atoms.
        is_z_axis_fixed (bool): Whether to fix atoms movement in the z direction.
        symprec (float): The symmetry precision for the ASE calculator. This parameter determines the tolerance
                         for symmetry operations, affecting the identification of equivalent atoms and the overall
                         symmetry of the system. For more details, refer to the ASE documentation:
                         https://wiki.fysik.dtu.dk/ase/ase/constraints.html#ase.constraints.FixSymmetry

    Example usage:
    ```python
    from ase.optimize import BFGS
    atoms = to_ase(material)
    calc = SurfaceDistanceCalculator(shadowing_radius=2.5)

    atoms.calc = calc
    opt = BFGS(atoms)
    opt.run(fmax=0.05)
    ```
    Args:
        shadowing_radius (float): Radius for atoms shadowing underlying from being treated as a surface, in Angstroms.
        force_constant (float): The force constant for the finite difference approximation of the
    Note:
        Built following https://wiki.fysik.dtu.dk/ase/development/calculators.html

        The calculate method is responsible for computing the energy and forces (if requested).
        Forces are estimated using a finite difference method, which is a simple approximation
        and might not be the most accurate or efficient for all cases.
    """

    implemented_properties = ["energy", "forces"]

    def __init__(
        self,
        shadowing_radius: float = 2.5,
        is_substrate_fixed: bool = True,
        is_z_axis_fixed: bool = True,
        symprec: float = 0.01,
        material_calculator: Union[MaterialCalculator, InterfaceMaterialCalculator] = InterfaceMaterialCalculator(),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.shadowing_radius = shadowing_radius
        self.fix_substrate = is_substrate_fixed
        self.fix_z = is_z_axis_fixed
        self.symprec = symprec
        self.material_calculator = material_calculator

    def _add_constraints(self, atoms: ASEAtoms) -> ASEAtoms:
        constraints: List[Union[ASEFixAtoms, ASEFixedPlane, RigidFilmXYInterfaceConstraint]] = []
        if self.fix_substrate:
            substrate_indices = get_interface_part_indices(atoms, InterfacePartsEnum.SUBSTRATE)
            constraints.append(ASEFixAtoms(indices=substrate_indices))
        if self.fix_z:
            all_indices = list(range(len(atoms)))
            constraints.append(ASEFixedPlane(indices=all_indices, direction=[0, 0, 1]))

        film_indices = get_interface_part_indices(atoms, InterfacePartsEnum.FILM)
        if film_indices:
            constraints.append(RigidFilmXYInterfaceConstraint(film_indices=film_indices))

        atoms.set_constraint(constraints)
        return atoms

    def _calculate_forces(self, atoms: ASEAtoms, energy: float) -> np.ndarray:
        forces = np.zeros((len(atoms), 3))
        dx = 0.01
        for i in range(len(atoms)):
            for j in range(3):
                atoms_plus = atoms.copy()
                atoms_plus.positions[i, j] += dx
                material_plus = Material.create(from_ase(atoms_plus))
                energy_plus = self.material_calculator.get_energy(material_plus)

                forces[i, j] = -(energy_plus - energy) / dx

        return forces

    def calculate(self, atoms: Optional[ASEAtoms] = None, properties=["energy"], system_changes=ase_all_changes):
        if atoms is None:
            atoms = self.atoms.copy()

        atoms = self._add_constraints(atoms)
        constraints = atoms.constraints

        super().calculate(atoms, properties, system_changes)
        material = Material.create(from_ase(atoms))
        energy = self.material_calculator.get_energy(material)

        self.results = {"energy": energy}

        if "forces" in properties:
            forces = self._calculate_forces(atoms, energy)
            for constraint in constraints:
                constraint.adjust_forces(atoms, forces)
            self.results["forces"] = forces

    def get_potential_energy(self, atoms=None, force_consistent=False):
        return self.get_property("energy", atoms)

    def get_forces(self, atoms=None):
        return self.get_property("forces", atoms)
