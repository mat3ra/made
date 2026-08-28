from typing import Any, Optional, Type, Union

import numpy as np

from mat3ra.made.material import Material
from mat3ra.made.tools.build_components import MaterialWithBuildMetadata, TypeConfiguration
from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseSingleBuilder
from mat3ra.made.tools.build_components.entities.reusable.one_dimensional.crystal_lattice_lines.edge_types import (
    get_edge_type_from_miller_indices,
)
from ...two_dimensional.nanoribbon.builders import NanoribbonBuilder, NanoribbonBuilderParameters
from .build_parameters import NanotubeBuilderParameters
from .configuration import NanotubeConfiguration


class NanotubeBuilder(BaseSingleBuilder):
    """
    Builder for single-walled nanotubes.

    Creates a nanotube by first building a nanoribbon and then applying a cylindrical
    folding transformation: the y-direction (width) of the nanoribbon is rolled into a
    circle to form the tube wall, while the x-direction (length) becomes the tube axis.
    """

    _ConfigurationType: Type[NanotubeConfiguration] = NanotubeConfiguration
    _GeneratedItemType: Type[Material] = Material
    _BuildParametersType: Type[NanotubeBuilderParameters] = NanotubeBuilderParameters
    _DefaultBuildParameters: NanotubeBuilderParameters = NanotubeBuilderParameters()

    def _generate(self, configuration: NanotubeConfiguration) -> MaterialWithBuildMetadata:
        nanoribbon_builder = NanoribbonBuilder(
            build_parameters=NanoribbonBuilderParameters(use_rectangular_lattice=True)
        )
        return nanoribbon_builder.get_material(configuration.nanoribbon)

    def _post_process(
        self,
        item: Union[Material, MaterialWithBuildMetadata],
        post_process_parameters: Optional[Any] = None,
        configuration: Optional[TypeConfiguration] = None,
    ) -> MaterialWithBuildMetadata:
        vacuum_around_tube = configuration.vacuum_around_tube if configuration is not None else 10.0
        return self._fold_to_nanotube(item, vacuum_around_tube)

    def _fold_to_nanotube(
        self, material: Union[Material, MaterialWithBuildMetadata], vacuum_around_tube: float = 10.0
    ) -> MaterialWithBuildMetadata:
        """
        Fold a nanoribbon into a nanotube by applying a cylindrical coordinate transformation.

        The nanoribbon width (y Cartesian direction) maps to the circumference of the nanotube.
        The nanoribbon length (x Cartesian direction) becomes the tube axis (a lattice vector).
        The 2D material's out-of-plane direction (z) shifts the effective radius for each atom,
        allowing correct handling of finite-thickness layered structures.

        Args:
            material: Nanoribbon material to fold.
            vacuum_around_tube: Vacuum region (in Angstroms) around the tube cross-section.

        Returns:
            MaterialWithBuildMetadata: The folded nanotube material.
        """
        new_material = material.clone()
        new_material.to_cartesian()
        coords = np.array(new_material.basis.coordinates.values)

        y_min = coords[:, 1].min()
        y_max = coords[:, 1].max()
        circumference = y_max - y_min

        if circumference < 1e-6:
            raise ValueError(
                "Nanoribbon width is too small to roll into a nanotube. "
                "Increase the nanoribbon width parameter."
            )

        radius = circumference / (2 * np.pi)

        # Compute the center of the 2D sheet in z (handles finite-thickness structures)
        z_center = (coords[:, 2].min() + coords[:, 2].max()) / 2.0

        # New cross-sectional cell size: diameter + vacuum
        cross_section_size = 2 * radius + vacuum_around_tube

        new_coords = np.empty_like(coords)
        for i, (x, y, z) in enumerate(coords):
            theta = 2 * np.pi * (y - y_min) / circumference
            effective_radius = radius + (z - z_center)
            new_coords[i, 0] = x
            new_coords[i, 1] = effective_radius * np.cos(theta) + cross_section_size / 2.0
            new_coords[i, 2] = effective_radius * np.sin(theta) + cross_section_size / 2.0

        old_vectors = new_material.lattice.vector_arrays
        new_material.set_lattice_vectors(
            [old_vectors[0][0], 0.0, 0.0],
            [0.0, cross_section_size, 0.0],
            [0.0, 0.0, cross_section_size],
        )
        new_material.set_coordinates(new_coords.tolist())
        new_material.to_crystal()
        return MaterialWithBuildMetadata.create(new_material)

    def _update_material_name(
        self, material: Union[Material, MaterialWithBuildMetadata], configuration: Any
    ) -> MaterialWithBuildMetadata:
        if isinstance(configuration, NanotubeConfiguration):
            nanotape = configuration.nanoribbon.nanotape
            lattice_lines = nanotape.lattice_lines
            crystal_name = lattice_lines.crystal.name
            miller_indices = lattice_lines.miller_indices_2d
            edge_type = get_edge_type_from_miller_indices(miller_indices)
            miller_str = f"{miller_indices[0]}{miller_indices[1]}"
            material.name = f"{crystal_name} - {edge_type} Nanotube ({miller_str})"
        return material
