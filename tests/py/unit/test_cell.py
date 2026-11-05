from mat3ra.code.vector import RoundedVector3D
from mat3ra.made.cell import Cell

VECTORS = [
    [1.0, 0.0, 0.0],
    [0.0, 2.0, 0.0],
    [0.0, 0.0, 3.0],
]

VECTORS_VOLUME = 6.0

VECTORS_EQUAL_UP_TO_PRECISION_4 = [
    [1.00001, 0.0, 0.0],
    [0.0, 2.00001, 0.0],
    [0.0, 0.0, 3.00001],
]

VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME = 6.000110000600002
VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4 = 6.0001
VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_5 = 6.00011


def test_cell_creation():
    cell = Cell(a=RoundedVector3D(VECTORS[0]), b=RoundedVector3D(VECTORS[1]), c=RoundedVector3D(VECTORS[2]))
    assert cell.a.value == VECTORS[0]
    assert cell.b.value == VECTORS[1]
    assert cell.c.value == VECTORS[2]
    assert cell.volume == 6.0
    assert cell.vector_arrays == VECTORS


def test_cell_creation_default():
    cell = Cell()
    assert cell.a.value == Cell.__default_vectors__[0]
    assert cell.b.value == Cell.__default_vectors__[1]
    assert cell.c.value == Cell.__default_vectors__[2]
    assert cell.volume == 1.0
    assert cell.vector_arrays == Cell.__default_vectors__


def test_from_vectors_array():
    cell = Cell.from_vectors_array(vectors=VECTORS)
    assert cell.a.value == VECTORS[0]
    assert cell.b.value == VECTORS[1]
    assert cell.c.value == VECTORS[2]
    assert cell.volume == VECTORS_VOLUME
    assert cell.vector_arrays == VECTORS


def test_get_vector_arrays():
    cell = Cell.from_vectors_array(vectors=VECTORS)
    assert cell.get_vector_arrays() == VECTORS
    assert cell.get_vector_arrays(skip_rounding=True) == VECTORS
    assert cell.get_vector_arrays(skip_rounding=False) == VECTORS


def test_vector_arrays_including_rounded(monkeypatch):
    class_reference = Cell
    class_reference.__rounded_vector3d__ = RoundedVector3D

    monkeypatch.setattr(RoundedVector3D, "__round_precision__", 4)
    cell = class_reference.from_vectors_array(vectors=VECTORS_EQUAL_UP_TO_PRECISION_4)
    assert cell.vector_arrays == VECTORS_EQUAL_UP_TO_PRECISION_4
    assert cell.vector_arrays_rounded == VECTORS

    monkeypatch.setattr(RoundedVector3D, "__round_precision__", 5)
    cell = class_reference.from_vectors_array(vectors=VECTORS_EQUAL_UP_TO_PRECISION_4)
    assert cell.vector_arrays == VECTORS_EQUAL_UP_TO_PRECISION_4
    assert cell.vector_arrays_rounded != VECTORS


def test_convert_point_to_cartesian():
    cell = Cell.from_vectors_array(vectors=VECTORS)
    coordinate_in_crystal = [0.5, 0.5, 0.5]
    coordinate_in_cartesian = cell.convert_point_to_cartesian(coordinate_in_crystal)
    expected_coordinate_in_cartesian = [0.5, 1.0, 1.5]
    assert coordinate_in_cartesian == expected_coordinate_in_cartesian


def test_convert_point_to_crystal():
    cell = Cell.from_vectors_array(vectors=VECTORS)
    coordinate_in_cartesian = [0.5, 1.0, 1.5]
    coordinate_in_crystal = cell.convert_point_to_crystal(coordinate_in_cartesian)
    expected_coordinate_in_crystal = [0.5, 0.5, 0.5]
    assert coordinate_in_crystal == expected_coordinate_in_crystal


def test_volume():
    cell = Cell.from_vectors_array(vectors=VECTORS)
    assert cell.volume == VECTORS_VOLUME


def test_volume_rounded(monkeypatch):
    class_reference = Cell
    monkeypatch.setattr(Cell, "__round_precision__", 4)
    cell = class_reference.from_vectors_array(vectors=VECTORS_EQUAL_UP_TO_PRECISION_4)
    assert cell.volume == VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME
    assert cell.volume_rounded == VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4

    monkeypatch.setattr(Cell, "__round_precision__", 5)
    cell = class_reference.from_vectors_array(vectors=VECTORS_EQUAL_UP_TO_PRECISION_4)
    assert cell.volume == VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME
    assert cell.volume_rounded != VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4
    assert cell.volume_rounded == VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_5
