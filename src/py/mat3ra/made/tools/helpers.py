# Analyzers
from .analyze.lattice import get_material_with_conventional_lattice, get_material_with_primitive_lattice

# Defective Structures
from .build.compound_pristine_structures.two_dimensional.heterostructure import create_heterostructure
from .build.compound_pristine_structures.two_dimensional.heterostructure.types import StackComponentDict

# Compound Pristine Structures
from .build.compound_pristine_structures.two_dimensional.interface.base.helpers import (
    create_interface_simple,
    create_interface_simple_between_slabs,
)
from .build.compound_pristine_structures.two_dimensional.interface.commensurate.helpers import (
    create_interface_commensurate,
    get_commensurate_strained_configurations,
)
from .build.compound_pristine_structures.two_dimensional.interface.twisted.helpers import create_interface_twisted
from .build.compound_pristine_structures.two_dimensional.interface.utils import get_optimal_film_displacement
from .build.compound_pristine_structures.two_dimensional.interface.zsl.helpers import (
    create_interface_zsl,
    create_interface_zsl_between_slabs,
)

# Defective Structures
from .build.defective_structures.one_dimensional.grain_boundary_linear.helpers import create_grain_boundary_linear
from .build.defective_structures.two_dimensional.adatom.helpers import (
    create_defect_adatom,
    create_multiple_adatom_defects,
    get_adatom_defect_analyzer_cls,
)
from .build.defective_structures.two_dimensional.adatom.types import AdatomDefectDict
from .build.defective_structures.two_dimensional.grain_boundary_planar.helpers import create_grain_boundary_planar
from .build.defective_structures.two_dimensional.island.helpers import create_defect_island, get_coordinate_condition
from .build.defective_structures.two_dimensional.terrace.helpers import create_defect_terrace
from .build.defective_structures.zero_dimensional.pair_defect.helpers import create_defect_pair
from .build.defective_structures.zero_dimensional.point_defect.helpers import create_multiple_defects
from .build.defective_structures.zero_dimensional.point_defect.interstitial.helpers import (
    create_defect_point_interstitial,
)
from .build.defective_structures.zero_dimensional.point_defect.substitutional.helpers import (
    create_defect_point_substitution,
)
from .build.defective_structures.zero_dimensional.point_defect.types import PointDefectDict
from .build.defective_structures.zero_dimensional.point_defect.vacancy.helpers import create_defect_point_vacancy
from .build.defective_structures.three_dimensional.solid_solution.helpers import create_solid_solution

# Pristine Structures
from .build.pristine_structures.three_dimensional.ideal_crystal.helpers import create_monolayer
from .build.pristine_structures.two_dimensional.nanoribbon.helpers import create_nanoribbon
from .build.pristine_structures.two_dimensional.nanotape.helpers import create_nanotape
from .build.pristine_structures.two_dimensional.slab.helpers import (
    create_slab,
    create_slab_if_not,
    get_slab_material_in_standard_representation,
    get_slab_terminations,
)
from .build.pristine_structures.two_dimensional.slab.termination_utils import select_slab_termination
from .build.pristine_structures.zero_dimensional.nanoparticle.helpers import (
    create_nanoparticle_by_shape,
    create_nanoparticle_by_shape_from_element,
    create_nanoparticle_from_material,
)

# Enums
from .build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum

# Processed Structures
from .build.processed_structures.two_dimensional.passivation.helpers import (
    get_coordination_numbers_distribution,
    get_unique_coordination_numbers,
    passivate_dangling_bonds,
    passivate_surface,
)
from .build_components.entities.reusable.one_dimensional.crystal_lattice_lines.edge_types import EdgeTypesEnum
from .build_components.entities.reusable.one_dimensional.crystal_lattice_lines.helpers import (
    create_lattice_lines_config_and_material,
)

# Build Components (for operations and utilities)
from .build_components.entities.reusable.three_dimensional.supercell.helpers import create_supercell
from .build_components.entities.reusable.two_dimensional.atomic_layers_unique_repeated.helpers import (
    create_atomic_layers,
)
from .build_components.entities.reusable.two_dimensional.slab_stack.helpers import (
    create_slab_stack,
    recreate_slab_with_fractional_layers,
)
from .build_components.operations.core.modifications.perturb.helpers import create_perturbation

# Entities
from .entities.coordinate import CoordinateCondition

__all__ = [
    # Crystal and related analyzer functions
    "get_material_with_primitive_lattice",
    "get_material_with_conventional_lattice",
    # Slab and related Functions
    "create_slab",
    "create_slab_if_not",
    "get_slab_material_in_standard_representation",
    "create_atomic_layers",
    "get_slab_terminations",
    "select_slab_termination",
    "create_supercell",
    "create_monolayer",
    "create_perturbation",
    # heterostructure Functions
    "create_heterostructure",
    "create_lattice_lines_config_and_material",
    # Nanostructure Functions
    "create_nanoparticle_from_material",
    "create_nanoparticle_by_shape",
    "create_nanoparticle_by_shape_from_element",
    "create_nanoribbon",
    "create_nanotape",
    # Point Defect Functions
    "create_defect_point_vacancy",
    "create_defect_point_substitution",
    "create_defect_point_interstitial",
    "create_multiple_defects",
    "create_solid_solution",
    # Surface Defect Functions
    "create_defect_adatom",
    "create_multiple_adatom_defects",
    "get_adatom_defect_analyzer_cls",
    "create_defect_island",
    "get_coordinate_condition",
    "create_defect_terrace",
    # Complex Defect Functions
    "create_defect_pair",
    "create_slab_stack",
    "recreate_slab_with_fractional_layers",
    # Interface Functions
    "create_interface_simple",
    "create_interface_simple_between_slabs",
    "create_interface_zsl",
    "create_interface_zsl_between_slabs",
    "create_interface_commensurate",
    "get_commensurate_strained_configurations",
    "create_interface_twisted",
    # Grain Boundary Functions
    "create_grain_boundary_planar",
    "create_grain_boundary_linear",
    # Passivation Functions
    "passivate_surface",
    "passivate_dangling_bonds",
    "get_unique_coordination_numbers",
    "get_coordination_numbers_distribution",
    # Utility Functions
    "get_optimal_film_displacement",
    # Type Definitions
    "AdatomDefectDict",
    "PointDefectDict",
    "StackComponentDict",
    # Entities
    "CoordinateCondition",
    # Enums
    "EdgeTypesEnum",
    "SurfaceTypesEnum",
]

# Aliases
create_vacancy = create_defect_point_vacancy
create_substitution = create_defect_point_substitution
create_interstitial = create_defect_point_interstitial
create_adatom = create_defect_adatom
create_island = create_defect_island
create_terrace = create_defect_terrace
