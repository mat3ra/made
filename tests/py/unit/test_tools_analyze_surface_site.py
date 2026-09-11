from typing import Final

import numpy as np
import pytest
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer, get_film_site_occupation
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.zsl.helpers import (
    create_interface_zsl,
)
from mat3ra.made.tools.build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum

from .fixtures.bulk import BULK_GRAPHENE, BULK_Ni_PRIMITIVE
from .fixtures.slab import CU001_SLAB, CU110_SLAB, MOS2_MONOLAYER, NI111_SLAB

SURFACE_SITE_ANALYZER_SITES_CASES = [
    (
        NI111_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[1.2395, 0.7156]],
            "bridge": [[1.8592, 1.789], [2.479, 0.7156], [3.0987, 1.789]],
            "fcc": [[0.0, 0.0]],
            "hcp": [[2.479, 1.4312]],
        },
    ),
    (
        NI111_SLAB,
        SurfaceTypesEnum.BOTTOM,
        {
            "atop": [[0.0, 0.0]],
            "bridge": [[0.6197, 1.0734], [1.2395, 0.0], [1.8592, 1.0734]],
            "fcc": [[1.2395, 0.7156]],
            "hcp": [[2.479, 1.4312]],
        },
    ),
    (
        CU001_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 0.0], [1.8106, 1.8106]],
            "bridge": [[0.9053, 0.9053], [0.9053, 2.7159], [2.7159, 0.9053], [2.7159, 2.7159]],
            "hollow": [[0.0, 1.8106], [1.8106, 0.0]],
        },
    ),
    (
        CU110_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 1.2803], [0.0, 3.8409]],
            "bridge": [[0.0, 0.0], [0.0, 2.5606], [1.8106, 1.2803], [1.8106, 3.8409]],
            "hollow": [[1.8106, 0.0], [1.8106, 2.5606]],
        },
    ),
    (
        MOS2_MONOLAYER,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 1.8453]],
            "bridge": [[0.7991, 0.4613], [2.3972, 0.4613], [1.5981, 1.8453]],
            "hcp": [[1.5981, 0.9227]],
            "hollow": [[0.0, 0.0]],
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


ANALYZER: Final = SurfaceSiteAnalyzer(material=NI111_SLAB)
ATOP_XY: Final = np.array(ANALYZER.sites["atop"][0])
OFF_SITE_XY: Final = ATOP_XY + np.array(ANALYZER.get_displacement_to_site(ATOP_XY, "fcc")[:2]) / 2

GET_SITE_NAME_CASES = [
    (ATOP_XY, "atop"),
    (np.array(ANALYZER.sites["hcp"][0]), "hcp"),
    (OFF_SITE_XY, None),
]


@pytest.mark.parametrize("coordinate_xy, expected_site_name", GET_SITE_NAME_CASES)
def test_get_site_name(coordinate_xy, expected_site_name):
    assert ANALYZER.get_site_name(coordinate_xy) == expected_site_name


def test_get_displacement_to_site():
    hcp_xy = np.array(ANALYZER.sites["hcp"][0])
    shift = ANALYZER.get_displacement_to_site(hcp_xy, "fcc")
    assert shift[2] == 0.0
    assert ANALYZER.get_site_name(hcp_xy + np.array(shift[:2])) == "fcc"


def test_get_displacement_to_site_invalid():
    with pytest.raises(ValueError):
        ANALYZER.get_displacement_to_site(ATOP_XY, "hollow")


GR_NI_111_INTERFACE: Final = create_interface_zsl(
    substrate_crystal=BULK_Ni_PRIMITIVE,
    film_crystal=BULK_GRAPHENE,
    substrate_miller_indices=(1, 1, 1),
    film_miller_indices=(0, 0, 1),
    substrate_number_of_layers=3,
    film_number_of_layers=1,
    gap=3.0,
    vacuum=10.0,
    max_area=90,
    max_area_ratio_tol=0.09,
    max_length_tol=0.05,
    max_angle_tol=0.02,
    use_conventional_cell=True,
    reduce_result_cell=False,
    reduce_result_cell_to_primitive=True,
)


def test_get_film_site_occupation():
    assert get_film_site_occupation(GR_NI_111_INTERFACE) == {3: "atop", 4: "hcp"}


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
