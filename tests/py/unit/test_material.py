import json
from pathlib import Path

import numpy as np
import pytest
from mat3ra.made.basis import Basis, Coordinates
from mat3ra.made.basis.atomic_properties import AtomicProperties
from mat3ra.made.lattice import Lattice
from mat3ra.made.material import Material
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.defective_structures.three_dimensional.solid_solution.helpers import create_solid_solution
from mat3ra.made.tools.build.defective_structures.zero_dimensional.point_defect.helpers import (
    create_defect_point_substitution,
    create_defect_point_vacancy,
)
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.modify import (
    filter_by_ids,
    filter_by_label,
    interface_get_part,
    interface_label_parts_by_elements,
)
from mat3ra.made.tools.operations.core.binary import merge
from mat3ra.made.tools.operations.core.unary import translate
from mat3ra.utils import assertion as assertion_utils
from unit.fixtures.bulk import BULK_FeSe_WITH_CONSTRAINTS, BULK_FeSe_WITH_LABELS, BULK_Si_PRIMITIVE
from unit.fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE_CONSTRAINED
from unit.fixtures.slab import BULK_Si_CONVENTIONAL
from unit.utils import assert_two_entities_deep_almost_equal

FIXED = [False, False, False]

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"
HASH_KEY = "hash"
SCALED_HASH_KEY = "scaledHash"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def test_create_default():
    material = Material.create_default()
    assert isinstance(material.basis, Basis)
    assert isinstance(material.basis.coordinates, Coordinates)
    assert isinstance(material.lattice, Lattice)
    assert material.name == Material.__default_config__["name"]


def test_create():
    material = Material.create(BULK_Si_CONVENTIONAL)
    assert isinstance(material.basis, Basis)
    assert isinstance(material.basis.coordinates, Coordinates)
    assert isinstance(material.lattice, Lattice)
    assert_two_entities_deep_almost_equal(material, BULK_Si_CONVENTIONAL)


def test_create_with_cell_as_list():
    # The key cell should be ignored and Basis.Cell created from Lattice by Material
    cell = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    config = {**Material.__default_config__, "basis": {**Material.__default_config__["basis"], "cell": cell}}

    material = Material.create(config)
    assert isinstance(material.basis, Basis)
    assert material.basis.cell.vector_arrays == material.lattice.vector_arrays


def test_material_to_json():
    material = Material.create_default()
    # Remove all keys that are null in the config
    assert_two_entities_deep_almost_equal(material, Material.__default_config__)


def test_material_clone():
    material = Material.create_default()
    clone = material.clone()
    assert_two_entities_deep_almost_equal(material, clone)


def test_material_to_from_cartesian():
    material = Material.create_default()
    assert material.basis.is_in_crystal_units is True
    assert material.basis.is_in_cartesian_units is False
    material.to_cartesian()
    assert material.basis.is_in_crystal_units is False
    assert material.basis.is_in_cartesian_units is True
    assert np.allclose(material.basis.coordinates.values[1], [1.1163, 0.7893, 1.9335], atol=1e-4)
    material.to_crystal()
    assert material.basis.is_in_crystal_units is True
    assert material.basis.is_in_cartesian_units is False
    assert np.allclose(material.basis.coordinates.values[1], [0.25, 0.25, 0.25], atol=1e-4)
    assert_two_entities_deep_almost_equal(material, Material.__default_config__)


def test_material_to_cartesian_to_crystal_repeated():
    material = Material.create_default()
    material.to_cartesian()
    material.to_cartesian()
    assert np.allclose(material.basis.coordinates.values[1], [1.1163, 0.7893, 1.9335], atol=1e-4)
    material.to_crystal()
    material.to_crystal()
    assert_two_entities_deep_almost_equal(material, Material.__default_config__)


def test_basis_to_json():
    material = Material.create_default()
    basis = material.basis
    assert_two_entities_deep_almost_equal(basis, Material.__default_config__["basis"])


def test_basis_cell_lattice_sync():
    """Test synchronization between basis.cell and material.lattice"""
    material = Material.create_default()
    # Change lattice vectors
    new_vectors = [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]]
    new_lattice = Lattice.from_vectors_array(new_vectors)
    material.set_lattice(new_lattice)
    # Verify basis.cell matches new lattice vectors
    assertion_utils.assert_deep_almost_equal(new_vectors, material.basis.cell.vector_arrays)
    assertion_utils.assert_deep_almost_equal(new_vectors, material.lattice.vector_arrays)
    # Verify basis coordinates are still correct


@pytest.mark.parametrize(
    "initial_labels, reset_labels, expected_final",
    [
        # Test resetting with empty list
        ([1, 2], [], []),
        # Test resetting with None
        ([1, 2], None, []),
        # Test normal behavior with non-empty lists
        ([], [1, 2], [1, 2]),
    ],
)
def test_set_labels_from_list(initial_labels, reset_labels, expected_final):
    material = Material.create(BULK_Si_PRIMITIVE)

    if initial_labels:
        material.basis.set_labels_from_list(initial_labels)
        assert len(material.basis.labels.values) == len(initial_labels)
        assert material.basis.labels.values == initial_labels

    material.basis.set_labels_from_list(reset_labels)

    assert len(material.basis.labels.values) == len(expected_final)
    assert material.basis.labels.values == expected_final


@pytest.mark.parametrize(
    "material_config, operation, expected_labels, expected_constraints",
    [
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: create_defect_point_vacancy(
                material, material.basis.coordinates.values[1], "closest_site"
            ),
            [0, 0, 1, 1],
            [None, None, None, FIXED],
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: create_defect_point_substitution(
                material, material.basis.coordinates.values[3], "Ge", "closest_site"
            ),
            [0, 0, 0, 1, 1],
            [None, None, None, FIXED, None],
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: interface_get_part(material, InterfacePartsEnum.SUBSTRATE),
            [0, 0, 0],
            [None, None, None],
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: merge([filter_by_label(material, 1), filter_by_label(material, 0)]),
            [1, 1, 0, 0, 0],
            [None, FIXED, None, None, None],
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: interface_label_parts_by_elements(
                interface_get_part(material, InterfacePartsEnum.FILM), ["Ni"]
            ),
            [1, 1],
            [None, FIXED],
        ),
        (
            BULK_FeSe_WITH_LABELS,
            lambda material: create_defect_point_substitution(
                material, material.basis.coordinates.values[2], "S", "closest_site"
            ),
            [1, 2, None, None],
            [None, None, None, None],
        ),
        (
            BULK_FeSe_WITH_LABELS,
            lambda material: create_solid_solution(material, "Fe", "Co", 0.5, seed=42),
            [2, None, None, 1],
            [None, None, None, None],
        ),
        (
            BULK_FeSe_WITH_CONSTRAINTS,
            lambda material: merge(
                [material, translate(MaterialWithBuildMetadata.create(BULK_FeSe_WITH_LABELS), [0, 0, 0.5])]
            ),
            [None, None, None, None, 1, 2, None, None],
            [FIXED, None, None, None, None, None, None, None],
        ),
        (
            GRAPHENE_NICKEL_INTERFACE_CONSTRAINED,
            lambda material: filter_by_ids(material, [2, 4], reset_ids=True),
            [0, 1],
            [None, FIXED],
        ),
    ],
)
def test_atomic_properties_follow_atom_ids(material_config, operation, expected_labels, expected_constraints):
    basis = operation(MaterialWithBuildMetadata.create(material_config)).basis
    assert basis.atomic_labels_array == expected_labels
    assert basis.constraints.to_padded_array_of_values(basis.elements.ids, None) == expected_constraints
    assert all(set(item.values.ids) <= set(basis.elements.ids) for item in basis.atomic_properties.root)


@pytest.mark.parametrize("properties", [BULK_FeSe_WITH_LABELS["basis"]["atomic_properties"]])
def test_atomic_properties_from_list_of_dicts(properties):
    atomic_properties = AtomicProperties.from_list_of_dicts(properties)
    assert atomic_properties.to_dict() == properties


@pytest.mark.parametrize("fixture_file", ["si-standata.json", "Graphene.json"])
def test_calculate_hash(fixture_file):
    fixture = load_fixture(fixture_file)
    material = Material.create(fixture)
    assert material.hash == fixture["hash"]
    assert material.scaled_hash == fixture["scaledHash"]


def test_calculate_hash_feo_standata():
    from mat3ra.standata.materials import Materials

    expected_hashes = load_fixture("hashes.json")["FeO"]
    data = Materials.get_by_name_first_match("FeO")
    material = Material.create(data)
    assert material.hash == expected_hashes["hash"]
    assert material.scaled_hash == expected_hashes["scaledHash"]


def test_calculate_hash_with_labels():
    material = Material.create(load_fixture("si-standata.json"))
    material.set_labels_from_list([0, 1])
    assert material.hash == load_fixture("hashes.json")["SiliconWithLabels"]["hash"]


@pytest.mark.parametrize(
    "coordinate, equivalent_coordinate",
    [(0.999998, 0.0), (-1e-06, 0.0), (0.0006, 0.0014), (0.5015, 0.502), (1.234, 0.234), (-2.0005, 0.9995)],
)
def test_calculate_hash_coordinate_rounding(coordinate, equivalent_coordinate):
    material, reference = Material.create_default(), Material.create_default()
    material.set_coordinates([[coordinate, 0.0, 0.0], [0.25, 0.25, 0.25]])
    reference.set_coordinates([[equivalent_coordinate, 0.0, 0.0], [0.25, 0.25, 0.25]])
    assert material.hash == reference.hash


def test_model_dump_includes_hashes():
    material = Material.create_default()
    serialized_material = material.model_dump()

    assert serialized_material[HASH_KEY] == material.hash
    assert serialized_material[SCALED_HASH_KEY] == material.scaled_hash
