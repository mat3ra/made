from types import SimpleNamespace

import numpy as np
import pytest
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface.simple import InterfaceAnalyzer
from mat3ra.made.tools.analyze.lattice_planes import CrystalLatticePlanesMaterialAnalyzer
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.base.build_parameters import (
    InterfaceBuilderParameters,
)
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.base.builder import InterfaceBuilder
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.base.configuration import (
    InterfaceConfiguration,
)
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.commensurate.helpers import (
    create_interface_commensurate,
)
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.twisted.helpers import (
    create_interface_twisted,
)
from mat3ra.made.tools.build.pristine_structures.two_dimensional.nanoribbon.helpers import create_nanoribbon
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab import SlabBuilder, SlabConfiguration
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.helpers import create_slab
from mat3ra.made.tools.build_components.entities.reusable.one_dimensional.crystal_lattice_lines.edge_types import (
    EdgeTypesEnum,
)
from mat3ra.made.tools.helpers import create_interface_simple, create_interface_simple_between_slabs
from unit.fixtures.bulk import BULK_Ge_CONVENTIONAL, BULK_Ni_PRIMITIVE, BULK_Si_CONVENTIONAL

from .fixtures.interface.commensurate import INTERFACE_GRAPHENE_GRAPHENE_X, INTERFACE_GRAPHENE_GRAPHENE_Z
from .fixtures.interface.gr_ni_111_top_hcp import (
    GRAPHENE_NICKEL_INTERFACE_TOP_HCP,
    GRAPHENE_NICKEL_INTERFACE_TOP_HCP_GH_WF,
)
from .fixtures.interface.simple import INTERFACE_Si_001_Ge_001  # type: ignore
from .fixtures.interface.twisted_nanoribbons import TWISTED_INTERFACE_GRAPHENE_GRAPHENE_60
from .fixtures.monolayer import GRAPHENE
from .utils import OSPlatform, assert_two_entities_deep_almost_equal

HASH_KEY = "hash"
SCALED_HASH_KEY = "scaledHash"

Si_Ge_SIMPLE_INTERFACE_TEST_CASE = (
    SimpleNamespace(
        bulk_config=BULK_Si_CONVENTIONAL,
        miller_indices=(0, 0, 1),
        number_of_layers=2,
        vacuum=0.0,
    ),
    SimpleNamespace(
        bulk_config=BULK_Ge_CONVENTIONAL,
        miller_indices=(0, 0, 1),
        number_of_layers=2,
        vacuum=0.0,
    ),
    INTERFACE_Si_001_Ge_001,
)


GRAPHENE_NICKEL_TEST_CASE = (
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
    3.0,  # gap between graphene and nickel
    10.0,  # vacuum
    90,  # max area
    {
        OSPlatform.DARWIN: GRAPHENE_NICKEL_INTERFACE_TOP_HCP,
        OSPlatform.OTHER: GRAPHENE_NICKEL_INTERFACE_TOP_HCP_GH_WF,
    },
)

PRECISION = 1e-3


@pytest.mark.parametrize("substrate, film, expected_interface", [Si_Ge_SIMPLE_INTERFACE_TEST_CASE])
def test_simple_interface_builder(substrate, film, expected_interface):
    builder = InterfaceBuilder(build_parameters=InterfaceBuilderParameters(make_primitive=False))
    substrate_slab_config = SlabConfiguration.from_parameters(
        substrate.bulk_config,
        substrate.miller_indices,
        substrate.number_of_layers,
        vacuum=substrate.vacuum,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        film.bulk_config,
        film.miller_indices,
        film.number_of_layers,
        vacuum=film.vacuum,
    )

    analyzer = InterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
    )

    film_configuration = analyzer.film_strained_configuration
    substrate_configuration = analyzer.substrate_strained_configuration
    vacuum_configuration = film_slab_config.vacuum_configuration

    config = InterfaceConfiguration(
        stack_components=[substrate_configuration, film_configuration, vacuum_configuration],
    )
    interface = builder.get_material(config)
    assert_two_entities_deep_almost_equal(interface, expected_interface)


@pytest.mark.parametrize("substrate, film, expected_interface", [Si_Ge_SIMPLE_INTERFACE_TEST_CASE])
def test_create_simple_interface_between_slabs(substrate, film, expected_interface):
    substrate_slab_config = SlabConfiguration.from_parameters(
        material_or_dict=substrate.bulk_config,
        miller_indices=substrate.miller_indices,
        number_of_layers=substrate.number_of_layers,
        vacuum=0,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        material_or_dict=film.bulk_config,
        miller_indices=film.miller_indices,
        number_of_layers=film.number_of_layers,
        vacuum=0,
    )

    substrate_slab = SlabBuilder().get_material(substrate_slab_config)
    film_slab = SlabBuilder().get_material(film_slab_config)

    interface = create_interface_simple_between_slabs(
        substrate_slab=substrate_slab,
        film_slab=film_slab,
        gap=None,
        vacuum=0.0,
        xy_shift=[0, 0],
    )
    interface.metadata.build = []
    assert_two_entities_deep_almost_equal(interface, expected_interface)


@pytest.mark.parametrize("substrate, film, expected_interface", [Si_Ge_SIMPLE_INTERFACE_TEST_CASE])
def test_create_simple_interface(substrate, film, expected_interface):
    interface = create_interface_simple(
        substrate_crystal=substrate.bulk_config,
        film_crystal=film.bulk_config,
        substrate_miller_indices=substrate.miller_indices,
        film_miller_indices=film.miller_indices,
        substrate_number_of_layers=substrate.number_of_layers,
        film_number_of_layers=film.number_of_layers,
        gap=None,
        vacuum=0.0,
        xy_shift=[0, 0],
    )
    interface.metadata.build = []
    assert_two_entities_deep_almost_equal(interface, expected_interface)


@pytest.mark.parametrize(
    "material_config, config_params, expected_interface",
    [
        (
            GRAPHENE,
            {
                "twist_angle": 60,
                "distance_z": 3.0,
                "ribbon_width": 3,
                "ribbon_length": 5,
                "vacuum_x": 2.0,
                "vacuum_y": 2.0,
            },
            TWISTED_INTERFACE_GRAPHENE_GRAPHENE_60,
        ),
    ],
)
def test_create_twisted_interface(material_config, config_params, expected_interface):
    material = Material.create(material_config)

    nanoribbon1 = create_nanoribbon(
        material=material,
        width=3,
        length=3,
        vacuum_width=15.0,
        vacuum_length=15.0,
        edge_type=EdgeTypesEnum.armchair,
    )

    nanoribbon2 = create_nanoribbon(
        material=material,
        width=3,
        length=3,
        vacuum_width=15.0,
        vacuum_length=15.0,
        edge_type=EdgeTypesEnum.armchair,
    )

    interface = create_interface_twisted(
        material1=nanoribbon1,
        material2=nanoribbon2,
        angle=config_params["twist_angle"],
        vacuum_x=config_params["vacuum_x"],
        vacuum_y=config_params["vacuum_y"],
        gap=config_params["distance_z"],
    )

    assert_two_entities_deep_almost_equal(interface, expected_interface)


@pytest.mark.parametrize(
    "material_config, analyzer_params, direction, gaps, expected_interface",
    [
        (
            GRAPHENE,
            {"target_angle": 13.0, "angle_tolerance": 0.5, "max_supercell_matrix_int": 5, "return_first_match": True},
            AxisEnum.z,
            3.0,
            INTERFACE_GRAPHENE_GRAPHENE_Z,
        ),
        (
            GRAPHENE,
            {"target_angle": 13.0, "angle_tolerance": 0.5, "max_supercell_matrix_int": 5, "return_first_match": True},
            AxisEnum.x,
            None,  # testing no gaps
            INTERFACE_GRAPHENE_GRAPHENE_X,
        ),
    ],
)
def test_commensurate_interface_creation(material_config, analyzer_params, direction, gaps, expected_interface):
    material = Material.create(material_config)

    slab = create_slab(
        crystal=material,
        miller_indices=(0, 0, 1),
        use_conventional_cell=True,
        use_orthogonal_c=True,
        number_of_layers=1,
        vacuum=0.0,
    )

    interface = create_interface_commensurate(
        material=slab,
        target_angle=analyzer_params["target_angle"],
        angle_tolerance=analyzer_params["angle_tolerance"],
        max_repetition_int=analyzer_params["max_supercell_matrix_int"],
        return_first_match=analyzer_params["return_first_match"],
        direction=direction,
        gap=gaps,
    )

    assert_two_entities_deep_almost_equal(interface, expected_interface, atol=PRECISION)


def test_create_slab_with_conventional_cell_stores_crystal_hashes_in_metadata():
    miller_indices = (0, 0, 1)
    material = Material.create(BULK_Ni_PRIMITIVE)
    expected_crystal = CrystalLatticePlanesMaterialAnalyzer(
        material=material, miller_indices=miller_indices
    ).material_with_conventional_lattice

    slab = create_slab(
        crystal=material,
        miller_indices=miller_indices,
        use_conventional_cell=True,
        use_orthogonal_c=True,
        number_of_layers=1,
        vacuum=0.0,
    )
    serialized_slab = slab.model_dump()
    crystal = serialized_slab["metadata"]["build"][-1]["configuration"]["stack_components"][0]["crystal"]

    assert crystal[HASH_KEY] == expected_crystal.hash
    assert crystal[SCALED_HASH_KEY] == expected_crystal.scaled_hash
    assert "bulkId" not in serialized_slab["metadata"]


@pytest.mark.parametrize(
    "interface_config, expected_coordinate_level",
    [(GRAPHENE_NICKEL_INTERFACE_TOP_HCP, 12.048)],
)
def test_find_interface_z_level(interface_config, expected_coordinate_level):
    interface_material = MaterialWithBuildMetadata.create(interface_config)
    builder = InterfaceBuilder()

    interface_z_level = builder._find_interface_coordinate_level(interface_material, axis=AxisEnum.z.value)

    assert np.allclose(interface_z_level, expected_coordinate_level, atol=PRECISION)
