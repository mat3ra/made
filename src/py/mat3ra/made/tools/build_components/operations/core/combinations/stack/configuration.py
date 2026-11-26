from typing import Any, List

from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from mat3ra.esse.models.materials_category_components.operations.core.combinations.stack import StackSchema

from .....entities.reusable.base_builder import BaseConfigurationPydantic


class StackConfiguration(StackSchema, BaseConfigurationPydantic):
    type: str = "StackConfiguration"

    stack_components: List[Any]  # Configuration objects only, no Materials
    gaps: ArrayWithIds = ArrayWithIds.from_values([])
    direction: AxisEnum = AxisEnum.z

    def __init__(self, **data):
        gaps = data.get("gaps", [])
        if not isinstance(gaps, ArrayWithIds):
            data["gaps"] = ArrayWithIds.from_values(gaps)
        super().__init__(**data)

    def get_gap_by_id(self, gap_id: int) -> float:
        return self.gaps.get_element_value_by_index(gap_id)
