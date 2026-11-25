from typing import Optional

from mat3ra.esse.models.materials_category_components.entities.reusable.two_dimensional.atomic_layers_unique_repeated import (
    AtomicLayersUniqueRepeatedSchema,
)

from ....auxiliary.two_dimensional.termination import Termination
from ..crystal_lattice_planes.configuration import CrystalLatticePlanesConfiguration


class AtomicLayersUniqueRepeatedConfiguration(CrystalLatticePlanesConfiguration, AtomicLayersUniqueRepeatedSchema):
    termination_top: Optional[Termination] = None
    termination_bottom: Optional[Termination] = None
    number_of_repetitions: int
