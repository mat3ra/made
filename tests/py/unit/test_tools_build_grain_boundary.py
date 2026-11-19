import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface.grain_boundary import GrainBoundaryPlanarAnalyzer
from mat3ra.made.tools.build.defective_structures.one_dimensional.grain_boundary_linear.helpers import (
    create_grain_boundary_linear,
)
from mat3ra.made.tools.build.defective_structures.two_dimensional.grain_boundary_planar.builder import (
    GrainBoundaryPlanarBuilder,
)
from mat3ra.made.tools.build.defective_structures.two_dimensional.grain_boundary_planar.configuration import (
    GrainBoundaryPlanarConfiguration,
)
from mat3ra.made.tools.build.defective_structures.two_dimensional.grain_boundary_planar.helpers import (
    create_grain_boundary_planar,
)

from .fixtures.bulk import BULK_Si_CONVENTIONAL
from .fixtures.grain_boundary import GRAIN_BOUNDARY_LINEAR_SI, GRAIN_BOUNDARY_SI_001_011
from .fixtures.monolayer import GRAPHENE
from .utils import assert_two_entities_deep_almost_equal


@pytest.mark.parametrize(
    "material_config, phase_1_miller, phase_2_miller, gap, translation_vector, max_area, expected_material_config",
    [
        (
            BULK_Si_CONVENTIONAL,
            (0, 0, 1),
            (0, 1, 1),
            2.0,
            [2.0, 1.0],
            220,
            GRAIN_BOUNDARY_SI_001_011,
        ),
    ],
)
def test_create_grain_boundary_planar(
    material_config, phase_1_miller, phase_2_miller, gap, translation_vector, max_area, expected_material_config
):
    material = Material.create(material_config)

    grain_boundary = create_grain_boundary_planar(
        phase_1_material=material,
        phase_1_miller_indices=phase_1_miller,
        phase_2_miller_indices=phase_2_miller,
        phase_1_thickness=1,
        phase_2_thickness=1,
        translation_vector=translation_vector,
        gap=gap,
        max_area=max_area,
    )

    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)


@pytest.mark.parametrize(
    "material_config, phase_1_miller, phase_2_miller, gap, translation_vector, max_area, expected_material_config",
    [
        (
            BULK_Si_CONVENTIONAL,
            (0, 0, 1),
            (0, 1, 1),
            2.0,
            [2.0, 1.0],
            220,
            GRAIN_BOUNDARY_SI_001_011,
        ),
    ],
)
def test_grain_boundary_builder(
    material_config, phase_1_miller, phase_2_miller, gap, translation_vector, max_area, expected_material_config
):
    phase_1_material = Material.create(material_config)
    phase_2_material = Material.create(material_config)

    analyzer = GrainBoundaryPlanarAnalyzer(
        phase_1_material=phase_1_material,
        phase_2_material=phase_2_material,
        phase_1_miller_indices=phase_1_miller,
        phase_2_miller_indices=phase_2_miller,
        phase_1_thickness=1,
        phase_2_thickness=1,
        max_area=max_area,
    )

    strained_config = analyzer.get_grain_boundary_configuration_by_match_id(0)

    config = GrainBoundaryPlanarConfiguration.from_parameters(
        phase_1_configuration=strained_config.substrate_configuration,
        phase_2_configuration=strained_config.film_configuration,
        xy_shift=translation_vector,
        gaps=[gap, gap],
    )

    builder = GrainBoundaryPlanarBuilder()
    grain_boundary = builder.get_material(config)

    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)


@pytest.mark.parametrize(
    "config_params, builder_params_dict, expected_material_config",
    [
        (
            {"film_config": GRAPHENE, "twist_angle": 13.0, "gap": 1.0},
            {
                "max_repetition_int": 5,
                "angle_tolerance": 0.5,
                "return_first_match": True,
            },
            GRAIN_BOUNDARY_LINEAR_SI,
        ),
    ],
)
def test_create_grain_boundary_linear(config_params, builder_params_dict, expected_material_config):
    config_params["film"] = Material.create(config_params.pop("film_config"))
    grain_boundary = create_grain_boundary_linear(
        material=config_params["film"],
        target_angle=config_params["twist_angle"],
        gap=config_params["gap"],
        use_conventional_cell=False,
        **builder_params_dict,
    )

    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)
