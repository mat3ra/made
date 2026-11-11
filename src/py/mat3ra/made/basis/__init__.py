from typing import Any, Dict, List, Optional, Union

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.code.constants import HASH_TOLERANCE
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.esse.models.material import BasisSchema, BasisUnitsEnum
from mat3ra.made.basis.coordinates import Coordinates
from mat3ra.made.cell import Cell
from mat3ra.utils.rounding import round_custom
from pydantic import Field
from scipy.spatial import cKDTree

PER_ATOM_FIELDS = ("coordinates", "labels", "magneticMoments", "constraints")


def get_overlapping_coordinates(
    coordinate: List[float],
    coordinates: List[List[float]],
    threshold: float = 0.01,
) -> List[List[float]]:
    """
    Find coordinates that are within a certain threshold of a given coordinate.

    Args:
        coordinate (List[float]): The coordinate.
        coordinates (List[List[float]]): The list of coordinates.
        threshold (float): The threshold for the distance, in the units of the coordinates.

    Returns:
        List[List[float]]: The list of overlapping coordinates.
    """
    return [c for c in coordinates if np.linalg.norm(np.array(c) - np.array(coordinate)) < threshold]


class Basis(BasisSchema, InMemoryEntityPydantic):
    elements: ArrayWithIds
    coordinates: Coordinates
    cell: Cell = Field(Cell(), exclude=True)
    labels: ArrayWithIds = Field(ArrayWithIds.from_values([]))
    constraints: ArrayWithIds = Field(ArrayWithIds.from_values([]))
    magneticMoments: ArrayWithIds = Field(ArrayWithIds.from_values([]))
    DEFAULT_COORDINATE_PROXIMITY_TOLERANCE: float = Field(
        0.1, exclude=True
    )  # Angstroms, used for checking overlapping coordinates

    def __convert_kwargs__(self, **kwargs: Any) -> Dict[str, Any]:
        for field in ("elements", *PER_ATOM_FIELDS):
            if isinstance(kwargs.get(field), list):
                kwargs[field] = type(self).model_fields[field].annotation.from_list_of_dicts(kwargs[field])
        if isinstance(kwargs.get("cell"), list):
            kwargs["cell"] = Cell.from_vectors_array(kwargs["cell"])
        return kwargs

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs = self.__convert_kwargs__(**kwargs)
        super().__init__(*args, **kwargs)

    @property
    def coordinates_as_kdtree(self):
        return cKDTree(np.array(self.coordinates.values))

    def get_coordinates_colliding_pairs(self, tolerance=DEFAULT_COORDINATE_PROXIMITY_TOLERANCE):
        return self.coordinates_as_kdtree.query_pairs(r=tolerance)

    @property
    def number_of_atoms(self) -> int:
        return len(self.elements.values)

    @classmethod
    def from_dict(
        cls,
        elements: List[Dict],
        coordinates: List[Dict],
        units: str,
        cell: List[List[float]],
        labels: Optional[List[Dict]] = ArrayWithIds.from_list_of_dicts([]),
        constraints: Optional[List[Dict]] = ArrayWithIds.from_list_of_dicts([]),
    ) -> "Basis":
        return Basis(
            elements=ArrayWithIds.from_list_of_dicts(elements),
            coordinates=Coordinates.from_list_of_dicts(coordinates),
            units=units,
            cell=Cell.from_vectors_array(cell),
            labels=ArrayWithIds.from_list_of_dicts(labels),
            constraints=ArrayWithIds.from_list_of_dicts(constraints),
        )

    def values_by_atom(self, field: str, default: Any = None) -> List[Any]:
        """Values of a per-atom field in basis order, matched by atom id; atoms without a value get the default."""
        per_atom_values = getattr(self, field)
        value_by_atom_id = dict(zip(per_atom_values.ids, per_atom_values.values))
        return [value_by_atom_id.get(atom_id, default) for atom_id in self.elements.ids]

    @property
    def unique_atomic_species(self) -> List[Dict[str, Any]]:
        """Species per element and magnetic moment, by first appearance: Fe, Fe1, Fe2 (at most 3 characters)."""
        species: List[Dict[str, Any]] = []
        atoms = zip(self.elements.values, self.values_by_atom("magneticMoments", 0))
        for element, magnetic_moment in dict.fromkeys(atoms):
            count = sum(item["element"] == element for item in species)
            name = f"{element}{count}" if count else element
            if len(name) > 3:
                raise ValueError(
                    f"{element} has more than {count} distinct magnetic moments; "
                    "species names are limited to 3 characters"
                )
            species.append({"name": name, "element": element, "magneticMoment": magnetic_moment})
        return species

    @property
    def atomic_species_array(self) -> List[str]:
        """Species name of each atom in basis order, e.g. ["Fe", "Fe1", "O", "O"]."""
        name_by_species = {
            (item["element"], item["magneticMoment"]): item["name"] for item in self.unique_atomic_species
        }
        atoms = zip(self.elements.values, self.values_by_atom("magneticMoments", 0))
        return [name_by_species[atom] for atom in atoms]

    @property
    def hash_string(self) -> str:
        """
        Mirrors JS Basis.hashString (getAsSortedString in crystal units).
        Converts to crystal, takes each coordinate as stored (wrapped into [0, 1), rounded to the coordinates'
        precision), rounds it with round_custom and wraps again, as JS getAsSortedString does, then builds sorted
        atom strings.
        """
        original_is_in_cartesian = self.is_in_cartesian_units
        self.to_crystal()
        parts = []
        for elem, coord in zip(self.elements.to_dict(), self.coordinates.to_dict()):
            stored = self.coordinates.round_array_or_number([value % 1 for value in coord["value"]])
            rounded = [f"{round_custom(value, HASH_TOLERANCE) % 1:g}" for value in stored]
            parts.append(f"{elem['value']} {','.join(rounded)}")
        if original_is_in_cartesian:
            self.to_cartesian()
        return ";".join(sorted(parts)) + ";"

    @property
    def is_in_crystal_units(self):
        return self.units == BasisUnitsEnum.crystal

    @property
    def is_in_cartesian_units(self):
        return self.units == BasisUnitsEnum.cartesian

    def to_cartesian(self):
        if self.is_in_cartesian_units:
            return
        self.coordinates.map_array_in_place(self.cell.convert_point_to_cartesian)
        self.units = BasisUnitsEnum.cartesian

    def to_crystal(self):
        if self.is_in_crystal_units:
            return
        self.coordinates.map_array_in_place(self.cell.convert_point_to_crystal)
        self.units = BasisUnitsEnum.crystal

    def add_atom(
        self,
        element="Si",
        coordinate: Optional[List[float]] = None,
        use_cartesian_coordinates: bool = False,
        force: bool = False,
        label: Optional[Union[int, str]] = None,
    ):
        """
        Add an atom to the basis at a specified coordinate. Check that no other atom is overlapping with it.

        Args:
            element (str): Element symbol of the atom to be added.
            coordinate (List[float]): Coordinate of the atom to be added.
            use_cartesian_coordinates (bool): Whether the coordinate is in Cartesian units (or crystal by default).
            force (bool): Whether to force adding the atom even if it overlaps with another atom.
            label (int|str|None): Per-atom label when the basis already uses labels; omit if the basis has none.
        """
        if coordinate is None:
            coordinate = [0, 0, 0]
        if use_cartesian_coordinates and self.is_in_crystal_units:
            coordinate = self.cell.convert_point_to_crystal(coordinate)
        if not use_cartesian_coordinates and self.is_in_cartesian_units:
            coordinate = self.cell.convert_point_to_cartesian(coordinate)
        cartesian_coordinates_for_overlap_check = [
            self.cell.convert_point_to_cartesian(coord) for coord in self.coordinates.values
        ]
        cartesian_coordinate_for_overlap_check = self.cell.convert_point_to_cartesian(coordinate)
        if get_overlapping_coordinates(
            cartesian_coordinate_for_overlap_check, cartesian_coordinates_for_overlap_check, threshold=0.01
        ):
            if force:
                print(f"Warning: Overlapping coordinates found for {coordinate}. Adding atom anyway.")
            else:
                print(f"Warning: Overlapping coordinates found for {coordinate}. Not adding atom.")
                return
        self.elements.add_item(element)
        self.coordinates.add_item(coordinate)
        if label is not None:
            self.labels.add_item(label, self.elements.ids[-1])

    def add_atoms_from_another_basis(self, other_basis: "Basis"):
        """
        Add atoms from another basis to this basis.

        Args:
            other_basis (Basis): The other basis to add atoms from.
        """

        id_offset = max(self.elements.ids, default=-1) + 1
        for field in ("elements", *PER_ATOM_FIELDS):
            other_values = getattr(other_basis, field)
            for value, atom_id in zip(other_values.values, other_values.ids):
                getattr(self, field).add_item(value, atom_id + id_offset)

    def remove_atom_by_id(self, id: int):
        self.filter_atoms_by_ids(id, invert=True)

    def remove_atoms_by_elements(self, values: Union[List[str], str]) -> "Basis":
        if isinstance(values, str):
            values = [values]
        ids_to_remove = [
            id_ for value in values for id_, v in zip(self.elements.ids, self.elements.values) if v == value
        ]
        self.filter_atoms_by_ids(ids_to_remove, invert=True)
        return self

    def filter_atoms_by_ids(self, ids: Union[List[int], int], invert: bool = False, reset_ids=False) -> "Basis":
        self.elements.filter_by_ids(ids, invert)
        kept_atom_ids = self.elements.ids
        for field in PER_ATOM_FIELDS:
            getattr(self, field).filter_by_ids(kept_atom_ids)
        if reset_ids:
            new_id_by_atom_id = {atom_id: index for index, atom_id in enumerate(kept_atom_ids)}
            for field in ("elements", *PER_ATOM_FIELDS):
                per_atom_values = getattr(self, field)
                per_atom_values.ids = [new_id_by_atom_id[atom_id] for atom_id in per_atom_values.ids]
        return self

    def filter_atoms_by_labels(self, labels: Union[List[str], str]) -> "Basis":
        labels_int = [int(label) if isinstance(label, str) else label for label in labels]
        self.labels.filter_by_values(labels_int)
        return self.filter_atoms_by_ids(self.labels.ids)

    def set_labels_from_list(self, labels: Optional[List[Union[int, str]]]) -> None:
        """
        Set the labels of the basis from a list of labels (i. e. [1,1,1] for a 3-atom basis).
            If None or [] are passed, the labels are removed (set to an empty array).
        """
        num_atoms = len(self.elements.values)

        if labels is None or len(labels) == 0:
            self.labels = ArrayWithIds.from_values([])
            return

        if len(labels) != num_atoms:
            raise ValueError(f"Number of labels ({len(labels)}) must match number of atoms ({num_atoms})")

        self.labels = ArrayWithIds.from_values(values=list(labels))

    def transform_by_matrix(self, matrix: Matrix3x3Schema) -> None:
        original_is_in_crystal_units = self.is_in_crystal_units
        self.to_crystal()
        matrix_np = np.array(matrix)
        new_coordinates = np.dot(self.coordinates.values, matrix_np)
        self.coordinates.values = new_coordinates.tolist()
        if not original_is_in_crystal_units:
            self.to_cartesian()

    # TODO: add/update test for this method
    def resolve_colliding_coordinates(self, tolerance=DEFAULT_COORDINATE_PROXIMITY_TOLERANCE):
        """
        Find all atoms that are within distance tolerance and only keep the last one, remove other sites.

        Args:
            tolerance (float): The distance tolerance in angstroms.
        """
        original_is_in_crystal = self.is_in_crystal_units
        self.to_cartesian()
        ids_to_remove = set()
        atom_ids = self.coordinates.ids
        for index_1, index_2 in self.get_coordinates_colliding_pairs(tolerance):
            ids_to_remove.add(atom_ids[index_1])  # Keep the last one in the pair

        self.filter_atoms_by_ids(list(ids_to_remove), invert=True, reset_ids=True)
        if original_is_in_crystal:
            self.to_crystal()
