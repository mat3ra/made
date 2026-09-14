from functools import cached_property
from typing import Dict, List, Optional, Union

import numpy as np
from pydantic import ConfigDict
from scipy.spatial import Voronoi, cKDTree

from ...build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from .. import BaseMaterialAnalyzer
from ..other import get_atom_indices_by_layer
from ..utils import decorator_perform_operation_in_cartesian_coordinates
from .enums import SurfaceSiteTypesEnum

FRACTIONAL_DECIMALS = 4


def _in_plane_periodic_images(points_xy: np.ndarray, vectors_2d: np.ndarray) -> np.ndarray:
    """The 3x3 in-plane periodic images of `points_xy`, home cell included."""
    shifts = [(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return np.vstack([points_xy + i * vectors_2d[0] + j * vectors_2d[1] for i, j in shifts])


class SurfaceSiteAnalyzer(BaseMaterialAnalyzer):
    """
    `sites`: every instance of each named site (atop, bridge, fcc, hcp, hollow) in the home cell, as
    3D crystal coordinates, z taken from the analyzed surface layer's own height. `get_site_name` and
    `get_displacement_to_site` resolve a point against it.
    fcc/hcp need a layer at depth 2 below the surface; otherwise a three-fold hollow is `hollow`.

    Tolerances, in Angstrom: `layer_tolerance` separates layers; `site_match_tolerance` is how close
    a point must be to count as on a site.
    """

    model_config = ConfigDict(frozen=True)

    surface: SurfaceTypesEnum = SurfaceTypesEnum.TOP
    layer_tolerance: float = 0.5
    site_match_tolerance: float = 0.3

    @cached_property
    def _in_plane_vectors(self) -> np.ndarray:
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @cached_property
    @decorator_perform_operation_in_cartesian_coordinates
    def _layers(self) -> List[np.ndarray]:
        """Coordinates of each layer, surface layer first."""
        coordinates = np.array(self.material.coordinates_array)
        layers = get_atom_indices_by_layer(self.material, self.layer_tolerance)
        ordered = layers if self.surface == SurfaceTypesEnum.BOTTOM else list(reversed(layers))
        return [coordinates[indices] for indices in ordered]

    @cached_property
    def _layers_xy(self) -> List[np.ndarray]:
        """In-plane coordinates of each layer, surface layer first, one instance each in the home cell."""
        return [self._wrap(layer[:, :2]) for layer in self._layers]

    @cached_property
    def _surface_z(self) -> float:
        """Cartesian height of the analyzed surface layer."""
        return float(np.mean(self._layers[0][:, 2]))

    @cached_property
    def _sites_xy(self) -> Dict[str, List[List[float]]]:
        """Site name -> every instance of that site in the cell, as [x, y] in Angstrom."""
        sites = {
            SurfaceSiteTypesEnum.ATOP.value: self._layers_xy[0].tolist(),
            SurfaceSiteTypesEnum.BRIDGE.value: self._bridges().tolist(),
        }
        for name, points in self._hollows().items():
            sites[name] = np.array(points).tolist()
        return sites

    @cached_property
    def sites(self) -> Dict[str, List[List[float]]]:
        """Site name -> every instance of that site in the cell, as 3D crystal coordinates."""
        return {name: [self._to_crystal(point) for point in points] for name, points in self._sites_xy.items()}

    def _to_crystal(self, point_xy: List[float]) -> List[float]:
        return self.material.basis.cell.convert_point_to_crystal([point_xy[0], point_xy[1], self._surface_z])

    def _to_cartesian_xy(self, coordinate: List[float], use_cartesian_coordinates: bool) -> np.ndarray:
        point = (
            coordinate if use_cartesian_coordinates else self.material.basis.cell.convert_point_to_cartesian(coordinate)
        )
        return np.array(point[:2], dtype=float)

    def _wrap(self, points_xy: np.ndarray) -> np.ndarray:
        """Points mapped into the home cell, one instance each."""
        fractional = points_xy @ np.linalg.inv(self._in_plane_vectors)
        shift = np.floor(np.round(fractional, FRACTIONAL_DECIMALS))
        wrapped = fractional - shift
        key = np.round(wrapped, FRACTIONAL_DECIMALS) % 1.0
        _, index = np.unique(key, axis=0, return_index=True)
        return wrapped[index] @ self._in_plane_vectors

    @cached_property
    def _surface_voronoi(self) -> Voronoi:
        return Voronoi(_in_plane_periodic_images(self._layers_xy[0], self._in_plane_vectors))

    def _bridges(self) -> np.ndarray:
        """Midpoints of natural-neighbour pairs: atoms whose Voronoi cells share a ridge of real
        length."""
        voronoi = self._surface_voronoi
        midpoints = []
        for (first_atom_index, second_atom_index), ridge in zip(voronoi.ridge_points, voronoi.ridge_vertices):
            degenerate = (
                -1 in ridge or np.linalg.norm(np.diff(voronoi.vertices[ridge], axis=0)) < self.site_match_tolerance
            )
            if degenerate:
                continue
            midpoints.append((voronoi.points[first_atom_index] + voronoi.points[second_atom_index]) / 2)
        return self._wrap(np.array(midpoints))

    def _hollows(self) -> Dict[str, List[np.ndarray]]:
        tiled = self._surface_voronoi.points
        hollows: Dict[str, List[np.ndarray]] = {}
        for vertex in self._wrap(self._surface_voronoi.vertices):
            distances = np.linalg.norm(tiled - vertex, axis=1)
            coordination = int(np.sum(distances < distances.min() + self.site_match_tolerance))
            hollows.setdefault(self._hollow_name(vertex, coordination), []).append(vertex)
        return hollows

    def _hollow_name(self, hollow_xy: np.ndarray, coordination: int) -> str:
        if coordination != 3:
            return SurfaceSiteTypesEnum.HOLLOW.value
        for name, depth in ((SurfaceSiteTypesEnum.HCP.value, 1), (SurfaceSiteTypesEnum.FCC.value, 2)):
            if (
                depth < len(self._layers_xy)
                and self._distance_to_points(hollow_xy, self._layers_xy[depth]) < self.site_match_tolerance
            ):
                return name
        return SurfaceSiteTypesEnum.HOLLOW.value

    def _distance_to_points(self, coordinate_xy: np.ndarray, points_xy: np.ndarray) -> float:
        """Distance to the nearest periodic image of any of the points."""
        return float(cKDTree(_in_plane_periodic_images(points_xy, self._in_plane_vectors)).query(coordinate_xy)[0])

    def get_site_name(self, coordinate: List[float], use_cartesian_coordinates: bool = False) -> Optional[str]:
        """The site a point sits on, within `site_match_tolerance`; None when it is on no site."""
        point = self._to_cartesian_xy(coordinate, use_cartesian_coordinates)
        distances = {name: self._distance_to_points(point, np.array(points)) for name, points in self._sites_xy.items()}
        nearest = min(distances, key=lambda name: distances[name])
        return nearest if distances[nearest] <= self.site_match_tolerance else None

    def get_displacement_to_site(
        self,
        coordinate: List[float],
        site_name: Union[str, SurfaceSiteTypesEnum],
        use_cartesian_coordinates: bool = False,
    ) -> List[float]:
        """The in-plane shift that moves a point onto the nearest instance of a site, in the same units as
        `coordinate`."""
        name = SurfaceSiteTypesEnum(site_name).value
        if name not in self._sites_xy:
            raise ValueError(f"No '{name}' site on this surface; present: {sorted(self._sites_xy)}")
        point = self._to_cartesian_xy(coordinate, use_cartesian_coordinates)
        images = _in_plane_periodic_images(np.array(self._sites_xy[name]), self._in_plane_vectors)
        nearest = images[np.argmin(np.linalg.norm(images - point, axis=1))]
        displacement = [float(nearest[0] - point[0]), float(nearest[1] - point[1]), 0.0]
        if use_cartesian_coordinates:
            return displacement
        return self.material.basis.cell.convert_point_to_crystal(displacement)
