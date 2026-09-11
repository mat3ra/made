import copy
from typing import Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from pydantic import ValidationError
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP


def substrate_of(config: dict) -> Material:
    material = Material.create(config)
    material.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
    return material


def cartesian_xy(config: dict, atom_index: int) -> np.ndarray:
    material = Material.create(config)
    material.to_cartesian()
    return np.array(material.coordinates_array[atom_index][:2])


def reversed_basis(config: dict) -> dict:
    reordered = copy.deepcopy(config)
    for key in ("elements", "coordinates", "labels"):
        items = list(reversed(reordered["basis"][key]))
        reordered["basis"][key] = [{"id": i, "value": item["value"]} for i, item in enumerate(items)]
    return reordered


SUBSTRATE: Final = substrate_of(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
LATTICE_A: Final = SUBSTRATE.lattice.a
ANALYZER: Final = SurfaceSiteAnalyzer(material=SUBSTRATE)
# The fixture's name says where its carbons sit: one atop, one over the hcp hollow.
CARBON_ATOP_XY: Final = cartesian_xy(GRAPHENE_NICKEL_INTERFACE_TOP_HCP, 3)
CARBON_HCP_XY: Final = cartesian_xy(GRAPHENE_NICKEL_INTERFACE_TOP_HCP, 4)
SITE_COUNTS_1X1: Final = {"atop": 1, "bridge": 3, "fcc": 1, "hcp": 1}

# Two-layer square net: one atop, two bridges, and a four-fold hollow that is not fcc or hcp.
SQUARE_NET: Final = {
    "name": "square net",
    "basis": {
        "elements": [{"id": 0, "value": "Cu"}, {"id": 1, "value": "Cu"}],
        "coordinates": [{"id": 0, "value": [0.5, 0.5, 0.1]}, {"id": 1, "value": [0.0, 0.0, 0.2]}],
        "units": "crystal",
    },
    "lattice": {
        "a": 2.5,
        "b": 2.5,
        "c": 15.0,
        "alpha": 90,
        "beta": 90,
        "gamma": 90,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TET",
    },
}

# Rectangular net: two distinct nearest-neighbour spacings, so two distinct bridges.
RECTANGULAR_NET: Final = copy.deepcopy(SQUARE_NET)
RECTANGULAR_NET["lattice"]["b"] = 3.0

SITE_NAME_CASES = [
    (CARBON_ATOP_XY, "atop"),
    (CARBON_HCP_XY, "hcp"),
]


def site_counts(analyzer: SurfaceSiteAnalyzer) -> dict:
    return {name: len(points) for name, points in analyzer.sites.items()}


def test_sites_of_the_1x1_ni111_cell():
    assert site_counts(ANALYZER) == SITE_COUNTS_1X1


def test_hollows_sit_one_site_step_from_atop():
    atop = np.array(ANALYZER.sites["atop"][0])
    for name in ("fcc", "hcp"):
        shift = np.array(ANALYZER.get_displacement_to_site(atop, name)[:2])
        assert np.isclose(np.linalg.norm(shift), LATTICE_A / np.sqrt(3), atol=1e-3)


@pytest.mark.parametrize("coordinate_xy,expected", SITE_NAME_CASES)
def test_get_site_name(coordinate_xy, expected):
    assert ANALYZER.get_site_name(coordinate_xy) == expected


def test_get_site_name_off_site_is_none():
    atop = np.array(ANALYZER.sites["atop"][0])
    halfway_to_fcc = atop + np.array(ANALYZER.get_displacement_to_site(atop, "fcc")[:2]) / 2
    assert ANALYZER.get_site_name(halfway_to_fcc) is None


def test_get_displacement_to_site_lands_on_it():
    shift = ANALYZER.get_displacement_to_site(CARBON_HCP_XY, "fcc")
    assert shift[2] == 0.0
    assert ANALYZER.get_site_name(CARBON_HCP_XY + np.array(shift[:2])) == "fcc"


def test_get_displacement_to_missing_site_raises():
    with pytest.raises(ValueError):
        ANALYZER.get_displacement_to_site(CARBON_HCP_XY, "hollow")


def test_supercell_names_every_equivalent_site():
    analyzer = SurfaceSiteAnalyzer(material=create_supercell(SUBSTRATE, scaling_factor=[2, 2, 1]))
    assert site_counts(analyzer) == {name: 4 * count for name, count in SITE_COUNTS_1X1.items()}
    for atop_xy in analyzer.sites["atop"]:
        assert analyzer.get_site_name(atop_xy) == "atop"


def test_sites_do_not_depend_on_basis_order():
    analyzer = SurfaceSiteAnalyzer(material=substrate_of(reversed_basis(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)))
    assert site_counts(analyzer) == SITE_COUNTS_1X1
    assert analyzer.get_site_name(CARBON_ATOP_XY) == "atop"
    assert analyzer.get_site_name(CARBON_HCP_XY) == "hcp"


def test_square_net_has_a_four_fold_hollow():
    analyzer = SurfaceSiteAnalyzer(material=Material.create(SQUARE_NET))
    assert site_counts(analyzer) == {"atop": 1, "bridge": 2, "hollow": 1}
    assert analyzer.get_site_name([1.25, 1.25]) == "hollow"


def test_rectangular_net_keeps_both_bridges():
    analyzer = SurfaceSiteAnalyzer(material=Material.create(RECTANGULAR_NET))
    assert site_counts(analyzer) == {"atop": 1, "bridge": 2, "hollow": 1}


def test_analyzer_is_frozen_because_sites_are_cached():
    with pytest.raises(ValidationError):
        ANALYZER.site_match_tolerance = 1.0
