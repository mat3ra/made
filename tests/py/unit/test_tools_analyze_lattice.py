import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.lattice import LatticeMaterialAnalyzer, get_lattice_type

from .fixtures.bulk import BULK_GRAPHITE, BULK_Hf2O_MCL, BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVE, BULK_Si_PRIMITIVIZED
from .fixtures.interface.gaas_dia import (
    GALLIUM_ARSENIDE_DIAMOND_INTERFACE,
    GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE,
    GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE_GH_WF,
)
from .fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from .utils import (
    OSPlatform,
    assert_interfaces_almost_equal,
    assert_two_entities_deep_almost_equal,
    get_platform_specific_value,
)


@pytest.mark.parametrize(
    "material_config, expected_conventional_material_config, expected_primitive_material_config",
    [
        (BULK_Si_PRIMITIVE, BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVIZED),
        (BULK_Si_CONVENTIONAL, BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVIZED),
    ],
)
def test_get_primitive_lattice(
    material_config, expected_conventional_material_config, expected_primitive_material_config
):
    material = Material.create(material_config)
    lattice_material_analyzer = LatticeMaterialAnalyzer(material=material)
    conventional_cell = lattice_material_analyzer.material_with_conventional_lattice
    assert_two_entities_deep_almost_equal(conventional_cell, expected_conventional_material_config)

    primitive_cell_generated = lattice_material_analyzer.material_with_primitive_lattice
    assert_two_entities_deep_almost_equal(primitive_cell_generated, expected_primitive_material_config)


@pytest.mark.parametrize(
    "material_config, keep_orientation, expected_primitive",
    [
        (
            GALLIUM_ARSENIDE_DIAMOND_INTERFACE,
            True,
            {
                OSPlatform.DARWIN: GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE,
                OSPlatform.OTHER: GALLIUM_ARSENIDE_DIAMOND_INTERFACE_PRIMITIVE_GH_WF,
            },
        ),
    ],
)
def test_get_primitive_lattice_standard(material_config, keep_orientation, expected_primitive):
    original_material = Material.create(material_config)
    analyzer = LatticeMaterialAnalyzer(material=original_material)
    corrected_primitive_material = analyzer.get_material_with_primitive_lattice_standard(
        keep_orientation=keep_orientation
    )
    expected_primitive_material = get_platform_specific_value(expected_primitive)
    assert_interfaces_almost_equal(corrected_primitive_material, expected_primitive_material)


@pytest.mark.parametrize(
    "material, expected_lattice_type",
    [
        (BULK_Si_PRIMITIVE, "FCC"),
        (BULK_Si_CONVENTIONAL, "FCC"),
        (GRAPHENE_NICKEL_INTERFACE_TOP_HCP, "HEX"),
        (BULK_Hf2O_MCL, "MCL"),
        (BULK_GRAPHITE, "HEX"),
    ],
)
def test_analyze_lattice_type(material, expected_lattice_type):
    result = get_lattice_type(material)
    assert result.value == expected_lattice_type
