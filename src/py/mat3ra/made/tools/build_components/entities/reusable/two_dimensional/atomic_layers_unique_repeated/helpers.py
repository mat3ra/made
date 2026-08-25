from typing import Optional, Tuple, Union

from mat3ra.made.material import Material

from ..... import MaterialWithBuildMetadata
from ....auxiliary.two_dimensional.termination import Termination
from .. import AtomicLayersUniqueRepeatedBuilder, AtomicLayersUniqueRepeatedConfiguration


def create_atomic_layers(
    material: Union[Material, MaterialWithBuildMetadata],
    miller_indices: Tuple[int, int, int] = (0, 0, 1),
    termination: Optional[Termination] = None,
    number_of_layers: int = 1,
) -> Material:
    """
    Creates a material composed of repeated unique atomic layers from a given crystal.

    This function identifies the sequence of unique atomic layers for the given Miller
    indices and then constructs the material by repeating this sequence, starting
    with a given surface termination.

    Args:
        material (Material): The crystal material to create atomic layers from.
        miller_indices (Tuple[int, int, int]): Miller indices for the atomic layers.
        termination (Termination): The termination to use for the atomic layers.
        number_of_layers (int): Number of times to repeat the sequence of unique atomic layers.
    Returns:
        Material: The atomic layers material.

    """
    atomic_layers_config = AtomicLayersUniqueRepeatedConfiguration(
        crystal=material,
        miller_indices=miller_indices,
        # Explicit: the schema defaults this True, and this path has never conventionalized.
        use_conventional_cell=False,
        termination_top=termination,
        number_of_repetitions=number_of_layers,
    )

    atomic_layers_builder = AtomicLayersUniqueRepeatedBuilder()
    atomic_layers_material = atomic_layers_builder.get_material(atomic_layers_config)

    return atomic_layers_material
