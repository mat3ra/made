import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.helpers import get_film_buckling, get_film_site_occupation
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer
from mat3ra.made.tools.build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum

from .fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from .fixtures.slab import CU001_SLAB, CU110_SLAB, MOS2_MONOLAYER, NI111_SLAB

SURFACE_SITE_ANALYZER_SITES_CASES = [
    (
        NI111_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.3333, 0.3333, 0.2843]],
            "bridge": [[0.3333, 0.8333, 0.2843], [0.8333, 0.3333, 0.2843], [0.8333, 0.8333, 0.2843]],
            "fcc": [[0.0, 0.0, 0.2843]],
            "hcp": [[0.6667, 0.6667, 0.2843]],
        },
    ),
    (
        NI111_SLAB,
        SurfaceTypesEnum.BOTTOM,
        {
            "atop": [[0.0, 0.0, 0.0]],
            "bridge": [[0.0, 0.5, 0.0], [0.5, 0.0, 0.0], [0.5, 0.5, 0.0]],
            "fcc": [[0.3333, 0.3333, 0.0]],
            "hcp": [[0.6667, 0.6667, 0.0]],
        },
    ),
    (
        CU001_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 0.0, 0.1329], [0.5, 0.5, 0.1329]],
            "bridge": [[0.25, 0.25, 0.1329], [0.25, 0.75, 0.1329], [0.75, 0.25, 0.1329], [0.75, 0.75, 0.1329]],
            "hollow": [[0.0, 0.5, 0.1329], [0.5, 0.0, 0.1329]],
        },
    ),
    (
        CU110_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 0.25, 0.1329], [0.0, 0.75, 0.1329]],
            "bridge": [[0.0, 0.0, 0.1329], [0.0, 0.5, 0.1329], [0.5, 0.25, 0.1329], [0.5, 0.75, 0.1329]],
            "hollow": [[0.5, 0.0, 0.1329], [0.5, 0.5, 0.1329]],
        },
    ),
    (
        MOS2_MONOLAYER,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.3333, 0.6667, 0.5679]],
            "bridge": [[0.3333, 0.1667, 0.5679], [0.8333, 0.1667, 0.5679], [0.8333, 0.6667, 0.5679]],
            "hcp": [[0.6667, 0.3333, 0.5679]],
            "hollow": [[0.0, 0.0, 0.5679]],
        },
    ),
]


@pytest.mark.parametrize("material, surface, expected_sites", SURFACE_SITE_ANALYZER_SITES_CASES)
def test_surface_site_analyzer_sites(material, surface, expected_sites):
    sites = SurfaceSiteAnalyzer(material=material, surface=surface).sites
    assert set(sites) == set(expected_sites)
    for name, points in expected_sites.items():
        rounded = sorted(np.round(sites[name], 3).tolist())
        assert np.allclose(rounded, sorted(points), atol=1e-3)


ANALYZER = SurfaceSiteAnalyzer(material=NI111_SLAB)
ATOP = np.array(ANALYZER.sites["atop"][0])
OFF_SITE = ATOP + np.array(ANALYZER.get_displacement_to_site(ATOP, "fcc")) / 2

GET_SITE_NAME_CASES = [
    (ATOP, "atop"),
    (np.array(ANALYZER.sites["hcp"][0]), "hcp"),
    (OFF_SITE, None),
]


@pytest.mark.parametrize("coordinate, expected_site_name", GET_SITE_NAME_CASES)
def test_get_site_name(coordinate, expected_site_name):
    assert ANALYZER.get_site_name(coordinate) == expected_site_name


def test_get_displacement_to_site():
    hcp = np.array(ANALYZER.sites["hcp"][0])
    shift = ANALYZER.get_displacement_to_site(hcp, "fcc")
    assert np.isclose(shift[2], 0.0, atol=1e-6)
    assert ANALYZER.get_site_name((hcp + np.array(shift)).tolist()) == "fcc"


def test_get_displacement_to_site_invalid():
    with pytest.raises(ValueError):
        ANALYZER.get_displacement_to_site(ATOP, "hollow")


GR_NI_111_INTERFACE = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)


def test_get_film_site_occupation():
    assert get_film_site_occupation(GR_NI_111_INTERFACE) == {3: "atop", 4: "hcp"}


GR_NI_111_SUBSTRATE = GR_NI_111_INTERFACE.clone()
GR_NI_111_SUBSTRATE.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
GR_NI_111_BOTTOM_ANALYZER = SurfaceSiteAnalyzer(material=GR_NI_111_SUBSTRATE, surface=SurfaceTypesEnum.BOTTOM)

# Raise the atop carbon (atom 3) by a known amount, the way interface_displace_part does: clone,
# to_cartesian, shift the one atom's coordinate, to_crystal.
GR_NI_111_RAISED_ATOP_SHIFT = 0.1  # Angstrom
GR_NI_111_RAISED_ATOP_INTERFACE = GR_NI_111_INTERFACE.clone()
GR_NI_111_RAISED_ATOP_INTERFACE.to_cartesian()
GR_NI_111_RAISED_ATOP_COORDINATES = GR_NI_111_RAISED_ATOP_INTERFACE.basis.coordinates.values
GR_NI_111_RAISED_ATOP_COORDINATES[3] = (
    np.array(GR_NI_111_RAISED_ATOP_COORDINATES[3]) + [0, 0, GR_NI_111_RAISED_ATOP_SHIFT]
).tolist()
GR_NI_111_RAISED_ATOP_INTERFACE.set_coordinates(GR_NI_111_RAISED_ATOP_COORDINATES)
GR_NI_111_RAISED_ATOP_INTERFACE.to_crystal()

GET_FILM_BUCKLING_CASES = [
    (GR_NI_111_INTERFACE, None, 0.0),  # top-hcp: atop carbon 3 and hcp carbon 4 sit at the same height
    (GR_NI_111_INTERFACE, GR_NI_111_BOTTOM_ANALYZER, None),  # against the bottom surface: no atom is atop
    (GR_NI_111_RAISED_ATOP_INTERFACE, None, GR_NI_111_RAISED_ATOP_SHIFT),  # atop carbon raised: positive
]


@pytest.mark.parametrize("interface, analyzer, expected_buckling", GET_FILM_BUCKLING_CASES)
def test_get_film_buckling(interface, analyzer, expected_buckling):
    buckling = get_film_buckling(interface, analyzer)
    if expected_buckling is None:
        assert buckling is None
    else:
        assert np.isclose(buckling, expected_buckling, atol=1e-6)


def test_get_film_site_occupation_no_film_invalid():
    substrate_only = GR_NI_111_INTERFACE.clone()
    substrate_only.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
    with pytest.raises(ValueError):
        get_film_site_occupation(substrate_only)


def test_get_film_site_occupation_no_substrate_invalid():
    film_only = GR_NI_111_INTERFACE.clone()
    film_only.basis.filter_atoms_by_labels([InterfacePartsEnum.FILM.value])
    with pytest.raises(ValueError):
        get_film_site_occupation(film_only)
