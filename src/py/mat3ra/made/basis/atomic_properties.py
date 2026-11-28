from functools import cached_property
from typing import Any, Dict, List

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.properties_directory.enum_options import ProtoPropertyEnum
from mat3ra.esse.models.properties_directory.structural.basis.atomic_properties import AtomicPropertiesSchema
from pydantic import BaseModel, Field, model_serializer

ATOMIC_PROPERTY_NAMES = (ProtoPropertyEnum.atomic_constraints, ProtoPropertyEnum.atomic_labels)


class AtomicProperty(BaseModel):
    name: ProtoPropertyEnum
    values: ArrayWithIds


class AtomicProperties(AtomicPropertiesSchema):
    """Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name."""

    root: List[AtomicProperty] = Field(default_factory=lambda: AtomicProperties.from_list_of_dicts([]).root)

    @classmethod
    def from_list_of_dicts(cls, list_of_dicts: List[Dict[str, Any]]) -> "AtomicProperties":
        """Builds one item per known property from the ESSE list of `{name, values}` entries, empty when not given."""
        values_by_name = {ProtoPropertyEnum(item["name"]): item["values"] for item in list_of_dicts}
        return cls(
            [
                AtomicProperty(name=name, values=ArrayWithIds.from_list_of_dicts(values_by_name.get(name, [])))
                for name in ATOMIC_PROPERTY_NAMES
            ]
        )

    @cached_property
    def property_map_by_name(self) -> Dict[ProtoPropertyEnum, AtomicProperty]:
        """The items of `root` by name, built once; they are the same objects as in `root`."""
        return {item.name: item for item in self.root}

    def get_by_name(self, name: ProtoPropertyEnum) -> ArrayWithIds:
        """Returns the stored property, so that changes made to it are kept."""
        return self.property_map_by_name[name].values

    def set_by_name(self, name: ProtoPropertyEnum, values: ArrayWithIds) -> None:
        self.property_map_by_name[name].values = values

    @model_serializer
    def to_dict(self) -> List[Dict[str, Any]]:
        """Returns the ESSE list; properties with no values are left out."""
        return [{"name": item.name.value, "values": item.values.to_dict()} for item in self.root if item.values.values]
