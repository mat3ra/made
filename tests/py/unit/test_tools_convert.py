import numpy as np
import pytest
from ase import Atoms
from ase.build import make_supercell, molecule
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.made.material import Material
from mat3ra.made.tools.convert import from_ase, from_poscar, from_pymatgen, to_ase, to_poscar, to_pymatgen
from mat3ra.made.tools.convert.utils import DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE, calculate_padded_cell_simple_cubic
from mat3ra.standata.materials import Materials
from mat3ra.utils import assertion as assertion_utils
from pymatgen.core.structure import Element, Lattice, Structure

from .fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE
from .fixtures.monolayer import GRAPHENE
from .fixtures.thrid_party.ase_atoms import (
    ASE_MOLECULE_H2O,
    BULK_SI_LABELS,
    BULK_SI_LATTICE_A,
    BULK_SI_LATTICE_ALPHA,
    ASE_BULK_Si,
)

PYMATGEN_LATTICE = Lattice.from_parameters(a=3.84, b=3.84, c=3.84, alpha=120, beta=90, gamma=60)
PYMATGEN_STRUCTURE = Structure(PYMATGEN_LATTICE, ["Si", "Si"], [[0, 0, 0], [0.75, 0.5, 0.75]])
PYMATGEN_STRUCTURE_WITH_CIF_LABELS = Structure(
    PYMATGEN_LATTICE, ["Si", "Si"], [[0, 0, 0], [0.75, 0.5, 0.75]], labels=["Si1", "Si2"]
)

POSCAR_CONTENT = """Si2
1.0
   3.3489202364344242    0.0000000000000000    1.9335000000000004
   1.1163067454781415    3.1573922784475164    1.9335000000000004
   0.0000000000000000    0.0000000000000000    3.8670000000000000
Si
2
direct
   0.0000000000000000    0.0000000000000000    0.0000000000000000 Si
   0.2500000000000000    0.2500000000000000    0.2500000000000000 Si
"""


@pytest.mark.parametrize(
    "material_config, expected_lattice_params, expected_species, expected_frac_coords, expected_labels",
    [
        (
            Material.__default_config__,
            {"a": 3.867, "b": 3.867, "c": 3.867, "alpha": 60, "beta": 60, "gamma": 60},
            [Element("Si"), Element("Si")],
            [[0.0, 0.0, 0.0], [0.25, 0.25, 0.25]],
            ["Si", "Si"],
        ),
        (
            GRAPHENE,
            {"a": 2.467291, "b": 2.467291, "c": 20.0, "alpha": 90, "beta": 90, "gamma": 120},
            [Element("C"), Element("C")],
            [[0.0, 0.0, 0.0], [0.333333, 0.666667, 0.0]],
            ["C", "C"],
        ),
    ],
)
def test_to_pymatgen(material_config, expected_lattice_params, expected_species, expected_frac_coords, expected_labels):
    material = Material.create(material_config)
    structure = to_pymatgen(material)
    assert isinstance(structure, Structure)
    assert np.allclose(structure.lattice.parameters, tuple(expected_lattice_params.values()), atol=1e-6)
    assert structure.species == expected_species
    assert structure.labels == expected_labels
    assert np.allclose(structure.frac_coords, expected_frac_coords, atol=1e-6)

    structure_to_poscar_str = structure.to(fmt="poscar")
    material_to_poscar_str = to_poscar(material)
    assert structure_to_poscar_str == material_to_poscar_str


@pytest.mark.parametrize("structure", [PYMATGEN_STRUCTURE, PYMATGEN_STRUCTURE_WITH_CIF_LABELS])
def test_from_pymatgen(structure):
    material_data = from_pymatgen(structure)
    assert material_data["lattice"]["a"] == 3.84
    assert material_data["lattice"]["alpha"] == 120
    assert material_data["basis"]["elements"] == [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}]
    assert material_data["basis"]["labels"] == []

    converted_material = Material.create(material_data)
    default_material = Material.create_default()
    assertion_utils.assert_deep_almost_equal(converted_material, default_material)


def test_to_poscar():
    material = Material.create_default()
    poscar = to_poscar(material)
    assert poscar == POSCAR_CONTENT


def test_from_poscar():
    material_data = from_poscar(POSCAR_CONTENT)
    assert material_data["lattice"]["a"] == 3.867
    assert material_data["lattice"]["alpha"] == 60


@pytest.mark.parametrize(
    "labels_array, expected_tags",
    [([{"id": 0, "value": 0}, {"id": 1, "value": 1}], [0, 1]), ([], [0, 0])],
)
def test_to_ase(labels_array, expected_tags):
    material = Material.create_default()
    material.basis.labels = ArrayWithIds.from_list_of_dicts(labels_array)
    ase_atoms = to_ase(material)
    assert isinstance(ase_atoms, Atoms)
    assert np.allclose(
        ase_atoms.get_cell().tolist(),
        [
            [3.3489202364344242, 0.0, 1.9335000000000004],
            [1.1163067454781415, 3.1573922784475164, 1.9335000000000004],
            [0.0, 0.0, 3.8670000000000000],
        ],
    )
    assert ase_atoms.get_chemical_symbols() == ["Si", "Si"]
    assert np.allclose(ase_atoms.get_scaled_positions().tolist(), [[0.0, 0.0, 0.0], [0.25, 0.25, 0.25]])
    assert ase_atoms.get_tags().tolist() == expected_tags


@pytest.mark.parametrize(
    "ase_atoms, expected_lattice_a, expected_lattice_alpha, expected_labels,"
    + " expected_is_non_periodic, expected_lattice_type",
    [
        (
            ASE_BULK_Si,
            BULK_SI_LATTICE_A,
            BULK_SI_LATTICE_ALPHA,
            BULK_SI_LABELS,
            False,
            None,
        ),
        (
            ASE_MOLECULE_H2O,
            None,
            None,
            [],
            True,
            "CUB",
        ),
    ],
)
def test_from_ase(
    ase_atoms,
    expected_lattice_a,
    expected_lattice_alpha,
    expected_labels,
    expected_is_non_periodic,
    expected_lattice_type,
):
    material_data = from_ase(ase_atoms)
    if expected_lattice_a is not None:
        assertion_utils.assert_almost_equal_numbers(material_data["lattice"]["a"], expected_lattice_a, atol=1e-4)
    if expected_lattice_alpha is not None:
        assert material_data["lattice"]["alpha"] == expected_lattice_alpha
    assert material_data["basis"]["labels"] == expected_labels
    assert material_data["isNonPeriodic"] == expected_is_non_periodic
    if expected_lattice_type is not None:
        assert material_data["lattice"]["type"] == expected_lattice_type


FESE = Materials.get_by_name_first_match("FeSe")
FESE_LABELS = [{"id": 0, "value": 1}, {"id": 1, "value": 2}]
FESE_LABELS_WITH_ZERO = [{"id": 0, "value": 0}, {"id": 1, "value": 2}]
FESE_WITH_LABELS = {**FESE, "basis": {**FESE["basis"], "labels": FESE_LABELS}}
FESE_WITH_LABELS_WITH_ZERO = {**FESE, "basis": {**FESE["basis"], "labels": FESE_LABELS_WITH_ZERO}}
interface_with_id_gap = Material.create(GRAPHENE_NICKEL_INTERFACE)
interface_with_id_gap.basis.remove_atom_by_id(1)
GRAPHENE_NICKEL_INTERFACE_WITH_ID_GAP = interface_with_id_gap.to_dict()
IDENTITY_MATRIX = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
SUPERCELL_MATRIX_2X1X1 = [[2, 0, 0], [0, 1, 0], [0, 0, 1]]


@pytest.mark.parametrize(
    "material_config, supercell_matrix, expected_tags, expected_labels",
    [
        (FESE_WITH_LABELS, IDENTITY_MATRIX, [1, 2, -1, -1], FESE_LABELS),
        (FESE_WITH_LABELS_WITH_ZERO, IDENTITY_MATRIX, [0, 2, -1, -1], FESE_LABELS_WITH_ZERO),
        (
            GRAPHENE_NICKEL_INTERFACE_WITH_ID_GAP,
            IDENTITY_MATRIX,
            [0, 0, 1, 1],
            [{"id": 0, "value": 0}, {"id": 1, "value": 0}, {"id": 2, "value": 1}, {"id": 3, "value": 1}],
        ),
        (
            FESE_WITH_LABELS,
            SUPERCELL_MATRIX_2X1X1,
            [1, 2, -1, -1, 1, 2, -1, -1],
            [{"id": 0, "value": 1}, {"id": 1, "value": 2}, {"id": 4, "value": 1}, {"id": 5, "value": 2}],
        ),
    ],
)
def test_from_ase_round_trip(material_config, supercell_matrix, expected_tags, expected_labels):
    ase_atoms = make_supercell(to_ase(Material.create(material_config)), supercell_matrix)
    assert ase_atoms.get_tags().tolist() == expected_tags
    assert from_ase(ase_atoms)["basis"]["labels"] == expected_labels


@pytest.mark.parametrize(
    "material_config, supercell_matrix, expected_site_labels, expected_labels",
    [
        (FESE_WITH_LABELS, IDENTITY_MATRIX, ["1", "2", "-1", "-1"], FESE_LABELS),
        (FESE_WITH_LABELS_WITH_ZERO, IDENTITY_MATRIX, ["0", "2", "-1", "-1"], FESE_LABELS_WITH_ZERO),
        (
            GRAPHENE_NICKEL_INTERFACE_WITH_ID_GAP,
            IDENTITY_MATRIX,
            ["0", "0", "1", "1"],
            [{"id": 0, "value": 0}, {"id": 1, "value": 0}, {"id": 2, "value": 1}, {"id": 3, "value": 1}],
        ),
        (
            FESE_WITH_LABELS,
            SUPERCELL_MATRIX_2X1X1,
            ["1", "1", "2", "2", "-1", "-1", "-1", "-1"],
            [{"id": 0, "value": 1}, {"id": 1, "value": 1}, {"id": 2, "value": 2}, {"id": 3, "value": 2}],
        ),
    ],
)
def test_from_pymatgen_round_trip(material_config, supercell_matrix, expected_site_labels, expected_labels):
    structure = to_pymatgen(Material.create(material_config))
    structure.make_supercell(supercell_matrix)
    assert structure.labels == expected_site_labels
    assert from_pymatgen(structure)["basis"]["labels"] == expected_labels


TOLERANCE = 1e-4

H2_EXPECTED_LATTICE_A = DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE
O2_EXPECTED_LATTICE_A = 3.7379
H2O_EXPECTED_LATTICE_A = 3.0530
C2H4_EXPECTED_LATTICE_A = 6.1754


@pytest.mark.parametrize(
    "molecule_name, expected_lattice_a",
    [
        ("H2", H2_EXPECTED_LATTICE_A),
        ("O2", O2_EXPECTED_LATTICE_A),
        ("H2O", H2O_EXPECTED_LATTICE_A),
        ("C2H4", C2H4_EXPECTED_LATTICE_A),
    ],
)
def test_calculate_padded_cell_simple_cubic(molecule_name, expected_lattice_a):
    atoms = molecule(molecule_name)
    cell_vectors = calculate_padded_cell_simple_cubic(atoms.get_positions().tolist())
    lattice_a = cell_vectors[0][0]
    assert np.isclose(lattice_a, expected_lattice_a, atol=TOLERANCE)
    assert lattice_a >= DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE
    assert np.isclose(cell_vectors[0][0], cell_vectors[1][1], atol=TOLERANCE)
    assert np.isclose(cell_vectors[0][0], cell_vectors[2][2], atol=TOLERANCE)
