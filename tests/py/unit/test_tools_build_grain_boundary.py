from collections import Counter

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface.grain_boundary import GrainBoundaryPlanarAnalyzer
from mat3ra.made.tools.analyze.rings import RingsMaterialAnalyzer
from mat3ra.made.tools.build.defective_structures.one_dimensional.grain_boundary_linear.builder import (
    GrainBoundaryLinearBuilder,
)
from mat3ra.made.tools.build.defective_structures.one_dimensional.grain_boundary_linear.configuration import (
    GrainBoundaryLinearConfiguration,
)
from mat3ra.made.tools.build.defective_structures.one_dimensional.grain_boundary_linear.helpers import (
    create_grain_boundary_linear,
    create_grain_boundary_linear_with_core,
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
from mat3ra.standata.materials import Materials

from .fixtures.bulk import BULK_Si_CONVENTIONAL
from .fixtures.grain_boundary import (
    GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7,
    GRAIN_BOUNDARY_LINEAR_SI,
    GRAIN_BOUNDARY_SI_001_011,
    GRAIN_BOUNDARY_SI_001_011_GH,
)
from .fixtures.monolayer import GRAPHENE
from .utils import OSPlatform, assert_two_entities_deep_almost_equal, get_platform_specific_value

GRAPHENE_2D = Materials.get_by_name_and_categories("Graphene", "2D")
BORON_NITRIDE_2D = Materials.get_by_name_and_categories("Boron_Nitride", "2D")
MOLYBDENUM_DISULFIDE_2D = Materials.get_by_name_and_categories("Molybdenum_Disulfide", "2D")


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
            {
                OSPlatform.DARWIN: GRAIN_BOUNDARY_SI_001_011,
                OSPlatform.OTHER: GRAIN_BOUNDARY_SI_001_011_GH,
            },
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

    expected_material_config = get_platform_specific_value(expected_material_config)
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
            {
                OSPlatform.DARWIN: GRAIN_BOUNDARY_SI_001_011,
                OSPlatform.OTHER: GRAIN_BOUNDARY_SI_001_011_GH,
            },
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

    expected_material_config = get_platform_specific_value(expected_material_config)
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


# Li et al., Nano Lett. 15, 5804 (2015), Type III: 32.2 degrees, 5-7-5-7 chains with B-B and N-N bonds alternating
@pytest.mark.parametrize(
    "material_config, boundary_vectors, core, homo_bonds, expected_material_config",
    [(BORON_NITRIDE_2D, ((3, 1), (1, 3)), "5|7", "alternating", GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7)],
)
def test_create_grain_boundary_linear_with_core(
    material_config, boundary_vectors, core, homo_bonds, expected_material_config
):
    grain_boundary = create_grain_boundary_linear_with_core(
        Material.create(material_config), boundary_vectors, core, homo_bonds
    )
    configuration = GrainBoundaryLinearConfiguration(**grain_boundary.metadata.build[-1].configuration)
    rebuilt_grain_boundary = GrainBoundaryLinearBuilder().get_material(configuration)

    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)
    assert_two_entities_deep_almost_equal(rebuilt_grain_boundary, expected_material_config)


# per line, at x = 0 and between the grains: the defect ring sizes and the homo bonds by element
@pytest.mark.parametrize(
    "material_config, boundary_vectors, number_of_periods_across, core, homo_bonds, elements, line_counts",
    [
        (
            BORON_NITRIDE_2D,
            ((3, 1), (1, 3)),
            2,
            "5|7",
            "alternating",
            {"B": 104, "N": 104},
            [([5, 5, 7, 7], {"B": 1, "N": 1})] * 2,
        ),
        (GRAPHENE_2D, ((2, 1), (1, 2)), 1, "5|7", None, {"C": 56}, [([5, 7], {})] * 2),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((2, 1), (1, 2)),
            1,
            "5|7",
            None,
            {"Mo": 28, "S": 56},
            [([5, 7], {"Mo": 2}), ([5, 7], {"S": 2})],
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 1), (1, 3)),
            1,
            "5|7",
            "N",
            {"B": 52, "N": 52},
            [([5, 5, 7, 7], {"N": 4}), ([5, 5, 7, 7], {"B": 4})],
        ),
        (BORON_NITRIDE_2D, ((1, 1), (1, 1)), 4, "4|8", "none", {"B": 16, "N": 16}, [([4, 8], {})] * 2),
        (BORON_NITRIDE_2D, ((1, 1), (1, 1)), 4, "6", None, {"B": 16, "N": 16}, [([], {"B": 1, "N": 1})] * 2),
    ],
)
def test_create_grain_boundary_linear_with_core_line_counts(
    material_config, boundary_vectors, number_of_periods_across, core, homo_bonds, elements, line_counts
):
    grain_boundary = create_grain_boundary_linear_with_core(
        Material.create(material_config), boundary_vectors, core, homo_bonds, number_of_periods_across
    )
    counts = RingsMaterialAnalyzer(material=grain_boundary).get_line_counts([0.0, grain_boundary.lattice.a / 2])

    assert Counter(grain_boundary.basis.elements.values) == elements
    assert [(sorted(rings.elements()), dict(bonds)) for rings, bonds, _ in counts] == line_counts


@pytest.mark.parametrize(
    "boundary_vectors, core, homo_bonds, message",
    [
        (((2, 1), (1, 2)), "5|8", None, "disclination"),
        (((2, 1), (1, 2)), "5|7", "C", "B, N"),
        (((3, 1), (2, 1)), "5|7", None, "differ in length"),
        (((1, 1), (1, 1)), "5|7", "none", "slides give"),
    ],
)
def test_create_grain_boundary_linear_with_core_invalid(boundary_vectors, core, homo_bonds, message):
    with pytest.raises(ValueError, match=message):
        create_grain_boundary_linear_with_core(Material.create(BORON_NITRIDE_2D), boundary_vectors, core, homo_bonds)
