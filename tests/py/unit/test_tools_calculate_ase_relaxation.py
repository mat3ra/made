from typing import Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.other import get_atom_indices_by_layer, get_atom_indices_in_bottom_layers
from mat3ra.made.tools.build_components.metadata import MaterialWithBuildMetadata
from mat3ra.made.tools.calculate import calculate_total_energy
from mat3ra.made.tools.calculate.ase.relaxation import relax_material
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.modify import interface_get_part
from mat3ra.made.tools.third_party import ASECalculatorEMT
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from unit.fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE

MATERIAL: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
INTERFACE_WITH_BUILD_METADATA: Final = MaterialWithBuildMetadata.create(GRAPHENE_NICKEL_INTERFACE)
SUBSTRATE_INDICES: Final = [
    i for i, label in enumerate(MATERIAL.basis.labels.values) if label == InterfacePartsEnum.SUBSTRATE.value
]
CALCULATOR: Final = ASECalculatorEMT()
RELAX_KWARGS: Final = {"fmax": 0.1, "max_steps": 50, "logfile": None}


def cartesian_positions(material: Material) -> np.ndarray:
    cartesian = material.clone()
    cartesian.to_cartesian()
    return np.array(cartesian.coordinates_array)


def test_get_atom_indices_by_layer():
    assert get_atom_indices_by_layer(MATERIAL) == [[0], [1], [2], [3, 4]]


def test_get_atom_indices_in_bottom_layers():
    assert get_atom_indices_in_bottom_layers(MATERIAL, 1, SUBSTRATE_INDICES) == [0]
    assert get_atom_indices_in_bottom_layers(MATERIAL, 2, SUBSTRATE_INDICES) == [0, 1]
    assert get_atom_indices_in_bottom_layers(MATERIAL, 1) == [0]
    assert get_atom_indices_in_bottom_layers(MATERIAL, 1, []) == []
    with pytest.raises(ValueError):
        get_atom_indices_in_bottom_layers(MATERIAL, 0)


def test_relax_material_lowers_the_energy_and_keeps_identity():
    relaxed = relax_material(MATERIAL, CALCULATOR, **RELAX_KWARGS)
    assert calculate_total_energy(relaxed, CALCULATOR) < calculate_total_energy(MATERIAL, CALCULATOR)
    assert relaxed.name == MATERIAL.name
    assert relaxed.basis.labels.values == MATERIAL.basis.labels.values
    assert relaxed.basis.is_in_crystal_units == MATERIAL.basis.is_in_crystal_units
    assert type(relaxed) is type(MATERIAL)


def test_relax_material_holds_fixed_atoms_and_z_only_motion():
    fixed = get_atom_indices_in_bottom_layers(MATERIAL, 1, SUBSTRATE_INDICES)
    relaxed = relax_material(MATERIAL, CALCULATOR, fixed_atom_indices=fixed, along_z_only=True, **RELAX_KWARGS)
    before, after = cartesian_positions(MATERIAL), cartesian_positions(relaxed)
    assert np.allclose(after[fixed], before[fixed])
    assert np.allclose(after[:, :2], before[:, :2], atol=1e-6)
    assert not np.allclose(after[:, 2], before[:, 2])


def test_relax_material_keeps_build_metadata_so_interface_parts_still_resolve():
    relaxed = relax_material(INTERFACE_WITH_BUILD_METADATA, CALCULATOR, **RELAX_KWARGS)
    assert type(relaxed) is MaterialWithBuildMetadata
    film = interface_get_part(relaxed, part=InterfacePartsEnum.FILM)
    assert len(film.basis.elements.values) == 2


def test_relax_material_raises_when_not_converged():
    with pytest.raises(RuntimeError):
        relax_material(MATERIAL, CALCULATOR, fmax=1e-6, max_steps=1, logfile=None)
