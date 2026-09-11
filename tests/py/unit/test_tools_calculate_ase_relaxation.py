from typing import Final

import numpy as np
from mat3ra.made.material import Material
from mat3ra.made.tools.calculate import calculate_total_energy
from mat3ra.made.tools.calculate.ase.relaxation import get_atom_indices_in_bottom_layers, relax_material
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.third_party import ASECalculatorEMT
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP

MATERIAL: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
SUBSTRATE_INDICES: Final = [
    i for i, label in enumerate(MATERIAL.basis.labels.values) if label == InterfacePartsEnum.SUBSTRATE.value
]
CALCULATOR: Final = ASECalculatorEMT()


def cartesian_positions(material: Material) -> np.ndarray:
    cartesian = material.clone()
    cartesian.to_cartesian()
    return np.array(cartesian.coordinates_array)


def test_get_atom_indices_in_bottom_layers():
    assert get_atom_indices_in_bottom_layers(MATERIAL, 1, SUBSTRATE_INDICES) == [0]
    assert get_atom_indices_in_bottom_layers(MATERIAL, 2, SUBSTRATE_INDICES) == [0, 1]
    assert get_atom_indices_in_bottom_layers(MATERIAL, 1) == [0]


def test_relax_material_lowers_the_energy_and_keeps_identity():
    relaxed = relax_material(MATERIAL, CALCULATOR, fmax=0.1, max_steps=30, logfile=None)
    assert calculate_total_energy(relaxed, CALCULATOR) <= calculate_total_energy(MATERIAL, CALCULATOR)
    assert relaxed.name == MATERIAL.name
    assert relaxed.basis.labels.values == MATERIAL.basis.labels.values
    assert relaxed.basis.is_in_crystal_units == MATERIAL.basis.is_in_crystal_units
    assert type(relaxed) is type(MATERIAL)


def test_relax_material_holds_fixed_atoms_and_z_only_motion():
    fixed = get_atom_indices_in_bottom_layers(MATERIAL, 1, SUBSTRATE_INDICES)
    relaxed = relax_material(
        MATERIAL, CALCULATOR, fmax=0.1, max_steps=30, fixed_atom_indices=fixed, along_z_only=True, logfile=None
    )
    before, after = cartesian_positions(MATERIAL), cartesian_positions(relaxed)
    assert np.allclose(after[fixed], before[fixed])
    assert np.allclose(after[:, :2], before[:, :2], atol=1e-6)
    assert not np.allclose(after[:, 2], before[:, 2])
