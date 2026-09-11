from typing import Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.crystal_site.surface_site_analyzer import SurfaceSiteAnalyzer, get_film_site_occupation
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.zsl.helpers import (
    create_interface_zsl,
)
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.helpers import create_slab
from mat3ra.made.tools.build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.standata.materials import Materials

from .fixtures.bulk import BULK_GRAPHENE, BULK_Cu, BULK_Ni_PRIMITIVE

NI111_SLAB: Final = create_slab(
    crystal=BULK_Ni_PRIMITIVE, miller_indices=(1, 1, 1), number_of_layers=3, vacuum=10.0, use_conventional_cell=False
)
CU001_SLAB: Final = create_slab(crystal=BULK_Cu, miller_indices=(0, 0, 1), number_of_layers=1, vacuum=10.0)
CU110_SLAB: Final = create_slab(crystal=BULK_Cu, miller_indices=(1, 1, 0), number_of_layers=1, vacuum=10.0)
MOS2_MONOLAYER: Final = Material.create(Materials.get_by_name_and_categories("MoS2", "2D"))

SURFACE_SITE_ANALYZER_SITES_CASES = [
    (NI111_SLAB, SurfaceTypesEnum.TOP, {"atop": [[1.2394, 0.7155]], "fcc": [[0.0, 0.0]], "hcp": [[2.4787, 1.4311]]}),
    (
        # Bottom surface: atop is the bottom layer's own atom; fcc/hcp count layers upward from it,
        # so the naming swaps versus the top view (fcc <-> hcp) without changing which xy is which.
        NI111_SLAB,
        SurfaceTypesEnum.BOTTOM,
        {"atop": [[0.0, 0.0]], "fcc": [[1.2394, 0.7155]], "hcp": [[2.4791, 1.4313]]},
    ),
    (
        CU001_SLAB,
        SurfaceTypesEnum.TOP,
        {"atop": [[0.0, 0.0], [1.8106, 1.8106]], "hollow": [[0.0, 1.8106], [1.8106, 0.0]]},
    ),
    (
        CU110_SLAB,
        SurfaceTypesEnum.TOP,
        {
            "atop": [[0.0, 1.2803], [0.0, 3.8409]],
            # two distinct bridge-to-atop distances: 1.2803 along the close-packed rows, 1.8106 across.
            "bridge": [[0.0, 0.0], [0.0, 2.5606], [1.8106, 1.2803], [1.8106, 3.8409]],
            "hollow": [[1.8106, 0.0], [1.8106, 2.5606]],
        },
    ),
    (
        MOS2_MONOLAYER,
        SurfaceTypesEnum.TOP,
        {"atop": [[0.0, 1.8454]], "hcp": [[1.5978, 0.9229]], "hollow": [[0.0, 0.0]]},
    ),
]


@pytest.mark.parametrize("material, surface, expected_sites", SURFACE_SITE_ANALYZER_SITES_CASES)
def test_surface_site_analyzer_sites(material, surface, expected_sites):
    """Site coordinates for a subset of site types, not only counts — a systematic displacement of
    every site of one type would otherwise go unnoticed."""
    sites = SurfaceSiteAnalyzer(material=material, surface=surface).sites
    for name, points in expected_sites.items():
        rounded = sorted(np.round(sites[name], 3).tolist())
        assert np.allclose(rounded, sorted(points), atol=1e-3)


def test_surface_site_analyzer_no_fcc_or_hcp_on_square_net():
    """Cu(001) hollows are 4-fold: no third layer to distinguish fcc from hcp."""
    sites = SurfaceSiteAnalyzer(material=CU001_SLAB).sites
    assert "fcc" not in sites
    assert "hcp" not in sites


ANALYZER: Final = SurfaceSiteAnalyzer(material=NI111_SLAB)
ATOP_XY: Final = np.array(ANALYZER.sites["atop"][0])
HALFWAY_TO_FCC_XY: Final = ATOP_XY + np.array(ANALYZER.get_displacement_to_site(ATOP_XY, "fcc")[:2]) / 2

GET_SITE_NAME_CASES = [
    (ATOP_XY, "atop"),
    (np.array(ANALYZER.sites["hcp"][0]), "hcp"),
    (HALFWAY_TO_FCC_XY, None),
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
