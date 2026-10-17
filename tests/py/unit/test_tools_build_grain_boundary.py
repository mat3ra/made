import time
from collections import Counter

import numpy as np
import pytest
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface.grain_boundary import GrainBoundaryPlanarAnalyzer
from mat3ra.made.tools.analyze.interface.grain_boundary_linear import GrainBoundaryLinearAnalyzer
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
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from mat3ra.made.tools.convert import to_pymatgen
from mat3ra.standata.materials import Materials
from pymatgen.analysis.structure_matcher import StructureMatcher

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
# three times the slowest row measured on a CI runner (MoS2 (1,9)|(9,1), 15 s; runners are up to 3.4x slower than an M1
# at load); the regression it guards, the commensurate matrix search, took 40 s at 13.2 degrees and never finished below 9.4
CORE_BUILD_TIME_LIMIT = 45.0  # seconds


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


def get_line_positions(grain_boundary: Material) -> list:
    """x of the two lines: 0 and the width of the first grain, from the supercell matrices in the build metadata."""
    components = grain_boundary.metadata.build[-1].configuration["stack_components"]
    areas = np.abs([np.linalg.det(component["xy_supercell_matrix"]) for component in components])
    return [0.0, grain_boundary.lattice.a * areas[0] / areas.sum()]


# vectors in the 60 degree basis; number_of_periods_across None: the fewest that hold both rebuilt bands
@pytest.mark.parametrize(
    "material_config, boundary_vectors, number_of_periods_across, core, homo_bonds, elements, cores, line_homo_bonds",
    [
        (GRAPHENE_2D, ((2, 1), (1, 2)), None, "5|7", "none", {"C": 112}, [[[5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((4, 2), (2, 4)), None, "5|7", "none", {"C": 224}, [[[5, 7], [5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((3, 2), (2, 3)), None, "5|7", "none", {"C": 152}, [[[5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((5, 4), (4, 5)), None, "5|7", "none", {"C": 488}, [[[5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((3, 1), (1, 3)), None, "5|7", "none", {"C": 104}, [[[5, 7, 5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((1, 3), (3, 1)), None, "5|7", "none", {"C": 104}, [[[5, 7, 5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((8, 7), (7, 8)), None, "5|7", "none", {"C": 1352}, [[[5, 7]]] * 2, [{}, {}]),
        (GRAPHENE_2D, ((2, 1), (1, 2)), None, "4|8", "none", {"C": 112}, [[[4, 8]]] * 2, [{}, {}]),
        (
            BORON_NITRIDE_2D,
            ((2, 1), (1, 2)),
            None,
            "5|7",
            "N",
            {"B": 56, "N": 56},
            [[[5, 7]]] * 2,
            [{"N-N": 2}, {"B-B": 2}],
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 2), (2, 3)),
            None,
            "5|7",
            "N",
            {"B": 76, "N": 76},
            [[[5, 7]]] * 2,
            [{"N-N": 2}, {"B-B": 2}],
        ),
        (
            BORON_NITRIDE_2D,
            ((5, 4), (4, 5)),
            None,
            "5|7",
            "N",
            {"B": 244, "N": 244},
            [[[5, 7]]] * 2,
            [{"N-N": 2}, {"B-B": 2}],
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 1), (1, 3)),
            None,
            "5|7",
            "N",
            {"B": 52, "N": 52},
            [[[5, 7, 5, 7]]] * 2,
            [{"N-N": 4}, {"B-B": 4}],
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 1), (1, 3)),
            None,
            "5|7",
            "alternating",
            {"B": 52, "N": 52},
            [[[5, 7, 5, 7]]] * 2,
            [{"B-B": 1, "N-N": 1}] * 2,
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 1), (1, 3)),
            2,
            "5|7",
            "alternating",
            {"B": 104, "N": 104},
            [[[5, 7, 5, 7]]] * 2,
            [{"B-B": 1, "N-N": 1}] * 2,
        ),
        (
            BORON_NITRIDE_2D,
            ((5, 4), (4, 5)),
            None,
            "5|7",
            "alternating",
            {"B": 244, "N": 244},
            [[[5, 7]]] * 2,
            [{"B-B": 4, "N-N": 4}] * 2,
        ),
        (BORON_NITRIDE_2D, ((2, 1), (1, 2)), None, "4|8", "none", {"B": 56, "N": 56}, [[[4, 8]]] * 2, [{}, {}]),
        (BORON_NITRIDE_2D, ((1, 1), (-1, -1)), None, "4|8", "none", {"B": 20, "N": 20}, [[[4, 8]]] * 2, [{}, {}]),
        (
            BORON_NITRIDE_2D,
            ((8, -5), (7, 0)),
            None,
            "5|7",
            "B",
            {"B": 336, "N": 336},
            [[[5, 7], [5, 7, 5, 7]]] * 2,
            [{"B-B": 9}, {"N-N": 9}],
        ),
        (
            BORON_NITRIDE_2D,
            ((0, 7), (5, 3)),
            None,
            "5|7",
            "B",
            {"B": 336, "N": 336},
            [[[5, 7], [5, 7, 5, 7]]] * 2,
            [{"B-B": 9}, {"N-N": 9}],
        ),
        (
            BORON_NITRIDE_2D,
            ((3, 8), (8, 3)),
            None,
            "5|7",
            "B",
            {"B": 388, "N": 388},
            [[[5, 7, 5, 7, 5, 7, 5, 7, 5, 7]]] * 2,
            [{"B-B": 10}, {"N-N": 10}],
        ),
        (BORON_NITRIDE_2D, ((0, 2), (2, 0)), None, "6", "B", {"B": 24, "N": 24}, [[]] * 2, [{"B-B": 4}, {"N-N": 4}]),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((2, 1), (1, 2)),
            None,
            "5|7",
            "Mo",
            {"Mo": 56, "S": 112},
            [[[5, 7]]] * 2,
            [{"Mo-Mo": 2}, {"S-S": 2}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((3, 2), (2, 3)),
            None,
            "5|7",
            "Mo",
            {"Mo": 76, "S": 152},
            [[[5, 7]]] * 2,
            [{"Mo-Mo": 2}, {"S-S": 2}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((5, 4), (4, 5)),
            None,
            "5|7",
            "Mo",
            {"Mo": 244, "S": 488},
            [[[5, 7]]] * 2,
            [{"Mo-Mo": 2}, {"S-S": 2}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((3, 1), (1, 3)),
            None,
            "5|7",
            "Mo",
            {"Mo": 52, "S": 104},
            [[[5, 7, 5, 7]]] * 2,
            [{"Mo-Mo": 4}, {"S-S": 4}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((3, 1), (1, 3)),
            None,
            "5|7",
            "alternating",
            {"Mo": 52, "S": 104},
            [[[5, 7, 5, 7]]] * 2,
            [{"Mo-Mo": 1, "S-S": 1}] * 2,
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((5, 4), (4, 5)),
            None,
            "5|7",
            "alternating",
            {"Mo": 244, "S": 488},
            [[[5, 7]]] * 2,
            [{"Mo-Mo": 4, "S-S": 4}] * 2,
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((1, 1), (-1, -1)),
            None,
            "4|8",
            "none",
            {"Mo": 20, "S": 40},
            [[[4, 8]]] * 2,
            [{}, {}],
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((1, 1), (1, 1)),
            None,
            "5|7",
            "alternating",
            {"Mo": 20, "S": 40},
            [[[5, 5, 7, 7]]] * 2,
            [{"Mo-Mo": 1, "S-S": 1}] * 2,
        ),
        (
            MOLYBDENUM_DISULFIDE_2D,
            ((1, 9), (9, 1)),
            None,
            "5|7",
            "S",
            {"Mo": 364, "S": 728},
            [[[5, 7, 5, 7]]] * 2,
            [{"S-S": 16}, {"Mo-Mo": 16}],
        ),
    ],
)
def test_create_grain_boundary_linear_core(
    material_config, boundary_vectors, number_of_periods_across, core, homo_bonds, elements, cores, line_homo_bonds
):
    material = Material.create(material_config)
    start = time.perf_counter()
    grain_boundary = create_grain_boundary_linear(
        material,
        boundary_vectors=boundary_vectors,
        core=core,
        homo_bonds=homo_bonds,
        number_of_periods_across=number_of_periods_across,
    )
    build_time = time.perf_counter() - start
    rings_analyzer = RingsMaterialAnalyzer(material=grain_boundary)
    arrangements = rings_analyzer.get_line_arrangements(get_line_positions(grain_boundary))
    bond_lengths = np.linalg.norm(rings_analyzer.bonds[2], axis=1) * np.sqrt(3) / material.lattice.a
    configuration = GrainBoundaryLinearConfiguration(**grain_boundary.metadata.build[-1].configuration)

    assert dict(Counter(grain_boundary.basis.elements.values)) == elements
    assert [arrangement.cores for arrangement in arrangements] == cores
    assert [arrangement.homo_bonds for arrangement in arrangements] == line_homo_bonds
    # settled bonds lie within 10 % of the input's: 0.92 to 1.08 of it over the rows
    assert np.all(np.abs(bond_lengths - 1) < 0.1)
    assert_two_entities_deep_almost_equal(GrainBoundaryLinearBuilder().get_material(configuration), grain_boundary)
    assert build_time < CORE_BUILD_TIME_LIMIT


@pytest.mark.parametrize(
    "material_config, target_angle, expected_matching_vectors",
    [(GRAPHENE_2D, 2.0, [[17, 16], [16, 17]]), (BORON_NITRIDE_2D, 32.2, [[3, 1], [1, 3]])],
)
def test_grain_boundary_linear_analyzer_matching_vectors(material_config, target_angle, expected_matching_vectors):
    slab = SlabConfiguration.from_parameters(Material.create(material_config), (0, 0, 1), 1, vacuum=0.0)
    analyzer = GrainBoundaryLinearAnalyzer(
        substrate_slab_configuration=slab, film_slab_configuration=slab, target_angle=target_angle
    )
    assert analyzer.matching_vectors.tolist() == expected_matching_vectors


@pytest.mark.parametrize(
    "material_config, boundary_vectors, target_angle, expected_material_config",
    [
        (BORON_NITRIDE_2D, ((3, 1), (1, 3)), 0.0, GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7),
        (BORON_NITRIDE_2D, None, 32.2, GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7),
    ],
)
def test_create_grain_boundary_linear_core_structure(
    material_config, boundary_vectors, target_angle, expected_material_config
):
    grain_boundary = create_grain_boundary_linear(
        Material.create(material_config),
        target_angle=target_angle,
        boundary_vectors=boundary_vectors,
        core="5|7",
        homo_bonds="alternating",
    )
    assert_two_entities_deep_almost_equal(grain_boundary, expected_material_config)


# the same h-BN with its basis listed the other way round, or shifted in the plane
@pytest.mark.parametrize(
    "boundary_vectors, atom_order, shift",
    [
        (((3, 1), (1, 3)), [1, 0], [0.0, 0.0]),
        (((3, 1), (1, 3)), [0, 1], [0.25, 0.6]),
        (((5, 4), (4, 5)), [1, 0], [0.0, 0.0]),
    ],
)
def test_create_grain_boundary_linear_core_basis_writing(boundary_vectors, atom_order, shift):
    basis = BORON_NITRIDE_2D["basis"]
    coordinates = [np.array(basis["coordinates"][index]["value"]) + [*shift, 0.0] for index in atom_order]
    material = Material.create(
        {
            **BORON_NITRIDE_2D,
            "basis": {
                **basis,
                "elements": [basis["elements"][index] for index in atom_order],
                "coordinates": [{"id": index, "value": value.tolist()} for index, value in enumerate(coordinates)],
            },
        }
    )
    arguments = {"boundary_vectors": boundary_vectors, "core": "5|7", "homo_bonds": "alternating"}
    grain_boundary = create_grain_boundary_linear(material, **arguments)
    expected = create_grain_boundary_linear(Material.create(BORON_NITRIDE_2D), **arguments)
    # at 0.2 the paired 5-5-7-7 does not match 5-7-5-7; the two writings put the bands 0.2 angstrom apart in the
    # lattice, so the settled sites differ by up to 0.11 angstrom
    matcher = StructureMatcher(ltol=0.2, stol=0.2, angle_tol=5, primitive_cell=False, scale=False)
    assert matcher.fit(to_pymatgen(grain_boundary), to_pymatgen(expected))


@pytest.mark.parametrize(
    "material_config, arguments, message",
    [
        (BULK_Si_CONVENTIONAL, {"boundary_vectors": ((1, 0), (0, 1)), "core": "5|7"}, "honeycomb"),
        (BULK_GRAPHITE, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7"}, "honeycomb"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "3|5"}, "disclination"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5-7"}, 'joined by "|"'),
        (BORON_NITRIDE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "homo_bonds": "C"}, "B, N"),
        (GRAPHENE_2D, {"boundary_vectors": ((1, 1), (-1, -1)), "core": "5|7"}, "equivalent to no rotation"),
        (BORON_NITRIDE_2D, {"boundary_vectors": ((3, 1), (2, 1)), "core": "5|7"}, "differ in length"),
        (BORON_NITRIDE_2D, {"boundary_vectors": ((0, 1), (1, 0)), "core": "5|7"}, "too short along the boundary"),
        (
            BORON_NITRIDE_2D,
            {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "homo_bonds": "none"},
            r"\('4\|8', 'none'\)",
        ),
        (
            GRAPHENE_2D,
            {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "number_of_periods_across": 1},
            "at least 2",
        ),
        (GRAPHENE_2D, {"core": "5|7"}, "rotated by 0.0 degrees"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "direction": AxisEnum.y}, "defaults"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "gap": 10.0}, "defaults"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "miller_indices": (1, 1, 1)}, "defaults"),
        (GRAPHENE_2D, {"boundary_vectors": ((2, 1), (1, 2)), "core": "5|7", "number_of_layers": 3}, "defaults"),
    ],
)
def test_create_grain_boundary_linear_invalid(material_config, arguments, message):
    with pytest.raises(ValueError, match=message):
        create_grain_boundary_linear(Material.create(material_config), **arguments)
