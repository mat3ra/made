from typing import Optional

from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilderParameters


class GrainBoundaryLinearBuilderParameters(InterfaceBuilderParameters):
    max_supercell_matrix_int: Optional[int] = None
    angle_tolerance: float = 0.1
    return_first_match: bool = False
    edge_inclusion_tolerance: float = 1.0
    distance_tolerance: float = 1.0
