import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.lattice import LatticeMaterialAnalyzer
from mat3ra.made.tools.analyze.lattice_swap_analyzer import MaterialLatticeSwapAnalyzer

from .fixtures.interface.gaas_dia import (
    GALLIUM_ARSENIDE_DIAMOND_INTERFACE,
    GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE,
)
from .fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP_GH_WF
from .fixtures.slab import SLAB_SrTiO3_011_TERMINATION_O2, SLAB_SrTiO3_011_TERMINATION_SrTiO
from .utils import assert_interfaces_almost_equal, assert_two_entities_deep_almost_equal


@pytest.mark.parametrize(
    "original_material_config, another_material_config, is_swapped",
    [
        (SLAB_SrTiO3_011_TERMINATION_O2, SLAB_SrTiO3_011_TERMINATION_O2, False),
        (SLAB_SrTiO3_011_TERMINATION_O2, SLAB_SrTiO3_011_TERMINATION_SrTiO, True),
    ],
)
def test_flip_detection_between_materials(original_material_config, another_material_config, is_swapped):
    original_material = Material.create(original_material_config)
    another_material = Material.create(another_material_config)

    rotation_analyzer = MaterialLatticeSwapAnalyzer(material=another_material)
    swap_info = rotation_analyzer.detect_swap_from_original(original_material)

    new_lattice = rotation_analyzer.get_corrected_material(another_material).lattice

    assert swap_info.is_swapped == is_swapped
    assert_two_entities_deep_almost_equal(new_lattice, another_material.lattice)


@pytest.mark.parametrize(
    "original_material_config, expected_swapped, expected_primitive, clear_labels",
    [
        (
            GALLIUM_ARSENIDE_DIAMOND_INTERFACE,
            True,
            GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE,
            False,
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_TOP_HCP_GH_WF,
            # The flag follows spglib's choice among equivalent orientations, which varies by machine.
            None,
            None,
            True,
        ),
    ],
)
def test_swap_detection(original_material_config, expected_swapped, expected_primitive, clear_labels):
    original_material = Material.create(original_material_config)
    primitive_material = LatticeMaterialAnalyzer(material=original_material).material_with_primitive_lattice

    analyzer = MaterialLatticeSwapAnalyzer(material=primitive_material)
    swap_info = analyzer.detect_swap_from_original(original_material)

    if expected_swapped is not None:
        assert swap_info.is_swapped is expected_swapped

    if clear_labels:
        original_material.basis.set_labels_from_list([])

    corrected_primitive_material = analyzer.get_corrected_material(original_material)

    if expected_primitive is not None:
        assert_interfaces_almost_equal(corrected_primitive_material, expected_primitive)
    else:
        assert_interfaces_almost_equal(corrected_primitive_material, original_material)
