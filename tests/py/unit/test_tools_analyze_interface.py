from types import SimpleNamespace
from typing import Final

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface import InterfaceAnalyzer
from mat3ra.made.tools.analyze.interface.commensurate import CommensurateLatticeInterfaceAnalyzer
from mat3ra.made.tools.analyze.interface.enums import angle_to_supercell_matrix_values_for_hex
from mat3ra.made.tools.analyze.interface.utils import calculate_interfacial_distance_from_rdf
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab import SlabConfiguration
from unit.fixtures.bulk import BULK_GRAPHENE, BULK_Ge_CONVENTIONAL, BULK_Si_CONVENTIONAL

from .fixtures.monolayer import GRAPHENE
from .utils import assert_two_entities_deep_almost_equal

SUBSTRATE_SI_001: Final = SimpleNamespace(
    bulk_config=BULK_Si_CONVENTIONAL,
    miller_indices=(0, 0, 1),
    number_of_layers=2,
    vacuum=0.0,
)

FILM_GE_001: Final = SimpleNamespace(
    bulk_config=BULK_Ge_CONVENTIONAL,
    miller_indices=(0, 0, 1),
    number_of_layers=2,
    vacuum=0.0,
)

EXPECTED_PROPERTIES_SI_GE_001: Final = SimpleNamespace(
    substrate_strain_matrix=np.identity(3).tolist(),
    substrate_supercell_matrix=[[1.0, 0.0], [0.0, 1.0]],
    film_strain_matrix=[[0.9643, 0.0, 0.0], [0.0, 0.9643, 0.0], [0.0, 0.0, 1.0]],
    film_supercell_matrix=[[1.0, 0.0], [0.0, 1.0]],
)

TEST_CASES = [(SUBSTRATE_SI_001, FILM_GE_001, EXPECTED_PROPERTIES_SI_GE_001)]


SUBSTRATE_SI_111: Final = SimpleNamespace(
    bulk_config=BULK_Si_CONVENTIONAL,
    miller_indices=(1, 1, 1),
    number_of_layers=2,
    vacuum=0.0,
)

FILM_GRAPHENE_001: Final = SimpleNamespace(
    bulk_config=BULK_GRAPHENE,
    miller_indices=(0, 0, 1),
    number_of_layers=1,
    vacuum=0.0,
)

OPTIMAL_SUPERCELL_TEST_CASES = [
    (SUBSTRATE_SI_111, FILM_GRAPHENE_001, 4, 4),  # n, m
]


@pytest.mark.parametrize("substrate, film, expected", TEST_CASES)
def test_interface_analyzer(substrate, film, expected):
    substrate_slab_config = SlabConfiguration.from_parameters(
        substrate.bulk_config,
        substrate.miller_indices,
        substrate.number_of_layers,
        vacuum=substrate.vacuum,
        termination_top_formula=None,
        termination_bottom_formula=None,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        film.bulk_config,
        film.miller_indices,
        film.number_of_layers,
        vacuum=film.vacuum,
        termination_top_formula=None,
        termination_bottom_formula=None,
    )

    interface_analyzer = InterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
    )

    assert_two_entities_deep_almost_equal(
        interface_analyzer.get_substrate_strain_matrix().root, expected.substrate_strain_matrix
    )
    assert_two_entities_deep_almost_equal(
        interface_analyzer.film_strained_configuration.strain_matrix.root, expected.film_strain_matrix, atol=1e-4
    )

    # Test strain matrix calculation using vectors from substrate and film
    substrate_vectors = np.array(interface_analyzer.substrate_material.lattice.vector_arrays)
    film_vectors = np.array(interface_analyzer.film_material.lattice.vector_arrays)

    strain_matrix_3d = interface_analyzer.get_film_strain_matrix(substrate_vectors, film_vectors)

    matrix = [row.root for row in strain_matrix_3d.root]
    strain_matrix_2d = np.array(matrix)[:2, :2]

    # Verify that strain applied to film vectors yields substrate vectors
    film_2d = film_vectors[:2, :2]
    substrate_2d = substrate_vectors[:2, :2]
    film_strained = film_2d @ strain_matrix_2d

    assert np.allclose(film_strained, substrate_2d, atol=1e-10)


EXPECTED_PROPERTIES_GRAPHENE_13: Final = SimpleNamespace(
    number_of_matches=1,
    angle_range=(12.5, 13.5),
    substrate_supercell_matrix=[[-5, -2], [-3, -5]],
    film_supercell_matrix=[[-5, -3], [-2, -5]],
)

EXPECTED_PROPERTIES_GRAPHENE_7_34: Final = SimpleNamespace(
    number_of_matches=1,
    angle_range=(7.24, 7.44),
    substrate_supercell_matrix=[[-9, -4], [-5, -9]],
    film_supercell_matrix=[[-9, -5], [-4, -9]],
)


@pytest.mark.parametrize(
    "material_config, use_conventional_cell, analyzer_params, expected",
    [
        (
            GRAPHENE,
            True,
            {"target_angle": 13.0, "angle_tolerance": 0.5, "max_supercell_matrix_int": 5, "return_first_match": True},
            EXPECTED_PROPERTIES_GRAPHENE_13,
        ),
        (GRAPHENE, True, {"target_angle": 7.34, "max_supercell_matrix_int": 8}, EXPECTED_PROPERTIES_GRAPHENE_7_34),
        (
            BULK_GRAPHENE,
            False,
            {"target_angle": 13.0, "angle_tolerance": 0.5, "max_supercell_matrix_int": 5, "limit_max_int": 6},
            EXPECTED_PROPERTIES_GRAPHENE_13,
        ),
    ],
)
def test_commensurate_analyzer_functionality(material_config, use_conventional_cell, analyzer_params, expected):
    slab_config = SlabConfiguration.from_parameters(
        material_config,
        miller_indices=(0, 0, 1),
        number_of_layers=1,
        vacuum=0.0,
        termination_top_formula=None,
        termination_bottom_formula=None,
        use_conventional_cell=use_conventional_cell,
    )

    analyzer = CommensurateLatticeInterfaceAnalyzer(substrate_slab_configuration=slab_config, **analyzer_params)

    assert analyzer.substrate_material == analyzer.film_material == analyzer.material

    match_holders = analyzer.commensurate_lattice_match_holders
    assert len(match_holders) == expected.number_of_matches
    assert match_holders[0].xy_supercell_matrix_substrate == expected.substrate_supercell_matrix
    assert match_holders[0].xy_supercell_matrix_film == expected.film_supercell_matrix

    for match in match_holders:
        assert expected.angle_range[0] <= match.angle <= expected.angle_range[1]
        assert expected.angle_range[0] <= match.actual_angle <= expected.angle_range[1]
        assert match.angle == match.actual_angle
        assert isinstance(match.xy_supercell_matrix_film, list)
        assert isinstance(match.xy_supercell_matrix_substrate, list)
        assert len(match.xy_supercell_matrix_film) == 2
        assert len(match.xy_supercell_matrix_substrate) == 2
        assert isinstance(match.match_id, int)
        assert match.match_id >= 0

    interface_configurations = analyzer.get_strained_configurations()
    assert len(interface_configurations) == len(match_holders)

    if len(match_holders) > 0:
        selected_config = analyzer.get_strained_configuration_by_match_id(0)
        assert selected_config.match_id == 0
        assert hasattr(selected_config, "substrate_configuration")
        assert hasattr(selected_config, "film_configuration")

        assert selected_config.substrate_configuration.stack_components == slab_config.stack_components
        assert selected_config.film_configuration.stack_components == slab_config.stack_components

        # Test invalid match ID
        with pytest.raises(ValueError, match="Match ID .* out of range"):
            analyzer.get_strained_configuration_by_match_id(999)

        # Test negative match ID
        with pytest.raises(ValueError, match="Match ID .* out of range"):
            analyzer.get_strained_configuration_by_match_id(-1)


COINCIDENCE_LATTICE_TEST_CASES = [
    (GRAPHENE, entry["angle"], entry["xy_supercell"]) for entry in angle_to_supercell_matrix_values_for_hex
] + [(BULK_Si_CONVENTIONAL, 36.8698976458, [[2, 1], [-1, 2]])]


@pytest.mark.parametrize("material_config, target_angle, expected_supercell_matrix", COINCIDENCE_LATTICE_TEST_CASES)
def test_commensurate_lattice_match_holders(material_config, target_angle, expected_supercell_matrix):
    slab_config = SlabConfiguration.from_parameters(material_config, (0, 0, 1), number_of_layers=1, vacuum=0.0)
    analyzer = CommensurateLatticeInterfaceAnalyzer(
        substrate_slab_configuration=slab_config, target_angle=target_angle, angle_tolerance=1e-3
    )
    match = analyzer.commensurate_lattice_match_holders[0]
    assert abs(match.angle - target_angle) < analyzer.angle_tolerance
    assert round(abs(np.linalg.det(match.xy_supercell_matrix_substrate))) == round(
        abs(np.linalg.det(expected_supercell_matrix))
    )


@pytest.mark.parametrize("substrate, film, expected_n, expected_m", OPTIMAL_SUPERCELL_TEST_CASES)
def test_optimal_supercell_functions(substrate, film, expected_n, expected_m):
    """Test the optimal supercell functions with Si/Ge fixtures."""
    substrate_slab_config = SlabConfiguration.from_parameters(
        substrate.bulk_config,
        substrate.miller_indices,
        substrate.number_of_layers,
        vacuum=substrate.vacuum,
        termination_top_formula=None,
        termination_bottom_formula=None,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        film.bulk_config,
        film.miller_indices,
        film.number_of_layers,
        vacuum=film.vacuum,
        termination_top_formula=None,
        termination_bottom_formula=None,
    )

    analyzer = InterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
        optimize_film_supercell=True,
    )

    # Test find_optimal_film_supercell
    optimal_n, optimal_m = analyzer.find_optimal_film_supercell()

    assert optimal_n == expected_n
    assert optimal_m == expected_m


@pytest.mark.parametrize(
    "substrate_config, film_config, expected_distance_range",
    [
        (BULK_Si_CONVENTIONAL, BULK_Si_CONVENTIONAL, (3.8, 3.9)),
        (BULK_Si_CONVENTIONAL, BULK_Ge_CONVENTIONAL, (3.1, 3.2)),
    ],
)
def test_calculate_interfacial_distance_from_rdf(substrate_config, film_config, expected_distance_range):
    """Test RDF-based interfacial distance calculation with different material types."""
    substrate_material = Material.create(substrate_config)
    film_material = Material.create(film_config)

    distance = calculate_interfacial_distance_from_rdf(
        substrate_material=substrate_material,
        film_material=film_material,
        rdf_cutoff=10.0,
        rdf_bin_size=0.1,
        supercell_size=(3, 3, 3),
    )

    assert isinstance(distance, float)
    assert expected_distance_range[0] <= distance <= expected_distance_range[1]
