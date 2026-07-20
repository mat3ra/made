import hashlib
from typing import Any, List, Optional, Union

from mat3ra.code.constants import AtomicCoordinateUnits, Units
from mat3ra.code.entity import HasDescriptionHasMetadataNamedDefaultableInMemoryEntityPydantic
from mat3ra.esse.models.material import MaterialSchema
from pydantic import ConfigDict, SkipValidation, computed_field, field_serializer

from .basis import Basis
from .lattice import Lattice

defaultMaterialConfig = {
    "name": "Silicon FCC",
    "basis": {
        "elements": [
            {
                "id": 0,
                "value": "Si",
            },
            {
                "id": 1,
                "value": "Si",
            },
        ],
        "coordinates": [
            {
                "id": 0,
                "value": [0.0, 0.0, 0.0],
            },
            {
                "id": 1,
                "value": [0.25, 0.25, 0.25],
            },
        ],
        "units": AtomicCoordinateUnits.crystal,
        "labels": [],
        "constraints": [],
    },
    "lattice": {
        "a": 3.867,
        "b": 3.867,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {
            "length": Units.angstrom,
            "angle": Units.degree,
        },
        "type": "FCC",
    },
}


# TODO: replace `-Pydantic` with actual class in the next PR
class Material(MaterialSchema, HasDescriptionHasMetadataNamedDefaultableInMemoryEntityPydantic):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    __default_config__ = defaultMaterialConfig
    __schema__ = MaterialSchema

    basis: Basis
    lattice: Lattice
    # TODO: Fix discriminator in ESSE and remove this:
    derivedProperties: Optional[SkipValidation[object]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.name and self.formula:
            self.name: str = self.formula
        self.basis.cell = self.lattice.vectors

    @classmethod
    def create_from_config_or_class_instance(cls, config_or_instance: Union[dict, "Material"]) -> "Material":
        if isinstance(config_or_instance, cls):
            return config_or_instance
        return cls.create(config_or_instance)

    @property
    def coordinates_array(self) -> List[List[float]]:
        return self.basis.coordinates.values

    def to_cartesian(self) -> None:
        self.basis.to_cartesian()

    def to_crystal(self) -> None:
        self.basis.to_crystal()

    def set_coordinates(self, coordinates: List[List[float]]) -> None:
        self.basis.coordinates.values = coordinates

    def set_lattice_vectors(
        self, lattice_vector1: List[float], lattice_vector2: List[float], lattice_vector3: List[float]
    ) -> None:
        original_is_in_crystal_units = self.basis.is_in_crystal_units
        self.to_cartesian()
        self.lattice = Lattice.from_vectors_array([lattice_vector1, lattice_vector2, lattice_vector3])
        self.basis.cell = self.lattice.vectors
        if original_is_in_crystal_units:
            self.to_crystal()

    def set_lattice_vectors_from_array(self, lattice_vectors: List[List[float]]) -> None:
        if len(lattice_vectors) != 3:
            raise ValueError("Lattice vectors array must contain exactly three vectors.")
        self.set_lattice_vectors(*lattice_vectors)

    def set_lattice(self, lattice: Lattice) -> None:
        self.set_lattice_vectors(*lattice.vector_arrays)

    def add_atom(self, element: str, coordinate: List[float], use_cartesian_coordinates: bool = False) -> None:
        self.basis.add_atom(element, coordinate, use_cartesian_coordinates)

    def set_labels_from_list(self, labels: Optional[List[Union[int, str]]]) -> None:
        self.basis.set_labels_from_list(labels)

    def set_labels_from_value(self, value: Union[int, str]) -> None:
        self.basis.set_labels_from_list([value] * self.basis.number_of_atoms)

    def calculate_hash(self, salt: str = "", is_scaled: bool = False) -> str:
        """Mirrors JS materialMixin.calculateHash(). MD5 of basis + lattice hash strings."""
        message = f"{self.basis.hash_string}#{self.lattice.get_hash_string(is_scaled)}#{salt}"
        return hashlib.md5(message.encode()).hexdigest()

    @computed_field
    @property
    def hash(self) -> str:
        return self.calculate_hash()

    @field_serializer("scaledHash")
    def serialize_scaled_hash(self, _scaled_hash: Optional[str]) -> str:
        return self.scaled_hash

    @property
    def scaled_hash(self) -> str:
        return self.calculate_hash(is_scaled=True)
