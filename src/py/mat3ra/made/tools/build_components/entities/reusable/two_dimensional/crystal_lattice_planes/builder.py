from typing import Any, Optional

from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseSingleBuilder, TypeConfiguration

from ......analyze.lattice_planes import CrystalLatticePlanesMaterialAnalyzer
from ......build_components import MaterialWithBuildMetadata
from ......modify import translate_to_z_level
from ......operations.core.unary import supercell
from .configuration import CrystalLatticePlanesConfiguration


class CrystalLatticePlanesBuilder(BaseSingleBuilder):
    _PostProcessParametersType: Any = None
    use_enforce_convention: bool = True

    def get_analyzer(self, configuration: CrystalLatticePlanesConfiguration) -> CrystalLatticePlanesMaterialAnalyzer:
        return CrystalLatticePlanesMaterialAnalyzer(
            material=configuration.crystal, miller_indices=configuration.miller_indices
        )

    def _generate(self, configuration: CrystalLatticePlanesConfiguration) -> MaterialWithBuildMetadata:
        crystal_lattice_planes_analyzer = self.get_analyzer(configuration)
        miller_supercell_matrix = crystal_lattice_planes_analyzer.miller_supercell_matrix
        crystal = configuration.crystal
        if configuration.use_conventional_cell:
            crystal = crystal_lattice_planes_analyzer.material_with_conventional_lattice
        miller_supercell_material = supercell(crystal, miller_supercell_matrix)
        return miller_supercell_material

    def _enforce_convention(self, material: MaterialWithBuildMetadata) -> MaterialWithBuildMetadata:
        if not self.use_enforce_convention:
            return material
        return translate_to_z_level(material, "bottom")

    def _post_process(
        self,
        item: MaterialWithBuildMetadata,
        post_process_parameters: Optional[Any] = None,
        configuration: Optional[TypeConfiguration] = None,
    ) -> MaterialWithBuildMetadata:
        item = super()._post_process(item, post_process_parameters, configuration)
        return self._enforce_convention(item)
