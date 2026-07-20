import copy
from types import SimpleNamespace

import numpy as np
import pytest
from mat3ra.made.basis import Basis
from mat3ra.made.lattice import COORDINATE_TOLERANCE
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.interface.zsl import ZSLInterfaceAnalyzer
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.base.builder import InterfaceBuilder
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.base.configuration import (
    InterfaceConfiguration,
)
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface.zsl.helpers import (
    create_interface_zsl,
    create_interface_zsl_between_slabs,
)
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab import SlabBuilder, SlabConfiguration
from mat3ra.made.tools.build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from mat3ra.standata.materials import Materials

from .fixtures.bulk import BULK_Ni_PRIMITIVE
from .fixtures.interface.gr_ni_111_top_hcp import (
    GRAPHENE_NICKEL_INTERFACE_TOP_HCP,
    GRAPHENE_NICKEL_INTERFACE_TOP_HCP_GH_WF,
)
from .fixtures.interface.zsl import DIAMOND_GaAs_INTERFACE, DIAMOND_GaAs_INTERFACE_GH
from .fixtures.monolayer import GRAPHENE
from .utils import OSPlatform, assert_interfaces_almost_equal, get_platform_specific_value

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

BULK_DIAMOND = Materials.get_by_name_first_match("Diamond")
BULK_GaAs = Materials.get_by_name_first_match("GaAs")

DIAMOND_GAAS_CSL_TEST_CASE = (
    SimpleNamespace(
        bulk_config=BULK_DIAMOND,
        miller_indices=(0, 0, 1),
        number_of_layers=1,
        vacuum=0.0,
    ),
    SimpleNamespace(
        bulk_config=BULK_GaAs,
        miller_indices=(0, 0, 1),
        number_of_layers=1,
        vacuum=0.0,
    ),
    1.5,  # gap between diamond and gaas
    10.0,  # vacuum
    70.0,  # max area
    {
        OSPlatform.DARWIN: DIAMOND_GaAs_INTERFACE,
        OSPlatform.OTHER: DIAMOND_GaAs_INTERFACE_GH,
    },
)


MAX_AREA_RATIO_TOL = 0.09
MAX_LENGTH_TOL = 0.05
MAX_ANGLE_TOL = 0.02


# The default comparison tolerance (atol=1e-9) in assert_two_entities_deep_almost_equal
# is too strict for cross-platform floating-point variations in ZSL interface coordinate
# calculations, which can differ on the order of 10**-8 to 10**-7 across different systems
# and compilers. We instead use the coordinate tolerance defined in mat3ra.made.lattice,
# which is 10**-COORDINATE_TOLERANCE (10**-6 = 1e-6).
UPDATED_COORDINATE_TOLERANCE = 10**-COORDINATE_TOLERANCE


def to_basis_obj(b_dict: dict) -> Basis:
    """
    Ensure a basis dictionary has sequential IDs and convert it to a Basis object.

    Args:
        b_dict (dict): The dictionary representation of a basis.

    Returns:
        Basis: The instantiated Basis object.
    """
    b_dict = copy.deepcopy(b_dict)
    for key in ["elements", "coordinates"]:
        if key in b_dict and isinstance(b_dict[key], list):
            for idx, item in enumerate(b_dict[key]):
                if isinstance(item, dict) and "id" not in item:
                    item["id"] = idx
    return Basis(**b_dict)


def are_bases_almost_equal(b1: Basis, b2: Basis, atol: float) -> bool:
    """
    Compare two Basis objects for equality with permuted ordering and coordinate tolerance.

    Args:
        b1 (Basis): The first Basis object.
        b2 (Basis): The second Basis object.
        atol (float): Absolute tolerance for coordinate comparison.

    Returns:
        bool: True if the bases are physically equivalent within tolerance, False otherwise.
    """
    if b1.number_of_atoms != b2.number_of_atoms:
        return False
    n = b1.number_of_atoms
    self_elements, other_elements = b1.elements.values, b2.elements.values
    self_coords, other_coords = b1.coordinates.values, b2.coordinates.values
    self_labels = b1.labels.values if (b1.labels and len(b1.labels.values) == n) else [None] * n
    other_labels = b2.labels.values if (b2.labels and len(b2.labels.values) == n) else [None] * n
    self_constraints = b1.constraints.values if (b1.constraints and len(b1.constraints.values) == n) else [None] * n
    other_constraints = b2.constraints.values if (b2.constraints and len(b2.constraints.values) == n) else [None] * n

    other_indices_left = set(range(n))
    for i in range(n):
        found = False
        elem, coord, lbl, const = self_elements[i], self_coords[i], self_labels[i], self_constraints[i]
        for j in list(other_indices_left):
            if other_elements[j] == elem and other_labels[j] == lbl and other_constraints[j] == const:
                if np.allclose(other_coords[j], coord, atol=atol):
                    other_indices_left.remove(j)
                    found = True
                    break
        if not found:
            return False
    return True


@pytest.mark.parametrize(
    "substrate, film,gap, vacuum, max_area, expected_interface",
    [GRAPHENE_NICKEL_TEST_CASE, DIAMOND_GAAS_CSL_TEST_CASE],
)
def test_zsl_interface_builder(substrate, film, gap, vacuum, max_area, expected_interface):
    """Test creating Si/Ge interface using ZSL approach."""
    substrate_slab_config = SlabConfiguration.from_parameters(
        substrate.bulk_config, substrate.miller_indices, substrate.number_of_layers, vacuum=substrate.vacuum
    )
    film_slab_config = SlabConfiguration.from_parameters(
        film.bulk_config, film.miller_indices, film.number_of_layers, vacuum=film.vacuum
    )

    # Use ZSLInterfaceAnalyzer to get strained slab configurations
    analyzer = ZSLInterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
        max_area=max_area,
        max_area_ratio_tol=MAX_AREA_RATIO_TOL,
        max_length_tol=MAX_LENGTH_TOL,
        max_angle_tol=MAX_ANGLE_TOL,
        reduce_result_cell=False,
    )

    interface_configurations = analyzer.get_strained_configurations()

    selected_config = interface_configurations[0]
    vacuum_configuration = VacuumConfiguration(size=vacuum)
    interface_config = InterfaceConfiguration(
        stack_components=[
            selected_config.substrate_configuration,
            selected_config.film_configuration,
            vacuum_configuration,
        ],
        gaps=[gap, gap],
    )

    builder = InterfaceBuilder()
    interface = builder.get_material(interface_config)

    # remove metadata
    interface.metadata.build = []
    expected_interface = Material.create(get_platform_specific_value(expected_interface))

    assert interface.basis.number_of_atoms == expected_interface.basis.number_of_atoms

    assert_interfaces_almost_equal(interface, expected_interface)


@pytest.mark.parametrize("substrate, film,gap, vacuum, max_area,  expected_interface", [GRAPHENE_NICKEL_TEST_CASE])
def test_create_zsl_interface(substrate, film, gap, vacuum, max_area, expected_interface):
    interface = create_interface_zsl(
        substrate_crystal=substrate.bulk_config,
        film_crystal=film.bulk_config,
        substrate_miller_indices=substrate.miller_indices,
        film_miller_indices=film.miller_indices,
        substrate_number_of_layers=substrate.number_of_layers,
        film_number_of_layers=film.number_of_layers,
        substrate_termination_formula=None,
        film_termination_formula=None,
        gap=gap,
        vacuum=vacuum,
        xy_shift=[0, 0],
        max_area=max_area,
        max_area_ratio_tol=MAX_AREA_RATIO_TOL,
        max_length_tol=MAX_LENGTH_TOL,
        max_angle_tol=MAX_ANGLE_TOL,
        use_conventional_cell=True,
        reduce_result_cell=False,
        reduce_result_cell_to_primitive=True,
    )
    interface.metadata.build = []
    expected_interface = get_platform_specific_value(expected_interface)
    assert_interfaces_almost_equal(interface, expected_interface)


@pytest.mark.parametrize(
    "substrate, film, gap, vacuum, max_area, expected_interface",
    [GRAPHENE_NICKEL_TEST_CASE, DIAMOND_GAAS_CSL_TEST_CASE],
)
def test_create_zsl_interface_between_slabs(substrate, film, gap, vacuum, max_area, expected_interface):
    substrate_slab_config = SlabConfiguration.from_parameters(
        material_or_dict=substrate.bulk_config,
        miller_indices=substrate.miller_indices,
        number_of_layers=substrate.number_of_layers,
        vacuum=0.0,
        termination_top_formula=None,
        use_conventional_cell=True,
    )
    film_slab_config = SlabConfiguration.from_parameters(
        material_or_dict=film.bulk_config,
        miller_indices=film.miller_indices,
        number_of_layers=film.number_of_layers,
        vacuum=0.0,
        termination_bottom_formula=None,
        use_conventional_cell=True,
    )

    substrate_slab = SlabBuilder().get_material(substrate_slab_config)
    film_slab = SlabBuilder().get_material(film_slab_config)

    interface = create_interface_zsl_between_slabs(
        substrate_slab=substrate_slab,
        film_slab=film_slab,
        gap=gap,
        vacuum=vacuum,
        xy_shift=[0, 0],
        max_area=max_area,
        max_area_ratio_tol=MAX_AREA_RATIO_TOL,
        max_length_tol=MAX_LENGTH_TOL,
        max_angle_tol=MAX_ANGLE_TOL,
        reduce_result_cell=False,
        reduce_result_cell_to_primitive=True,
    )
    expected_interface = get_platform_specific_value(expected_interface)
    assert_interfaces_almost_equal(interface, expected_interface)
