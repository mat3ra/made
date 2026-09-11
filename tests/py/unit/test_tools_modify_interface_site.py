from typing import Final, List

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import get_film_site_occupation
from mat3ra.made.tools.analyze.other import (
    get_atom_indices_within_radius_pbc,
    get_closest_site_id_from_coordinate_within_radius,
)
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.modify import interface_displace_film_to_site
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP

INTERFACE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)  # Ni 0-2 (2 on top), C 3 (atop), C 4 (hcp)
MOS2: Final = {
    "name": "MoS2 monolayer",
    "basis": {
        "elements": [{"id": 0, "value": "Mo"}, {"id": 1, "value": "S"}, {"id": 2, "value": "S"}],
        "coordinates": [
            {"id": 0, "value": [0.3333, 0.6667, 0.5]},
            {"id": 1, "value": [0.6667, 0.3333, 0.42]},
            {"id": 2, "value": [0.6667, 0.3333, 0.58]},
        ],
        "units": "crystal",
    },
    "lattice": {
        "a": 3.19,
        "b": 3.19,
        "c": 20.0,
        "alpha": 90,
        "beta": 90,
        "gamma": 120,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "HEX",
    },
}


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


def test_atoms_within_a_radius_of_a_coordinate_nearest_first():
    mos2 = Material.create(MOS2)
    assert get_atom_indices_within_radius_pbc(
        mos2, coordinate=[0.6667, 0.3333, 0.45], radius=1.0, chemical_element="S"
    ) == [1]
    assert get_atom_indices_within_radius_pbc(
        mos2, coordinate=[0.6667, 0.3333, 0.45], radius=3.0, chemical_element="S"
    ) == [1, 2]
    assert (
        get_atom_indices_within_radius_pbc(mos2, coordinate=[0.6667, 0.3333, 0.45], radius=0.1, chemical_element="S")
        == []
    )


def test_closest_site_within_radius_by_element():
    mos2 = Material.create(MOS2)
    assert get_closest_site_id_from_coordinate_within_radius(mos2, [0.25, 0.75, 0.5], 1.0, "Mo") == 0
    assert get_closest_site_id_from_coordinate_within_radius(mos2, [0.6, 0.3, 0.58], 1.0, "S") == 2
    with pytest.raises(ValueError, match=r"No Mo within 0.5 A .* nearest Mo is 1\.\d\d A away"):
        get_closest_site_id_from_coordinate_within_radius(mos2, [0.0, 0.0, 0.5], 0.5, "Mo")


def test_film_over_one_substrate_atom_is_atop():
    placed = interface_displace_film_to_site(INTERFACE, film_atom=4, substrate_atoms=[2])
    assert get_film_site_occupation(placed)[4] == "atop"


def test_film_over_two_neighbours_is_a_bridge():
    supercell = create_supercell(INTERFACE, scaling_factor=[2, 2, 1])
    # The 2x2 cell's four equivalent top-Ni images; any two are natural neighbours.
    assert top_nickel(supercell) == [2, 7, 12, 17]
    carbon = first_carbon(supercell)
    placed = interface_displace_film_to_site(supercell, carbon, [2, 7])
    assert get_film_site_occupation(placed)[carbon] == "bridge"


def test_film_over_three_neighbours_is_a_hollow():
    supercell = create_supercell(INTERFACE, scaling_factor=[2, 2, 1])
    assert top_nickel(supercell) == [2, 7, 12, 17]
    carbon = first_carbon(supercell)
    placed = interface_displace_film_to_site(supercell, carbon, [2, 7, 12])
    assert get_film_site_occupation(placed)[carbon] == "hcp"


def test_rejects_substrate_atoms_that_are_not_one_site():
    supercell = create_supercell(INTERFACE, scaling_factor=[4, 4, 1])
    with pytest.raises(ValueError, match="not one site's neighbours"):
        interface_displace_film_to_site(
            supercell, first_carbon(supercell), far_apart(supercell, top_nickel(supercell), 3)
        )


def test_rejects_wrong_parts():
    with pytest.raises(ValueError, match="not in the film"):
        interface_displace_film_to_site(INTERFACE, film_atom=0, substrate_atoms=[2])
    with pytest.raises(ValueError, match="Not all"):
        interface_displace_film_to_site(INTERFACE, film_atom=3, substrate_atoms=[4])


def test_rejects_wrong_arity():
    with pytest.raises(ValueError, match="one, two or three"):
        interface_displace_film_to_site(INTERFACE, film_atom=4, substrate_atoms=[])


def test_rejects_out_of_range_indices():
    with pytest.raises(ValueError, match="out of range"):
        interface_displace_film_to_site(INTERFACE, film_atom=99, substrate_atoms=[2])
    with pytest.raises(ValueError, match="out of range"):
        interface_displace_film_to_site(INTERFACE, film_atom=3, substrate_atoms=[99])


def test_rejects_substrate_atoms_not_in_one_layer():
    with pytest.raises(ValueError, match="not in one layer"):
        interface_displace_film_to_site(INTERFACE, film_atom=3, substrate_atoms=[0, 1])


def test_film_site_occupation_of_a_non_interface_raises():
    substrate_only = INTERFACE.clone()
    substrate_only.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
    with pytest.raises(ValueError, match="not an interface"):
        get_film_site_occupation(substrate_only)
