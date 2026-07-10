import json
from pathlib import Path

import numpy as np
import pytest
from mat3ra.made.basis import Basis, Coordinates
from mat3ra.made.lattice import Lattice
from mat3ra.made.material import Material
from mat3ra.utils import assertion as assertion_utils
from unit.fixtures.bulk import BULK_Si_PRIMITIVE
from unit.fixtures.slab import BULK_Si_CONVENTIONAL
from unit.utils import assert_two_entities_deep_almost_equal

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


def test_model_dump_includes_hashes():
    material = Material.create_default()
    serialized_material = material.model_dump()

    assert serialized_material[HASH_KEY] == material.hash
    assert serialized_material[SCALED_HASH_KEY] == material.scaled_hash
