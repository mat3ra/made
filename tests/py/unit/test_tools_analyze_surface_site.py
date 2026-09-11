import copy
from typing import Any, Dict, Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer
from mat3ra.made.tools.build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from unit.fixtures.surface_nets import RECTANGULAR_NET, SQUARE_NET


def substrate_of(config: Dict[str, Any]) -> Material:
    material = Material.create(config)
    material.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
    return material


def cartesian_xy(config: Dict[str, Any], atom_index: int) -> np.ndarray:
    material = Material.create(config)
    material.to_cartesian()
    return np.array(material.coordinates_array[atom_index][:2])


def shifted_by_one_cell(config: Dict[str, Any]) -> Dict[str, Any]:
    """The same substrate with every atom moved by +1 along a — positions on and past the boundary."""
    moved = copy.deepcopy(config)
    for item in moved["basis"]["coordinates"]:
        item["value"] = [item["value"][0] + 1.0, item["value"][1], item["value"][2]]
    return moved


def reversed_basis(config: Dict[str, Any]) -> Dict[str, Any]:
    reordered = copy.deepcopy(config)
    for key in ("elements", "coordinates", "labels"):
        items = list(reversed(reordered["basis"][key]))
        reordered["basis"][key] = [{"id": i, "value": item["value"]} for i, item in enumerate(items)]
    return reordered


def site_counts(analyzer: SurfaceSiteAnalyzer) -> Dict[str, int]:
    return {name: len(points) for name, points in analyzer.sites.items()}


SUBSTRATE_1X1: Final = substrate_of(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
SUBSTRATE_2X2: Final = create_supercell(SUBSTRATE_1X1, scaling_factor=[2, 2, 1])
SUBSTRATE_REVERSED_BASIS: Final = substrate_of(reversed_basis(GRAPHENE_NICKEL_INTERFACE_TOP_HCP))
SUBSTRATE_SHIFTED_BY_ONE_CELL: Final = substrate_of(shifted_by_one_cell(GRAPHENE_NICKEL_INTERFACE_TOP_HCP))
SQUARE_NET_MATERIAL: Final = Material.create(SQUARE_NET)
RECTANGULAR_NET_MATERIAL: Final = Material.create(RECTANGULAR_NET)

SITE_COUNTS_1X1: Final = {"atop": 1, "bridge": 3, "fcc": 1, "hcp": 1}
SITE_COUNTS_2X2: Final = {name: 4 * count for name, count in SITE_COUNTS_1X1.items()}
SITE_COUNTS_NET: Final = {"atop": 1, "bridge": 2, "hollow": 1}

SURFACE_SITE_ANALYZER_CASES = [
    (SUBSTRATE_1X1, SITE_COUNTS_1X1),
    (SUBSTRATE_2X2, SITE_COUNTS_2X2),
    (SUBSTRATE_REVERSED_BASIS, SITE_COUNTS_1X1),
    (SUBSTRATE_SHIFTED_BY_ONE_CELL, SITE_COUNTS_1X1),
    (SQUARE_NET_MATERIAL, SITE_COUNTS_NET),
    (RECTANGULAR_NET_MATERIAL, SITE_COUNTS_NET),
]


@pytest.mark.parametrize("material, expected_site_counts", SURFACE_SITE_ANALYZER_CASES)
def test_surface_site_analyzer(material, expected_site_counts):
    assert site_counts(SurfaceSiteAnalyzer(material=material)) == expected_site_counts


ANALYZER: Final = SurfaceSiteAnalyzer(material=SUBSTRATE_1X1)
CARBON_ATOP_XY: Final = cartesian_xy(GRAPHENE_NICKEL_INTERFACE_TOP_HCP, 3)
CARBON_HCP_XY: Final = cartesian_xy(GRAPHENE_NICKEL_INTERFACE_TOP_HCP, 4)
ATOP_XY: Final = np.array(ANALYZER.sites["atop"][0])
HALFWAY_TO_FCC_XY: Final = ATOP_XY + np.array(ANALYZER.get_displacement_to_site(ATOP_XY, "fcc")[:2]) / 2

GET_SITE_NAME_CASES = [
    (CARBON_ATOP_XY, "atop"),
    (CARBON_HCP_XY, "hcp"),
    (HALFWAY_TO_FCC_XY, None),
]


@pytest.mark.parametrize("coordinate_xy, expected_site_name", GET_SITE_NAME_CASES)
def test_get_site_name(coordinate_xy, expected_site_name):
    assert ANALYZER.get_site_name(coordinate_xy) == expected_site_name


GET_DISPLACEMENT_TO_SITE_CASES = [
    (CARBON_HCP_XY, "fcc"),
]


@pytest.mark.parametrize("coordinate_xy, site_name", GET_DISPLACEMENT_TO_SITE_CASES)
def test_get_displacement_to_site(coordinate_xy, site_name):
    shift = ANALYZER.get_displacement_to_site(coordinate_xy, site_name)
    assert shift[2] == 0.0
    assert ANALYZER.get_site_name(coordinate_xy + np.array(shift[:2])) == site_name


def test_get_displacement_to_site_invalid():
    with pytest.raises(ValueError):
        ANALYZER.get_displacement_to_site(CARBON_HCP_XY, "hollow")
