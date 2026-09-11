from enum import Enum
from functools import cached_property
from typing import Dict, List, Optional, Union

import numpy as np
from mat3ra.made.material import Material
from pydantic import ConfigDict
from scipy.spatial import Voronoi, cKDTree

from ...build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from ...convert.interface_parts_enum import InterfacePartsEnum
from .. import BaseMaterialAnalyzer
from ..other import get_atom_indices_by_layer

FRACTIONAL_DECIMALS = 4


class SurfaceSiteEnum(str, Enum):
    ATOP = "atop"
    BRIDGE = "bridge"
    FCC = "fcc"
    HCP = "hcp"
    HOLLOW = "hollow"


def _in_plane_periodic_images(points_xy: np.ndarray, vectors_2d: np.ndarray) -> np.ndarray:
    """The 3x3 in-plane periodic images of `points_xy`, home cell included."""
    shifts = [(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return np.vstack([points_xy + i * vectors_2d[0] + j * vectors_2d[1] for i, j in shifts])


class SurfaceSiteAnalyzer(BaseMaterialAnalyzer):
    """
    `sites`: every instance of each named site (atop, bridge, fcc, hcp, hollow) in the home cell, as
    [x, y] in Angstrom. `get_site_name` and `get_displacement_to_site` resolve a point against it.
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
    def _layers_xy(self) -> List[np.ndarray]:
        """In-plane coordinates of each layer, surface layer first."""
        cartesian = self.material.clone()
        cartesian.to_cartesian()
        coordinates = np.array(cartesian.coordinates_array)
        layers = get_atom_indices_by_layer(self.material, self.layer_tolerance)
        ordered = layers if self.surface == SurfaceTypesEnum.BOTTOM else list(reversed(layers))
        return [self._wrap(coordinates[indices][:, :2]) for indices in ordered]

    @cached_property
    def sites(self) -> Dict[str, List[List[float]]]:
        """Site name -> every instance of that site in the cell, as [x, y] in Angstrom."""
        sites = {
            SurfaceSiteEnum.ATOP.value: self._layers_xy[0].tolist(),
            SurfaceSiteEnum.BRIDGE.value: self._bridges().tolist(),
        }
        for name, points in self._hollows().items():
            sites[name] = np.array(points).tolist()
        return sites

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
            return SurfaceSiteEnum.HOLLOW.value
        for name, depth in ((SurfaceSiteEnum.HCP.value, 1), (SurfaceSiteEnum.FCC.value, 2)):
            if (
                depth < len(self._layers_xy)
                and self._distance_to_points(hollow_xy, self._layers_xy[depth]) < self.site_match_tolerance
            ):
                return name
        return SurfaceSiteEnum.HOLLOW.value

    def _distance_to_points(self, coordinate_xy: np.ndarray, points_xy: np.ndarray) -> float:
        """Distance to the nearest periodic image of any of the points."""
        return float(cKDTree(_in_plane_periodic_images(points_xy, self._in_plane_vectors)).query(coordinate_xy)[0])

    def get_site_name(self, coordinate_xy: List[float]) -> Optional[str]:
        """The site a point sits on, within `site_match_tolerance`; None when it is on no site."""
        point = np.array(coordinate_xy[:2], dtype=float)
        distances = {name: self._distance_to_points(point, np.array(points)) for name, points in self.sites.items()}
        nearest = min(distances, key=lambda name: distances[name])
        return nearest if distances[nearest] <= self.site_match_tolerance else None

    def get_displacement_to_site(
        self, coordinate_xy: List[float], site_name: Union[str, SurfaceSiteEnum]
    ) -> List[float]:
        """The in-plane shift, as a 3D vector, that moves a point onto the nearest instance of a site."""
        name = SurfaceSiteEnum(site_name).value
        if name not in self.sites:
            raise ValueError(f"No '{name}' site on this surface; present: {sorted(self.sites)}")
        point = np.array(coordinate_xy[:2], dtype=float)
        images = _in_plane_periodic_images(np.array(self.sites[name]), self._in_plane_vectors)
        nearest = images[np.argmin(np.linalg.norm(images - point, axis=1))]
        return [float(nearest[0] - point[0]), float(nearest[1] - point[1]), 0.0]


def get_film_site_occupation(
    interface: Material, analyzer: Optional[SurfaceSiteAnalyzer] = None
) -> Dict[int, Optional[str]]:
    """
    Which named substrate site each film atom sits on — atom index -> site name, None for no site.
    The default analyzer takes the substrate's top surface.

    Raises:
        ValueError: when the material carries no film-labelled or no substrate-labelled atoms.
    """
    labels = interface.basis.labels.values
    if InterfacePartsEnum.FILM.value not in labels:
        raise ValueError("The material is not an interface — no film labels.")
    if InterfacePartsEnum.SUBSTRATE.value not in labels:
        raise ValueError("The material is not an interface — no substrate labels.")
    if analyzer is None:
        substrate = interface.clone()
        substrate.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
        analyzer = SurfaceSiteAnalyzer(material=substrate)
    cartesian = interface.clone()
    cartesian.to_cartesian()
    xy = np.array(cartesian.coordinates_array)[:, :2]
    return {
        i: analyzer.get_site_name(xy[i]) for i, label in enumerate(labels) if label == InterfacePartsEnum.FILM.value
    }
