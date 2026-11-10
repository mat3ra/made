import pytest
from mat3ra.esse.models.materials_category_components.operations.core.combinations.merge import MergeMethodsEnum
from mat3ra.made.material import Material
from mat3ra.made.tools.build_components import BaseConfigurationPydantic, MaterialWithBuildMetadata
from mat3ra.made.tools.build_components.operations.core.combinations.merge.build_parameters import (
    MergeBuilderParameters,
)
from mat3ra.made.tools.build_components.operations.core.combinations.merge.builder import MergeBuilder
from mat3ra.made.tools.build_components.operations.core.combinations.merge.configuration import MergeConfiguration
from mat3ra.made.tools.operations.core.binary import merge
from mat3ra.utils import assertion as assertion_utils
from unit.fixtures.bulk import BULK_Ge_CONVENTIONAL, BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVE
from unit.fixtures.cuts import (
    CAVITY_MATERIAL_BASIS,
    FULL_MATERIAL,
    MERGED_CAVITY_SECTION_BASIS,
    MERGED_SECTION_CAVITY_BASIS,
    SECTION_MATERIAL_BASIS,
    SECTION_MATERIAL_BASIS_EXTRA_ATOM,
)
from unit.fixtures.merge import MERGED_BULK_Si_Ge
from unit.fixtures.point_defects import (
    INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si,
    SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
    VACANCY_DEFECT_BULK_PRIMITIVE_Si,
)
from unit.utils import assert_two_entities_deep_almost_equal

section = Material.create({**FULL_MATERIAL, **SECTION_MATERIAL_BASIS})
cavity = Material.create({**FULL_MATERIAL, **CAVITY_MATERIAL_BASIS})
section_with_extra_atom = Material.create({**FULL_MATERIAL, **SECTION_MATERIAL_BASIS_EXTRA_ATOM})


@pytest.mark.parametrize(
    "materials_to_merge, expected_basis, expected_basis_reverse",
    [
        (
            [section, cavity],
            MERGED_CAVITY_SECTION_BASIS,
            MERGED_SECTION_CAVITY_BASIS,
        ),
        (
            [section_with_extra_atom, cavity],
            MERGED_CAVITY_SECTION_BASIS,
            MERGED_SECTION_CAVITY_BASIS,
        ),
    ],
)
def test_merge_materials(materials_to_merge, expected_basis, expected_basis_reverse):
    merged_material = merge(materials_to_merge)
    merged_material_reverse = merge(materials_to_merge[::-1])
    assertion_utils.assert_deep_almost_equal(merged_material.basis, expected_basis)
    assertion_utils.assert_deep_almost_equal(merged_material_reverse.basis, expected_basis_reverse)


def test_configuration():
    class MockConfiguration(BaseConfigurationPydantic):
        value_1: str = "test"
        value_2: int = 0

    class CompositeMockConfiguration(BaseConfigurationPydantic):
        component: MockConfiguration = MockConfiguration(value_1="component_value")

    mock_config = MockConfiguration(value_1="component_value", value_2=42)
    configuration = CompositeMockConfiguration(component=mock_config)
    assert isinstance(configuration.component, MockConfiguration)
    assert configuration.component.value_1 == "component_value"
    assert configuration.component.value_2 == 42

    config_dict = configuration.to_dict()
    assert config_dict["component"]["value_1"] == "component_value"
    assert config_dict["component"]["value_2"] == 42

    configuration_from_dict = CompositeMockConfiguration(**config_dict)
    assert isinstance(configuration_from_dict.component, MockConfiguration)
    assert configuration_from_dict.component.value_1 == "component_value"
    assert configuration_from_dict.component.value_2 == 42


MERGE_TEST_PARAMS = [
    (
        BULK_Si_CONVENTIONAL,
        BULK_Ge_CONVENTIONAL,
        MergeMethodsEnum.REPLACE,
        {"material_name": "Si-Ge Merged", "distance_tolerance": 0.1, "merge_dangerously": True},
        MERGED_BULK_Si_Ge,
    ),
]


@pytest.mark.parametrize(
    "material1_config, material2_config, merge_method, builder_params, expected_material_config", MERGE_TEST_PARAMS
)
def test_merge_builder(material1_config, material2_config, merge_method, builder_params, expected_material_config):
    material1 = MaterialWithBuildMetadata.create(material1_config)
    material2 = MaterialWithBuildMetadata.create(material2_config)

    merge_config = MergeConfiguration(merge_components=[material1, material2], merge_method=merge_method)

    builder_parameters = MergeBuilderParameters(**builder_params)
    builder = MergeBuilder(build_parameters=builder_parameters)

    merged_material = builder.get_material(merge_config)

    assert_two_entities_deep_almost_equal(merged_material, expected_material_config)


@pytest.mark.parametrize(
    "material1_config, material2_config, merge_method, expected_material_config",
    [
        (
            VACANCY_DEFECT_BULK_PRIMITIVE_Si,
            INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si,
            MergeMethodsEnum.ADD,
            INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si,
        ),
        (
            VACANCY_DEFECT_BULK_PRIMITIVE_Si,
            SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
            MergeMethodsEnum.REPLACE,
            SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
        ),
        (
            SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
            BULK_Si_PRIMITIVE,
            MergeMethodsEnum.YIELD,
            SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
        ),
    ],
)
def test_merge_methods(material1_config, material2_config, merge_method, expected_material_config):
    material1 = MaterialWithBuildMetadata.create(material1_config)
    material2 = MaterialWithBuildMetadata.create(material2_config)
    merge_config = MergeConfiguration(merge_components=[material1, material2], merge_method=merge_method)
    builder = MergeBuilder(build_parameters=MergeBuilderParameters(merge_dangerously=True))
    merged_material = builder.get_material(merge_config)

    # Custom comparison that ignores atom IDs, metadata, and name
    def compare_materials_ignoring_ids(actual, expected):
        actual_dict = actual.to_dict()
        expected_dict = expected.to_dict()

        # Remove IDs from coordinates and elements
        for material_dict in [actual_dict, expected_dict]:
            for coord in material_dict["basis"]["coordinates"]:
                coord.pop("id", None)
            for elem in material_dict["basis"]["elements"]:
                elem.pop("id", None)
            # Remove metadata and name differences
            material_dict.pop("metadata", None)
            material_dict.pop("name", None)
            material_dict["lattice"].pop("type", None)

        # Compare only essential structure
        assert_two_entities_deep_almost_equal(actual_dict, expected_dict)

    expected_material = Material.create(expected_material_config)
    compare_materials_ignoring_ids(merged_material, expected_material)
