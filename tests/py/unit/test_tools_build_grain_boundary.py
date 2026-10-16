import time
from collections import Counter

import numpy as np
import pytest
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.grain_boundary_network import GrainBoundaryRingNetworkAnalyzer
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
from scipy.spatial import cKDTree

from .fixtures.bulk import BULK_GRAPHITE, BULK_Si_CONVENTIONAL
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
CORE_BUILD_TIME_LIMIT = 20.0  # seconds
REBUILT_BAND_WIDTH = GrainBoundaryRingNetworkAnalyzer.model_fields["band_width"].default


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


def get_kept_atoms_deviation(grain_boundary: Material, lattice_constant: float) -> float:
    """Largest distance from a stacked atom outside the rebuilt bands to the nearest atom of the grain boundary."""
    configuration = GrainBoundaryLinearConfiguration(**grain_boundary.metadata.build[-1].configuration)
    stacked = GrainBoundaryLinearBuilder().get_material(configuration.model_copy(update={"core": None}))
    stacked.to_cartesian()
    grain_boundary.to_cartesian()
    coordinates, quarter_width = np.array(stacked.basis.coordinates.values), stacked.lattice.a / 4
    line_distances = np.abs((coordinates[:, 0] + quarter_width) % (2 * quarter_width) - quarter_width)
    kept_coordinates = coordinates[line_distances >= REBUILT_BAND_WIDTH * lattice_constant]
    return float(cKDTree(grain_boundary.basis.coordinates.values).query(kept_coordinates)[0].max())


@pytest.mark.parametrize(
    "material_config, boundary_vectors, number_of_periods_across, core, elements, sequence, homo_bonds",
    [
        (GRAPHENE_2D, ((3, 1), (3, 2)), 1, "5|7", {"C": 56}, "[5-7]", [{}] * 2),
        (GRAPHENE_2D, ((5, 2), (5, 3)), 1, "5|7", {"C": 152}, "[5-7]", [{}] * 2),
        (GRAPHENE_2D, ((9, 4), (9, 5)), 1, "5|7", {"C": 488}, "[5-7]", [{}] * 2),
        (GRAPHENE_2D, ((4, 1), (4, 3)), 1, "5|7", {"C": 104}, "(5-7-5-7)", [{}] * 2),
        (BORON_NITRIDE_2D, ((3, 1), (3, 2)), 1, "5|7", {"B": 28, "N": 28}, "[5-7]", [{"N-N": 2}, {"B-B": 2}]),
        (BORON_NITRIDE_2D, ((5, 2), (5, 3)), 1, "5|7", {"B": 76, "N": 76}, "[5-7]", [{"N-N": 2}, {"B-B": 2}]),
        (BORON_NITRIDE_2D, ((9, 4), (9, 5)), 1, "5|7", {"B": 244, "N": 244}, "[5-7]", [{"N-N": 2}, {"B-B": 2}]),
        (BORON_NITRIDE_2D, ((4, 1), (4, 3)), 1, "5|7", {"B": 52, "N": 52}, "(5-7-5-7)", [{"N-N": 4}, {"B-B": 4}]),
        (BORON_NITRIDE_2D, ((4, 1), (-4, -3)), 1, "5|7", {"B": 52, "N": 52}, "(5-7-5-7)", [{"B-B": 1, "N-N": 1}] * 2),
        (BORON_NITRIDE_2D, ((4, 1), (-4, -3)), 2, "5|7", {"B": 104, "N": 104}, "(5-7-5-7)", [{"B-B": 1, "N-N": 1}] * 2),
        (BORON_NITRIDE_2D, ((9, 4), (-9, -5)), 1, "5|7", {"B": 244, "N": 244}, "[5-7]", [{"B-B": 4, "N-N": 4}] * 2),
        (MOLYBDENUM_DISULFIDE_2D, ((3, 1), (3, 2)), 1, "5|7", {"Mo": 28, "S": 56}, "[5-7]", [{"Mo-Mo": 2}, {"S-S": 2}]),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((5, 2), (5, 3)),
            1,
            "5|7",
            {"Mo": 76, "S": 152},
            "[5-7]",
            [{"Mo-Mo": 2}, {"S-S": 2}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((9, 4), (9, 5)),
            1,
            "5|7",
            {"Mo": 244, "S": 488},
            "[5-7]",
            [{"Mo-Mo": 2}, {"S-S": 2}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((4, 1), (4, 3)),
            1,
            "5|7",
            {"Mo": 52, "S": 104},
            "(5-7-5-7)",
            [{"Mo-Mo": 4}, {"S-S": 4}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((4, 1), (-4, -3)),
            1,
            "5|7",
            {"Mo": 52, "S": 104},
            "(5-7-5-7)",
            [{"Mo-Mo": 1, "S-S": 1}] * 2,
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((9, 4), (-9, -5)),
            1,
            "5|7",
            {"Mo": 244, "S": 488},
            "[5-7]",
            [{"Mo-Mo": 4, "S-S": 4}] * 2,
        ),
        (BORON_NITRIDE_2D, ((2, 1), (-2, -1)), 6, "4|8", {"B": 24, "N": 24}, "(4-8)", [{}] * 2),
        (MOLYBDENUM_DISULFIDE_2D, ((2, 1), (-2, -1)), 5, "4|8", {"Mo": 20, "S": 40}, "(4-8)", [{}] * 2),
        (GRAPHENE_2D, ((15, 7), (15, 8)), 1, "5|7", {"C": 1352}, "[5-7]", [{}] * 2),
    ],
)
def test_create_grain_boundary_linear_core(
    material_config, boundary_vectors, number_of_periods_across, core, elements, sequence, homo_bonds
):
    material = Material.create(material_config)
    start = time.perf_counter()
    grain_boundary = create_grain_boundary_linear(
        material, boundary_vectors=boundary_vectors, core=core, number_of_periods_across=number_of_periods_across
    )
    build_time = time.perf_counter() - start
    rings_analyzer = RingsMaterialAnalyzer(material=grain_boundary)
    arrangements = rings_analyzer.get_line_arrangements([0.0, grain_boundary.lattice.a / 2])
    lattice_vectors = np.array(material.lattice.vector_arrays)[:2, :2]
    site_distance = material.lattice.a / np.sqrt(3)

    assert build_time < CORE_BUILD_TIME_LIMIT
    assert dict(Counter(grain_boundary.basis.elements.values)) == elements
    assert grain_boundary.lattice.b == pytest.approx(np.linalg.norm(np.array(boundary_vectors[0]) @ lattice_vectors))
    assert [arrangement.sequence for arrangement in arrangements] == [[sequence]] * 2
    assert [arrangement.homo_bonds for arrangement in arrangements] == homo_bonds
    assert [arrangement.rings_without_core_partner for arrangement in arrangements] == [0, 0]
    assert np.all(np.abs(np.linalg.norm(rings_analyzer.bonds[2], axis=1) / site_distance - 1) < 0.1)
    assert get_kept_atoms_deviation(grain_boundary, material.lattice.a) < 1e-6


@pytest.mark.parametrize(
    "material_config, boundary_vectors, gap, elements, lattice_lengths",
    [
        (GRAPHENE_2D, ((3, 1), (3, 2)), None, {"C": 56}, (22.592, 6.522)),
        (GRAPHENE_2D, ((3, 1), (3, 2)), 3.0, {"C": 56}, (28.054, 6.522)),
    ],
)
def test_create_grain_boundary_linear_boundary_vectors(
    material_config, boundary_vectors, gap, elements, lattice_lengths
):
    grain_boundary = create_grain_boundary_linear(
        Material.create(material_config), boundary_vectors=boundary_vectors, gap=gap
    )
    assert dict(Counter(grain_boundary.basis.elements.values)) == elements
    assert (grain_boundary.lattice.a, grain_boundary.lattice.b) == pytest.approx(lattice_lengths, abs=1e-3)


@pytest.mark.parametrize(
    "material_config, boundary_vectors, target_angle, expected_material_config",
    [
        (BORON_NITRIDE_2D, ((4, 1), (-4, -3)), 0.0, GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7),
        (BORON_NITRIDE_2D, None, 212.204, GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7),
    ],
)
def test_create_grain_boundary_linear_core_structure(
    material_config, boundary_vectors, target_angle, expected_material_config
):
    grain_boundary = create_grain_boundary_linear(
        Material.create(material_config), target_angle=target_angle, boundary_vectors=boundary_vectors, core="5|7"
    )
    configuration = GrainBoundaryLinearConfiguration(**grain_boundary.metadata.build[-1].configuration)
    rebuilt = GrainBoundaryLinearBuilder().get_material(configuration)
    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)
    assert_two_entities_deep_almost_equal(rebuilt, grain_boundary)


@pytest.mark.parametrize(
    "material_config, boundary_vectors, core, number_of_periods_across, direction, message",
    [
        (BULK_Si_CONVENTIONAL, ((1, 0), (0, 1)), "5|7", 1, AxisEnum.x, "honeycomb"),
        (BULK_GRAPHITE, ((2, 1), (1, 2)), "5|7", 1, AxisEnum.x, "honeycomb"),
        (GRAPHENE_2D, None, "5|7", 1, AxisEnum.x, "rotated by 0"),
        (GRAPHENE_2D, ((3, 1), (3, 2)), "5|7", 1, AxisEnum.y, "stacked along x"),
        (GRAPHENE_2D, ((3, 1), (3, 2)), "4|8", 1, AxisEnum.x, r"achievable: \['5\|7'\]"),
    ],
)
def test_create_grain_boundary_linear_invalid(
    material_config, boundary_vectors, core, number_of_periods_across, direction, message
):
    with pytest.raises(ValueError, match=message):
        create_grain_boundary_linear(
            Material.create(material_config),
            boundary_vectors=boundary_vectors,
            core=core,
            number_of_periods_across=number_of_periods_across,
            direction=direction,
        )
