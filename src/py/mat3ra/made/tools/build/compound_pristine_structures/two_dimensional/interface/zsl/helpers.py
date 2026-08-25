from typing import List, Optional, Tuple, Union

from mat3ra.code.array_with_ids import ArrayWithIds

from mat3ra.made.material import Material
from ......analyze.interface import ZSLInterfaceAnalyzer
from ......analyze.slab import SlabMaterialAnalyzer
from ......build.compound_pristine_structures.two_dimensional.interface import (
    InterfaceBuilderParameters,
    InterfaceBuilder,
    InterfaceConfiguration,
)
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab.helpers import create_slab
from ......build_components import MaterialWithBuildMetadata
from ......build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration


def create_interface_zsl(
    substrate_crystal: Union[Material, MaterialWithBuildMetadata],
    film_crystal: Union[Material, MaterialWithBuildMetadata],
    substrate_miller_indices: Tuple[int, int, int] = (0, 0, 1),
    film_miller_indices: Tuple[int, int, int] = (0, 0, 1),
    substrate_number_of_layers: int = 1,
    film_number_of_layers: int = 1,
    substrate_termination_formula: Optional[str] = None,
    film_termination_formula: Optional[str] = None,
    gap: Optional[float] = None,
    vacuum: float = 10.0,
    xy_shift: List[float] = [0, 0],
    max_area: float = 50.0,
    match_id: int = 0,
    max_area_ratio_tol: float = 0.09,
    max_length_tol: float = 0.03,
    max_angle_tol: float = 0.01,
    use_conventional_cell: bool = True,
    reduce_result_cell: bool = True,
    reduce_result_cell_to_primitive: bool = False,
) -> MaterialWithBuildMetadata:
    substrate_slab = create_slab(
        crystal=substrate_crystal,
        miller_indices=substrate_miller_indices,
        number_of_layers=substrate_number_of_layers,
        vacuum=0,
        termination_bottom_formula=substrate_termination_formula,
        use_conventional_cell=use_conventional_cell,
    )
    film_slab = create_slab(
        crystal=film_crystal,
        miller_indices=film_miller_indices,
        number_of_layers=film_number_of_layers,
        vacuum=0,
        termination_top_formula=film_termination_formula,
        use_conventional_cell=use_conventional_cell,
    )

    return create_interface_zsl_between_slabs(
        substrate_slab=substrate_slab,
        film_slab=film_slab,
        gap=gap,
        vacuum=vacuum,
        xy_shift=xy_shift,
        max_area=max_area,
        max_area_ratio_tol=max_area_ratio_tol,
        max_length_tol=max_length_tol,
        max_angle_tol=max_angle_tol,
        match_id=match_id,
        reduce_result_cell=reduce_result_cell,
        reduce_result_cell_to_primitive=reduce_result_cell_to_primitive,
    )


def create_interface_zsl_between_slabs(
    substrate_slab: MaterialWithBuildMetadata,
    film_slab: MaterialWithBuildMetadata,
    gap: Optional[float] = None,
    vacuum: float = 10.0,
    xy_shift: Optional[List[float]] = None,
    max_area: float = 200.0,
    max_area_ratio_tol: float = 0.1,
    max_length_tol: float = 0.03,
    max_angle_tol: float = 0.01,
    match_id: int = 0,
    reduce_result_cell: bool = True,
    reduce_result_cell_to_primitive: bool = False,
) -> MaterialWithBuildMetadata:
    if xy_shift is None:
        xy_shift = [0, 0]

    substrate_slab_config = SlabMaterialAnalyzer(material=substrate_slab).build_configuration
    film_slab_config = SlabMaterialAnalyzer(material=film_slab).build_configuration

    analyzer = ZSLInterfaceAnalyzer(
        substrate_slab_configuration=substrate_slab_config,
        film_slab_configuration=film_slab_config,
        max_area=max_area,
        max_area_ratio_tol=max_area_ratio_tol,
        max_length_tol=max_length_tol,
        max_angle_tol=max_angle_tol,
        reduce_result_cell=reduce_result_cell,
    )

    interface_configurations = analyzer.get_strained_configurations()
    if not interface_configurations:
        raise ValueError("No ZSL match found for the given parameters.")

    if match_id >= len(interface_configurations):
        raise IndexError(f"match_id {match_id} is out of bounds for {len(interface_configurations)} matches found.")

    selected_config = interface_configurations[match_id]

    vacuum_configuration = VacuumConfiguration(size=vacuum)
    stack_components = [
        selected_config.substrate_configuration,
        selected_config.film_configuration,
        vacuum_configuration,
    ]

    interface_config = InterfaceConfiguration(
        stack_components=stack_components, gaps=ArrayWithIds.from_values([gap, gap]), xy_shift=xy_shift
    )
    builder = InterfaceBuilder(
        build_parameters=InterfaceBuilderParameters(make_primitive=reduce_result_cell_to_primitive)
    )
    return builder.get_material(interface_config)
