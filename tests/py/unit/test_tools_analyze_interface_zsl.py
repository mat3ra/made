from types import SimpleNamespace
from typing import Final

import numpy as np
import pytest
from mat3ra.made.tools.analyze.interface.zsl import ZSLInterfaceAnalyzer
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab import SlabConfiguration
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab_strained_supercell.builder import (
    SlabStrainedSupercellBuilder,
)
from mat3ra.made.tools.utils import supercell_matrix_2d_schema_to_list, unwrap
from mat3ra.utils.matrix import convert_2x2_to_3x3
from unit.fixtures.bulk import BULK_Ge_CONVENTIONAL, BULK_Ni_PRIMITIVE, BULK_Si_CONVENTIONAL

from .fixtures.monolayer import GRAPHENE

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


@pytest.mark.parametrize(
    "substrate, film, zsl_params, expected_matches_min",
    [
        (
            SUBSTRATE_SI_001,
            FILM_GE_001,
            {"max_area": 350.0, "max_area_ratio_tol": 0.09, "max_length_tol": 0.03, "max_angle_tol": 0.01},
            1,
        ),
        (
            SimpleNamespace(
                bulk_config=BULK_Ni_PRIMITIVE,
                miller_indices=(0, 0, 1),
                number_of_layers=2,
                vacuum=0.0,
            ),
            SimpleNamespace(
                bulk_config=GRAPHENE,
                miller_indices=(0, 0, 1),
                number_of_layers=1,
                vacuum=0.0,
            ),
            {"max_area": 120.0, "max_area_ratio_tol": 0.09, "max_length_tol": 0.03, "max_angle_tol": 0.01},
            1,
        ),
    ],
)
def test_zsl_interface_analyzer(substrate, film, zsl_params, expected_matches_min):
    substrate_slab_config = SlabConfiguration.from_parameters(
        substrate.bulk_config,
        substrate.miller_indices,
        substrate.number_of_layers,
        vacuum=0.0,
        termination_top_formula=None,
        termination_bottom_formula=None,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        film.bulk_config, film.miller_indices, film.number_of_layers, vacuum=0.0
    )

    analyzer = ZSLInterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
        **zsl_params,
    )

    # Test ZSL match generation
    match_holders = analyzer.zsl_match_holders
    assert len(match_holders) >= expected_matches_min

    match = analyzer.get_strained_configuration_by_match_id(0)

    sub_config = match.substrate_configuration
    film_config = match.film_configuration

    film_vectors = np.array(analyzer.film_slab.lattice.vector_arrays)
    substrate_vectors = np.array(analyzer.substrate_slab.lattice.vector_arrays)

    film_sl_vectors = (
        np.array(unwrap(film_config.strain_matrix.root))
        @ np.array(convert_2x2_to_3x3(supercell_matrix_2d_schema_to_list(film_config.xy_supercell_matrix)))
        @ film_vectors
    )
    substrate_sl_vectors = (
        np.array(convert_2x2_to_3x3(supercell_matrix_2d_schema_to_list(sub_config.xy_supercell_matrix)))
        @ substrate_vectors
    )

    substrate_material = SlabStrainedSupercellBuilder().get_material(sub_config)
    film_material = SlabStrainedSupercellBuilder().get_material(film_config)

    # Check that the lattice vectors have the same magnitudes (allowing for orientation differences)
    film_a = np.linalg.norm(film_sl_vectors[0])
    film_b = np.linalg.norm(film_sl_vectors[1])
    substrate_a = np.linalg.norm(substrate_sl_vectors[0])
    substrate_b = np.linalg.norm(substrate_sl_vectors[1])

    assert np.isclose(film_a, substrate_a, atol=0.1)
    assert np.isclose(film_b, substrate_b, atol=0.1)

    # Check that the unit cell areas match
    film_area = abs(np.cross(film_sl_vectors[0][:2], film_sl_vectors[1][:2]))
    substrate_area = abs(np.cross(substrate_sl_vectors[0][:2], substrate_sl_vectors[1][:2]))
    assert np.isclose(film_area, substrate_area, atol=1e-4)

    assert np.isclose(substrate_material.lattice.a, film_material.lattice.a, atol=1e-4)
    assert np.isclose(substrate_material.lattice.b, film_material.lattice.b, atol=1e-4)


@pytest.mark.parametrize(
    "substrate, film, zsl_parameters, expected_number_of_matches, expected_properties",
    [
        (
            SimpleNamespace(
                bulk_config=BULK_Ni_PRIMITIVE,
                miller_indices=(1, 1, 1),
                number_of_layers=3,
                vacuum=0.0,
            ),
            SimpleNamespace(
                bulk_config=GRAPHENE,
                miller_indices=(0, 0, 1),
                number_of_layers=1,
                vacuum=0.0,
            ),
            {"max_area": 90.0, "max_area_ratio_tol": 0.1, "max_length_tol": 0.1, "max_angle_tol": 0.1},
            28,
            {"strain_percentage": 0.475, "match_id": 0},
        ),
    ],
)
def test_zsl_interface_analyzer_sort_by_strain_then_area(
    substrate, film, zsl_parameters, expected_number_of_matches, expected_properties
):
    analyzer = ZSLInterfaceAnalyzer(
        substrate_slab_configuration=SlabConfiguration.from_parameters(
            substrate.bulk_config,
            substrate.miller_indices,
            substrate.number_of_layers,
            vacuum=0.0,
            termination_top_formula=None,
            termination_bottom_formula=None,
        ),
        film_slab_configuration=SlabConfiguration.from_parameters(
            film.bulk_config, film.miller_indices, film.number_of_layers, vacuum=0.0
        ),
        **zsl_parameters,
    )

    sorted_match_holders = analyzer.zsl_match_holders

    assert len(sorted_match_holders) == expected_number_of_matches

    index_to_check = expected_properties["match_id"]
    match_to_check = sorted_match_holders[index_to_check]
    expected_strain_percentage = expected_properties["strain_percentage"]

    assert np.isclose(match_to_check.total_strain_percentage, expected_strain_percentage, atol=1e-3)
