from typing import Any, Optional, Type

from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum
from mat3ra.made.utils import AXIS_TO_INDEX_MAP

from ..... import MaterialWithBuildMetadata
from ....reusable.base_builder import BaseSingleBuilder, TypeConfiguration
from .configuration import VacuumConfiguration


class VacuumBuilder(BaseSingleBuilder):
    _ConfigurationType: Type[VacuumConfiguration] = VacuumConfiguration

    def get_material(
        self,
        configuration: TypeConfiguration,
        post_process_parameters: Optional[Any] = None,
    ) -> Optional[MaterialWithBuildMetadata]:
        if configuration.size == 0.0:
            return None
        return super().get_material(configuration, post_process_parameters)

    def _generate(self, configuration: TypeConfiguration) -> MaterialWithBuildMetadata:
        reference = configuration.crystal
        if reference is None:
            raise ValueError("VacuumConfiguration.crystal must be provided to build a vacuum material.")
        size = configuration.size
        direction: AxisEnum = configuration.direction

        lattice_vectors = reference.lattice.vector_arrays.copy()

        # Replace the target direction with the vacuum vector
        axis = AXIS_TO_INDEX_MAP[direction.value]
        vacuum_vector = [0.0, 0.0, 0.0]
        vacuum_vector[axis] = size
        lattice_vectors[axis] = vacuum_vector

        vacuum_lattice = reference.lattice.from_vectors_array(
            lattice_vectors, reference.lattice.units, reference.lattice.type
        )

        return MaterialWithBuildMetadata.create(
            {
                "name": "Vacuum",
                "lattice": vacuum_lattice.to_dict(),
                "basis": {"elements": [], "coordinates": []},
            }
        )
