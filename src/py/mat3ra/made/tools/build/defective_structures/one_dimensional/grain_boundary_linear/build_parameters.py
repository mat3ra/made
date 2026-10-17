from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilderParameters
from .....build_components.operations.core.modifications.reconstruct import RingNetworkReconstructionBuilderParameters


class GrainBoundaryLinearBuilderParameters(InterfaceBuilderParameters, RingNetworkReconstructionBuilderParameters):
    # the cell holds the periods the grains were cut to
    make_primitive: bool = False
