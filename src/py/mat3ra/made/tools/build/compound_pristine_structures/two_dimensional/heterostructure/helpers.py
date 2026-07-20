from typing import List

from .types import StackComponentDict
from .utils import (
    apply_gaps_and_stack,
    create_initial_slabs,
    create_strained_films,
    create_strained_substrate,
    find_common_supercell_matrix,
    validate_heterostructure_inputs,
)
from .....analyze import BaseMaterialAnalyzer
from .....build_components import MaterialWithBuildMetadata


def create_heterostructure(
    stack_component_dicts: List[StackComponentDict],
    gaps: List[float],
    vacuum: float = 10.0,
    use_conventional_cell: bool = True,
    optimize_layer_supercells: bool = True,
) -> MaterialWithBuildMetadata:
    """
    Create a heterostructure by stacking multiple slabs, while applying strain to each slab relative to the first slab.
    Args:
        stack_component_dicts: List of stack component configurations
        gaps: List of gaps between adjacent slabs (in Angstroms)
        vacuum: Size of vacuum layer over the last slab (in Angstroms)
        use_conventional_cell: Whether to use conventional cell
        optimize_layer_supercells: Whether to find optimal supercells for strained layers
    Returns:
        Heterostructure material with stacked strained slabs
    """
    validate_heterostructure_inputs(stack_component_dicts, gaps)

    slabs = create_initial_slabs(stack_component_dicts, vacuum, use_conventional_cell)
    common_supercell_matrix = find_common_supercell_matrix(slabs, optimize_layer_supercells)

    strained_substrate = create_strained_substrate(slabs[0], common_supercell_matrix)
    strained_films = create_strained_films(slabs, common_supercell_matrix, optimize_layer_supercells)

    strained_slabs = [strained_substrate] + strained_films
    heterostructure = apply_gaps_and_stack(strained_slabs, gaps)
    heterostructure.name = generate_heterostructure_name(stack_component_dicts)

    return heterostructure


def generate_heterostructure_name(stack_component_dicts: List[StackComponentDict]):
    """Generate a descriptive name for the heterostructure."""

    components = []
    for component in stack_component_dicts:
        analyzer = BaseMaterialAnalyzer(material=component.crystal)
        formula = analyzer.formula
        miller_str = "".join(map(str, component.miller_indices))
        components.append(f"{formula}({miller_str})")

    return f"Heterostructure [{'-'.join(components)}]"
