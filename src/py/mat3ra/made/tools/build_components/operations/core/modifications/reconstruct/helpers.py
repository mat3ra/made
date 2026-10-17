from typing import List, Optional, Union

from mat3ra.made.material import Material

from ..... import MaterialWithBuildMetadata
from .build_parameters import RingNetworkReconstructionBuilderParameters
from .builder import RingNetworkReconstructionBuilder
from .configuration import RingNetworkReconstructionConfiguration


def create_ring_network_reconstruction(
    material: Union[Material, MaterialWithBuildMetadata],
    supercell_matrices: List[List[List[int]]],
    build_parameters: Optional[RingNetworkReconstructionBuilderParameters] = None,
) -> MaterialWithBuildMetadata:
    """
    Rebuilds the band along each line of two grains stacked along x as their ring network.

    Args:
        material (Union[Material, MaterialWithBuildMetadata]): Two honeycomb grains stacked along x without a gap,
            labelled 0 and 1.
        supercell_matrices (List[List[List[int]]]): Supercell matrix of each grain.
        build_parameters (Optional[RingNetworkReconstructionBuilderParameters]): Band width and settling tolerance.

    Returns:
        MaterialWithBuildMetadata: The grains with both bands rebuilt and settled.
    """
    configuration = RingNetworkReconstructionConfiguration(material=material, supercell_matrices=supercell_matrices)
    return RingNetworkReconstructionBuilder(build_parameters=build_parameters).get_material(configuration)
