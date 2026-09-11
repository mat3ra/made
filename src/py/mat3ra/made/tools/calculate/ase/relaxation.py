from typing import List, Optional, Sequence, Union

import numpy as np
from mat3ra.made.material import Material

from ...build_components.metadata import MaterialWithBuildMetadata
from ...convert import to_ase
from ...third_party import ASEBFGS, ASECalculator, ASEFixAtoms, ASEFixedLine

Z_DIRECTION = [0, 0, 1]


def _build_constraints(atom_count: int, fixed_atom_indices: Optional[Sequence[int]], along_z_only: bool) -> list:
    constraints: list = []
    if fixed_atom_indices:
        constraints.append(ASEFixAtoms(indices=list(fixed_atom_indices)))
    if along_z_only:
        constraints.append(ASEFixedLine(list(range(atom_count)), direction=Z_DIRECTION))
    return constraints


def _with_positions(material: Material, positions: np.ndarray) -> Material:
    """A copy of the material with new cartesian positions and everything else — name, labels,
    lattice, build metadata, units — as it was."""
    relaxed = material.clone()
    was_in_crystal_units = relaxed.basis.is_in_crystal_units
    relaxed.to_cartesian()
    relaxed.set_coordinates(positions.tolist())
    if was_in_crystal_units:
        relaxed.to_crystal()
    return relaxed


def relax_material(
    material: Union[Material, MaterialWithBuildMetadata],
    calculator: ASECalculator,
    fmax: float = 0.05,
    max_steps: int = 300,
    fixed_atom_indices: Optional[Sequence[int]] = None,
    along_z_only: bool = False,
    logfile: Optional[str] = "-",
) -> Union[Material, MaterialWithBuildMetadata]:
    """
    Relax atomic positions with an ASE calculator at fixed cell, optionally holding atoms fixed or
    allowing motion along z only.

    Holding the deepest substrate layers fixed is the usual slab protocol (they stand in for bulk);
    z-only motion keeps an adsorbed film in its registry, which an unconstrained relaxation can lose.

    Args:
        material: The structure to relax; labels and build metadata are preserved in the result.
        calculator: Any ASE calculator, e.g. EMT or a machine-learned force field.
        fmax: Force convergence criterion, eV/Angstrom.
        max_steps: Optimizer step limit.
        fixed_atom_indices: Atoms held fixed, e.g. from `get_atom_indices_in_bottom_layers`.
        along_z_only: Restrict every atom's motion to the z direction.
        logfile: ASE optimizer log target; "-" is stdout, None silences it.

    Returns:
        The relaxed material, same type and units as the input.
    """
    atoms = to_ase(material)
    constraints = _build_constraints(len(atoms), fixed_atom_indices, along_z_only)
    if constraints:
        atoms.set_constraint(constraints)
    atoms.calc = calculator
    ASEBFGS(atoms, logfile=logfile).run(fmax=fmax, steps=max_steps)
    return _with_positions(material, atoms.positions)


def get_atom_indices_in_bottom_layers(
    material: Material,
    layer_count: int,
    atom_indices: Optional[Sequence[int]] = None,
    tolerance: float = 0.5,
) -> List[int]:
    """
    Indices of the atoms in the `layer_count` lowest layers, among `atom_indices` (all atoms by
    default). Atoms within `tolerance` Angstrom in height belong to one layer.
    """
    cartesian = material.clone()
    cartesian.to_cartesian()
    heights = np.array(cartesian.coordinates_array)[:, 2]
    candidates = list(range(len(heights))) if atom_indices is None else list(atom_indices)
    layer_tops: List[float] = []
    for z in sorted(heights[i] for i in candidates):
        if not layer_tops or z - layer_tops[-1] > tolerance:
            layer_tops.append(z)
        else:
            layer_tops[-1] = z
    cutoff = layer_tops[min(layer_count, len(layer_tops)) - 1] + tolerance / 2
    return [i for i in candidates if heights[i] <= cutoff]
