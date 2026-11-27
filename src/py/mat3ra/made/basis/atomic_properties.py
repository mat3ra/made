from typing import Any, Dict, List

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.properties_directory.enum_options import ProtoPropertyEnum
from mat3ra.esse.models.properties_directory.structural.basis.atomic_properties import AtomicPropertiesSchema
from pydantic import BaseModel, Field, model_serializer


class AtomicProperty(BaseModel):
    name: ProtoPropertyEnum
    values: ArrayWithIds


class AtomicProperties(AtomicPropertiesSchema):
    """Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name."""

    root: List[AtomicProperty] = Field(default_factory=list)

    @classmethod
    def from_list_of_dicts(cls, list_of_dicts: List[Dict[str, Any]]) -> "AtomicProperties":
        """Builds the properties from the ESSE list of `{name, values}` entries."""
        return cls(
            [
                AtomicProperty(name=item["name"], values=ArrayWithIds.from_list_of_dicts(item["values"]))
                for item in list_of_dicts
            ]
        )

    @property
    def property_by_name(self) -> Dict[ProtoPropertyEnum, ArrayWithIds]:
        return {item.name: item.values for item in self.root}

    def get_by_name(self, name: ProtoPropertyEnum) -> ArrayWithIds:
        """Returns the stored property, storing an empty one first if absent, so that changes made to it are kept."""
        if name not in self.property_by_name:
            self.set_by_name(name, ArrayWithIds.from_values([]))
        return self.property_by_name[name]

    def filter_by_ids(self, ids: List[int], reset_ids: bool = False) -> None:
        """Keeps the items of the given atom ids; with reset_ids each id becomes its index in ids."""
        new_id_by_atom_id = {atom_id: index for index, atom_id in enumerate(ids)}
        for item in self.root:
            item.values.filter_by_ids(ids)
            if reset_ids:
                item.values.ids = [new_id_by_atom_id[atom_id] for atom_id in item.values.ids]

    def add_items_from_another(self, other: "AtomicProperties", id_offset: int) -> None:
        """Adds the items of another one under the same names, with their atom ids shifted by id_offset."""
        for item in other.root:
            values = self.get_by_name(item.name)
            for value, atom_id in zip(item.values.values, item.values.ids):
                values.add_item(value, atom_id + id_offset)

    def set_by_name(self, name: ProtoPropertyEnum, values: ArrayWithIds) -> None:
        property_by_name = {**self.property_by_name, name: values}
        self.root = [AtomicProperty(name=name, values=values) for name, values in property_by_name.items()]

    @model_serializer
    def to_dict(self) -> List[Dict[str, Any]]:
        """Returns the ESSE list; properties with no values are left out."""
        return [
            {"name": name.value, "values": values.to_dict()}
            for name, values in self.property_by_name.items()
            if values.ids
        ]
