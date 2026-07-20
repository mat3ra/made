from functools import cached_property
from typing import List, Tuple, Union

from mat3ra.code.vector import Vector3D
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema
from mat3ra.made.material import Material

from ..build_components.metadata import MaterialWithBuildMetadata
from ..convert import from_pymatgen, to_pymatgen
from ..entities import MillerIndices, Termination, TerminationHolder
from ..third_party import PymatgenSlab, PymatgenSlabGenerator, label_pymatgen_slab_termination
from .lattice import LatticeMaterialAnalyzer


def select_slab_with_termination_by_formula(slabs: List[PymatgenSlab], termination: Termination) -> PymatgenSlab:
    for slab in slabs:
        if Termination.from_string(label_pymatgen_slab_termination(slab)).formula == termination.formula:
            return slab
    raise ValueError(f"No slab found with termination: {termination}")


class CrystalLatticePlanesMaterialAnalyzer(LatticeMaterialAnalyzer):
    # Values used to generate slabs with terminations, these values are set to allow for all terminations to be found.
    # Heuristic showed that these values are sufficient for all slabs configurations.
    DEFAULT_THICKNESS_FOR_TERMINATIONS: int = 3
    DEFAULT_VACUUM_SIZE_FOR_TERMINATIONS: int = 1
    # Values used to generate slabs for later use. A single layer thickness and no vacuum.
    DEFAULT_THICKNESS_FOR_GENERATION: int = 1
    DEFAULT_VACUUM_SIZE_FOR_GENERATION: int = 0
    DEFAULT_SYMMETRIZE: bool = False
    miller_indices: Union[List[int], Tuple[int, int, int]]

    def get_pymatgen_slab_generator(
        self,
        min_slab_size: float = DEFAULT_VACUUM_SIZE_FOR_GENERATION,
        min_vacuum_size: float = DEFAULT_VACUUM_SIZE_FOR_GENERATION,
        in_unit_planes: bool = True,
        make_primitive: bool = False,
    ):
        return PymatgenSlabGenerator(
            initial_structure=to_pymatgen(self.material_with_conventional_lattice),
            miller_index=MillerIndices(root=self.miller_indices).to_tuple(),
            min_slab_size=min_slab_size,
            min_vacuum_size=min_vacuum_size,
            in_unit_planes=in_unit_planes,
            primitive=make_primitive,
        )

    @cached_property
    def pymatgen_slab_generator_with_vacuum(self) -> PymatgenSlabGenerator:
        # This generator is used to create slabs with vacuum and thick enough to allow for all terminations to be found.
        return self.get_pymatgen_slab_generator(
            min_slab_size=self.DEFAULT_THICKNESS_FOR_TERMINATIONS,
            min_vacuum_size=self.DEFAULT_VACUUM_SIZE_FOR_TERMINATIONS,
        )

    @cached_property
    def pymatgen_slab_generator_without_vacuum(self) -> PymatgenSlabGenerator:
        # This generator is used to create slabs without vacuum and with a single layer thickness.
        return self.get_pymatgen_slab_generator(
            min_slab_size=self.DEFAULT_THICKNESS_FOR_GENERATION, min_vacuum_size=self.DEFAULT_VACUUM_SIZE_FOR_GENERATION
        )

    @cached_property
    def all_planes_as_pymatgen_slabs_with_vacuum(self) -> List[PymatgenSlab]:
        return [
            *self.pymatgen_slab_generator_with_vacuum.get_slabs(symmetrize=True),
            # Leaving option to create a non-symmetrized slabs too for additional terminations.
            # As of now, looks like symmetrize=True gives all the unique terminations needed.
            # *self.pymatgen_slab_generator_with_vacuum.get_slabs(symmetrize=False),
        ]

    @cached_property
    def all_planes_as_pymatgen_slabs_without_vacuum(self) -> List[PymatgenSlab]:
        return [
            *self.pymatgen_slab_generator_without_vacuum.get_slabs(symmetrize=self.DEFAULT_SYMMETRIZE),
            # Leaving option to create symmetrized slabs for layers generation.
            # *self.pymatgen_slab_generator_without_vacuum.get_slabs(symmetrize=not self.DEFAULT_SYMMETRIZE),
        ]

    def _create_fallback_termination_for_failed_slab_generation(self) -> TerminationHolder:
        """
        Creates a fallback termination when pymatgen's SlabGenerator fails to generate slabs.

        This happens for certain materials where SlabGenerator removes "too many sites"
        and returns empty slab lists (e.g., some nanoribbons, thin 2D materials).

        Returns:
             TerminationHolder: A basic termination using the material's chemical formula
        """
        formula = self.formula
        fallback_termination = Termination(chemical_elements=formula, space_group_symmetry_label="")

        return TerminationHolder(
            termination_with_vacuum=fallback_termination,
            termination_without_vacuum=fallback_termination,
            shift_with_vacuum=0.0,
            shift_without_vacuum=0.0,
        )

    @cached_property
    def termination_holders(self):
        termination_holders = []
        slabs_with_vacuum = self.all_planes_as_pymatgen_slabs_with_vacuum
        slabs_without_vacuum = self.all_planes_as_pymatgen_slabs_without_vacuum

        # Handle case where pymatgen fails to generate slabs for certain materials
        # (e.g., some nanoribbons where "Too many sites removed" by SlabGenerator)
        if not slabs_with_vacuum:
            fallback_holder = self._create_fallback_termination_for_failed_slab_generation()
            termination_holders.append(fallback_holder)

        for slab_with_vacuum in slabs_with_vacuum:
            termination_with_vacuum_string = label_pymatgen_slab_termination(slab_with_vacuum)
            termination_with_vacuum = Termination.from_string(termination_with_vacuum_string)

            try:
                matching_slab_without_vacuum = select_slab_with_termination_by_formula(
                    slabs_without_vacuum, termination_with_vacuum
                )
                termination_without_vacuum_string = label_pymatgen_slab_termination(matching_slab_without_vacuum)
                termination_without_vacuum = Termination.from_string(termination_without_vacuum_string)
                shift_without_vacuum = matching_slab_without_vacuum.shift
            except ValueError:
                termination_without_vacuum = None
                shift_without_vacuum = 0.0
            shift_with_vacuum = slab_with_vacuum.shift

            termination_holders.append(
                TerminationHolder(
                    termination_with_vacuum=termination_with_vacuum,
                    termination_without_vacuum=termination_without_vacuum,
                    shift_with_vacuum=shift_with_vacuum,
                    shift_without_vacuum=shift_without_vacuum,
                )
            )

        return termination_holders

    @cached_property
    def terminations_with_vacuum(self) -> List[Termination]:
        return [holder.termination_with_vacuum for holder in self.termination_holders]

    @cached_property
    def terminations_without_vacuum(self) -> List[Termination]:
        return [holder.termination_without_vacuum for holder in self.termination_holders]

    @cached_property
    def terminations(self):
        return self.terminations_with_vacuum

    @property
    def default_termination(self) -> Termination:
        return self.terminations[0]

    @property
    def miller_supercell_matrix(self) -> Matrix3x3Schema:
        return self.pymatgen_slab_generator_without_vacuum.slab_scale_factor.tolist()

    def get_material_name_for_termination(self, termination: Termination) -> str:
        # for example: "Si(001), termination Si_P4/mmm_1, Slab"
        return f"{self.material.formula}({self.miller_indices}), termination {termination}, Slab"

    def get_material_with_termination_without_vacuum(self, termination: Termination) -> Material:
        # Note: termination is passed with vacuum, but we return the material without vacuum
        holder = next((h for h in self.termination_holders if h.termination_with_vacuum == termination), None)
        if holder is None:
            raise ValueError(f"Termination {termination} not found.")

        slabs_without_vacuum = self.all_planes_as_pymatgen_slabs_without_vacuum
        slab = select_slab_with_termination_by_formula(slabs_without_vacuum, termination)
        material = MaterialWithBuildMetadata.create(from_pymatgen(slab))
        material.name = self.get_material_name_for_termination(termination)
        return material

    def get_translation_vector_for_termination_without_vacuum(self, termination: Termination) -> Vector3D:
        holder = next((h for h in self.termination_holders if h.termination_with_vacuum == termination), None)
        if holder is None:
            raise ValueError(f"Termination {termination} not found.")

        # NOTE: pymatgen shift values are in fractional crystal coordinates and need to be negated
        # Convert from crystal to cartesian coordinates using the conventional lattice
        crystal_shift = [0.0, 0.0, -holder.shift_without_vacuum]
        cartesian_shift = self.material_with_conventional_lattice.basis.cell.convert_point_to_cartesian(crystal_shift)
        return cartesian_shift

    def get_materials_for_all_terminations_without_vacuum(self) -> List[Material]:
        return [
            self.get_material_with_termination_without_vacuum(holder.termination_with_vacuum)
            for holder in self.termination_holders
            if holder.termination_without_vacuum is not None
        ]
