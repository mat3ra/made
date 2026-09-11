from typing import Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer, SurfaceSiteEnum
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP

INTERFACE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
INTERFACE.to_cartesian()
SUBSTRATE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
SUBSTRATE.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
ANALYZER: Final = SurfaceSiteAnalyzer(material=SUBSTRATE)

# Ni(111) 1x1: the three surface sites project onto the three Ni layers, and the fixture's name
# says where the carbons are — one atop, one over the hcp hollow.
CARBON_ATOP_XY: Final = INTERFACE.coordinates_array[3][:2]
CARBON_HCP_XY: Final = INTERFACE.coordinates_array[4][:2]
NEAREST_SITE_DISTANCE: Final = 2.478974 / np.sqrt(3)

SITE_NAME_CASES = [
    (CARBON_ATOP_XY, SurfaceSiteEnum.ATOP.value),
    (CARBON_HCP_XY, SurfaceSiteEnum.HCP.value),
]


def test_all_four_site_types_are_found():
    assert set(ANALYZER.sites) == {"atop", "bridge", "fcc", "hcp"}


def test_sites_are_one_third_of_a_lattice_step_apart():
    atop, hcp, fcc = (np.array(ANALYZER.sites[name]) for name in ("atop", "hcp", "fcc"))
    assert np.isclose(ANALYZER._distance_to_site(atop, hcp.tolist()), NEAREST_SITE_DISTANCE, atol=1e-3)
    assert np.isclose(ANALYZER._distance_to_site(atop, fcc.tolist()), NEAREST_SITE_DISTANCE, atol=1e-3)


@pytest.mark.parametrize("coordinate_xy,expected", SITE_NAME_CASES)
def test_get_site_name(coordinate_xy, expected):
    assert ANALYZER.get_site_name(coordinate_xy) == expected


def test_get_site_name_refuses_a_tie():
    atop = np.array(ANALYZER.sites["atop"])
    midpoint = atop + np.array(ANALYZER.get_displacement_to_site(atop.tolist(), "fcc")[:2]) / 2
    assert ANALYZER.get_site_name(midpoint.tolist()) is None


def test_get_displacement_to_site_lands_on_it():
    shift = ANALYZER.get_displacement_to_site(CARBON_HCP_XY, "fcc")
    assert shift[2] == 0.0
    moved = np.array(CARBON_HCP_XY) + np.array(shift[:2])
    assert ANALYZER.get_site_name(moved.tolist()) == "fcc"
