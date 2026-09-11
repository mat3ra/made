from typing import Final, List

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import get_film_site_occupation
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.modify import interface_displace_film_to_site
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from unit.utils import assert_two_entities_deep_almost_equal

INTERFACE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)  # Ni 0-2 (2 on top), C 3 (atop), C 4 (hcp)
SUPERCELL_2X2: Final = create_supercell(INTERFACE, scaling_factor=[2, 2, 1])
SUPERCELL_4X4: Final = create_supercell(INTERFACE, scaling_factor=[4, 4, 1])


def top_nickel(material: Material) -> List[int]:
    cartesian = material.clone()
    cartesian.to_cartesian()
    z = np.array(cartesian.coordinates_array)[:, 2]
    nickel = [i for i, e in enumerate(material.basis.elements.values) if e == "Ni"]
    return [i for i in nickel if z[i] > z[nickel].max() - 0.5]


def periodic_distance(material: Material, a: int, b: int) -> float:
    """The shortest distance between two atoms' in-plane coordinates, periodic images included."""
    cartesian = material.clone()
    cartesian.to_cartesian()
    xy = np.array(cartesian.coordinates_array)[:, :2]
    vectors = np.array(material.lattice.vector_arrays)[:2, :2]
    shifts = [i * vectors[0] + j * vectors[1] for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return min(np.linalg.norm(xy[a] + s - xy[b]) for s in shifts)


def far_apart(material: Material, atoms: List[int], count: int) -> List[int]:
    """`count` atoms of the list chosen greedily to be as far from one another as periodicity allows."""
    chosen = [atoms[0]]
    while len(chosen) < count:
        chosen.append(
            max(
                (a for a in atoms if a not in chosen),
                key=lambda a: min(periodic_distance(material, a, c) for c in chosen),
            )
        )
    return chosen


def first_carbon(material: Material) -> int:
    return next(i for i, e in enumerate(material.basis.elements.values) if e == "C")


CARBON_2X2: Final = first_carbon(SUPERCELL_2X2)

EXPECTED_BASIS_ATOP: Final = {
    "elements": [
        {"id": 0, "value": "Ni"},
        {"id": 1, "value": "Ni"},
        {"id": 2, "value": "Ni"},
        {"id": 3, "value": "C"},
        {"id": 4, "value": "C"},
    ],
    "coordinates": [
        {"id": 0, "value": [0.0, 0.0, 3.03e-07]},
        {"id": 1, "value": [0.666666667, 0.333333333, 0.100960811]},
        {"id": 2, "value": [0.333333333, 0.666666667, 0.201921319]},
        {"id": 3, "value": [0.0, 0.0, 0.351561882]},
        {"id": 4, "value": [0.333333333, 0.666666667, 0.351561882]},
    ],
    "units": "crystal",
    "labels": [
        {"id": 0, "value": 0},
        {"id": 1, "value": 0},
        {"id": 2, "value": 0},
        {"id": 3, "value": 1},
        {"id": 4, "value": 1},
    ],
}

EXPECTED_BASIS_BRIDGE_TO_SELF_IMAGE: Final = {
    "elements": [
        {"id": 0, "value": "Ni"},
        {"id": 1, "value": "Ni"},
        {"id": 2, "value": "Ni"},
        {"id": 3, "value": "C"},
        {"id": 4, "value": "C"},
    ],
    "coordinates": [
        {"id": 0, "value": [0.0, 0.0, 3.03e-07]},
        {"id": 1, "value": [0.666666667, 0.333333333, 0.100960811]},
        {"id": 2, "value": [0.333333333, 0.666666667, 0.201921319]},
        {"id": 3, "value": [0.499999999, 0.500000001, 0.351561882]},
        {"id": 4, "value": [0.833333333, 0.166666667, 0.351561882]},
    ],
    "units": "crystal",
    "labels": [
        {"id": 0, "value": 0},
        {"id": 1, "value": 0},
        {"id": 2, "value": 0},
        {"id": 3, "value": 1},
        {"id": 4, "value": 1},
    ],
}

INTERFACE_DISPLACE_FILM_TO_SITE_CASES = [
    (INTERFACE, 4, [2], EXPECTED_BASIS_ATOP),
    # a bridge to the substrate atom's own periodic image — the only way to name a bridge in a 1x1 cell
    (INTERFACE, 4, [2, 2], EXPECTED_BASIS_BRIDGE_TO_SELF_IMAGE),
]


@pytest.mark.parametrize("interface, film_atom, substrate_atoms, expected_basis", INTERFACE_DISPLACE_FILM_TO_SITE_CASES)
def test_interface_displace_film_to_site(interface, film_atom, substrate_atoms, expected_basis):
    placed = interface_displace_film_to_site(interface, film_atom=film_atom, substrate_atoms=substrate_atoms)
    assert_two_entities_deep_almost_equal(placed.basis, expected_basis, atol=1e-6)


INTERFACE_DISPLACE_FILM_TO_SITE_INVALID_CASES = [
    (INTERFACE, 99, [2], "out of range"),
    (INTERFACE, 3, [99], "out of range"),
    (INTERFACE, 0, [2], "not in the film"),
    (INTERFACE, 3, [4], "Not all"),
    (INTERFACE, 4, [], "one, two or three"),
    (INTERFACE, 3, [0, 1], "not in one layer"),
    (
        SUPERCELL_4X4,
        first_carbon(SUPERCELL_4X4),
        far_apart(SUPERCELL_4X4, top_nickel(SUPERCELL_4X4), 3),
        "not one site's neighbours",
    ),
]


@pytest.mark.parametrize("material, film_atom, substrate_atoms, match", INTERFACE_DISPLACE_FILM_TO_SITE_INVALID_CASES)
def test_interface_displace_film_to_site_invalid(material, film_atom, substrate_atoms, match):
    with pytest.raises(ValueError, match=match):
        interface_displace_film_to_site(material, film_atom=film_atom, substrate_atoms=substrate_atoms)


GET_FILM_SITE_OCCUPATION_CASES = [
    (interface_displace_film_to_site(INTERFACE, film_atom=4, substrate_atoms=[2]), 4, "atop"),
    (
        interface_displace_film_to_site(SUPERCELL_2X2, film_atom=CARBON_2X2, substrate_atoms=[2, 7]),
        CARBON_2X2,
        "bridge",
    ),
    (
        interface_displace_film_to_site(SUPERCELL_2X2, film_atom=CARBON_2X2, substrate_atoms=[2, 7, 12]),
        CARBON_2X2,
        "hcp",
    ),
]


@pytest.mark.parametrize("placed, film_atom, expected_site_name", GET_FILM_SITE_OCCUPATION_CASES)
def test_get_film_site_occupation(placed, film_atom, expected_site_name):
    assert get_film_site_occupation(placed)[film_atom] == expected_site_name


def substrate_only() -> Material:
    material = INTERFACE.clone()
    material.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
    return material


def film_only() -> Material:
    material = INTERFACE.clone()
    material.basis.filter_atoms_by_labels([InterfacePartsEnum.FILM.value])
    return material


GET_FILM_SITE_OCCUPATION_INVALID_CASES = [
    (substrate_only(), "not an interface"),
    (film_only(), "not an interface"),
]


@pytest.mark.parametrize("material, match", GET_FILM_SITE_OCCUPATION_INVALID_CASES)
def test_get_film_site_occupation_invalid(material, match):
    with pytest.raises(ValueError, match=match):
        get_film_site_occupation(material)
