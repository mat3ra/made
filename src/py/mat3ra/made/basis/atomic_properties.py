from typing import Any, Dict, List

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.properties_directory.enum_options import ProtoPropertyEnum
from pydantic import BaseModel, Field, model_serializer


class AtomicProperties(BaseModel):
    """Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name."""

    arrays_by_name: Dict[ProtoPropertyEnum, ArrayWithIds] = Field(default_factory=dict)

    @classmethod
    def from_list_of_dicts(cls, list_of_dicts: List[Dict[str, Any]]) -> "AtomicProperties":
        """Builds the properties from the ESSE list of `{name, values}` entries."""
        return cls(
            arrays_by_name={
                ProtoPropertyEnum(item["name"]): ArrayWithIds.from_list_of_dicts(item["values"])
                for item in list_of_dicts
            }
        )

    def get_by_name(self, name: ProtoPropertyEnum) -> ArrayWithIds:
        """Returns the stored property, storing an empty one first if absent, so that changes made to it are kept."""
        return self.arrays_by_name.setdefault(name, ArrayWithIds.from_values([]))

    def set_by_name(self, name: ProtoPropertyEnum, values: ArrayWithIds) -> None:
        self.arrays_by_name[name] = values

    @model_serializer
    def to_dict(self) -> List[Dict[str, Any]]:
        """Returns the ESSE list; properties with no values are left out."""
        return [
            {"name": name.value, "values": values.to_dict()}
            for name, values in self.arrays_by_name.items()
            if values.ids
        ]
