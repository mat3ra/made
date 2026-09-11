from enum import Enum
from typing import Dict, List, Optional

import numpy as np
from scipy.spatial import Delaunay

from .. import BaseMaterialAnalyzer


class SurfaceSiteEnum(str, Enum):
    ATOP = "atop"
    BRIDGE = "bridge"
    FCC = "fcc"
    HCP = "hcp"
    HOLLOW = "hollow"


def _tile_periodic_images(points_xy: np.ndarray, vectors_2d: np.ndarray) -> np.ndarray:
    shifts = [i * vectors_2d[0] + j * vectors_2d[1] for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return np.vstack([points_xy + shift for shift in shifts])


def _triangle_edges(corners: np.ndarray) -> List[tuple]:
    a, b, c = corners
    return [(a, b), (b, c), (a, c)]


class SurfaceSiteAnalyzer(BaseMaterialAnalyzer):
    """
    High-symmetry adsorption sites of the top surface of a slab, in cartesian in-plane coordinates.

    Sites are found geometrically from the surface layer alone, so any lattice and Miller index whose
    surface is flat within `layer_tolerance` works. A three-fold hollow is named by the subsurface
    layer beneath it: "hcp" when the second layer's atom lies under it, "fcc" when the third layer's
    does, "hollow" when neither.
    """

    layer_tolerance: float = 0.5
    site_match_tolerance: float = 0.3
    tie_tolerance: float = 0.05

    @property
    def in_plane_vectors(self) -> np.ndarray:
        return np.array(self.material.lattice.vector_arrays)[:2, :2]

    @property
    def layers(self) -> List[np.ndarray]:
        """Cartesian coordinates grouped into layers, top surface first."""
        cartesian = self.material.clone()
        cartesian.to_cartesian()
        coordinates = np.array(cartesian.coordinates_array)
        layers: List[np.ndarray] = []
        for z in sorted(coordinates[:, 2], reverse=True):
            if any(abs(z - layer[0][2]) < self.layer_tolerance for layer in layers):
                continue
            layers.append(coordinates[np.abs(coordinates[:, 2] - z) < self.layer_tolerance])
        return layers

    @property
    def sites(self) -> Dict[str, List[float]]:
        """Site name -> [x, y] in Angstrom; one representative per site type present."""
        layers = self.layers
        surface_xy = layers[0][:, :2]
        tiled = _tile_periodic_images(surface_xy, self.in_plane_vectors)
        triangles = Delaunay(tiled).simplices
        centroids = [tiled[corners].mean(axis=0) for corners in triangles]
        midpoints = [tiled[list(edge)].mean(axis=0) for corners in triangles for edge in _triangle_edges(corners)]
        atop = surface_xy[0]
        sites: Dict[str, List[float]] = {SurfaceSiteEnum.ATOP.value: atop.tolist()}
        for point in sorted(midpoints, key=lambda p: np.linalg.norm(p - atop)):
            sites.setdefault(SurfaceSiteEnum.BRIDGE.value, point.tolist())
        for point in sorted(centroids, key=lambda p: np.linalg.norm(p - atop)):
            sites.setdefault(self._hollow_name(point, layers), point.tolist())
        return sites

    def _hollow_name(self, hollow_xy: np.ndarray, layers: List[np.ndarray]) -> str:
        for name, depth in ((SurfaceSiteEnum.HCP.value, 1), (SurfaceSiteEnum.FCC.value, 2)):
            if depth >= len(layers):
                continue
            images = _tile_periodic_images(layers[depth][:, :2], self.in_plane_vectors)
            if np.linalg.norm(images - hollow_xy, axis=1).min() < self.site_match_tolerance:
                return name
        return SurfaceSiteEnum.HOLLOW.value

    def _distance_to_site(self, coordinate_xy: np.ndarray, site_xy: List[float]) -> float:
        images = _tile_periodic_images(np.array([site_xy]), self.in_plane_vectors)
        return float(np.linalg.norm(images - coordinate_xy, axis=1).min())

    def get_site_name(self, coordinate_xy: List[float]) -> Optional[str]:
        """
        The named site a point sits on, or None when two sites are equally close.

        None rather than a guess: an ambiguous label is how a structure gets reported under the
        wrong registry.
        """
        point = np.array(coordinate_xy[:2])
        distances = {name: self._distance_to_site(point, site) for name, site in self.sites.items()}
        ordered = sorted(distances.values())
        if len(ordered) > 1 and ordered[1] - ordered[0] < self.tie_tolerance:
            return None
        return min(distances, key=lambda name: distances[name])

    def get_displacement_to_site(self, coordinate_xy: List[float], site_name: str) -> List[float]:
        """The in-plane shift, as a 3D vector, that moves a point onto the named site."""
        site = np.array(self.sites[site_name])
        point = np.array(coordinate_xy[:2])
        images = _tile_periodic_images(np.array([site]), self.in_plane_vectors)
        nearest = images[np.argmin(np.linalg.norm(images - point, axis=1))]
        return [float(nearest[0] - point[0]), float(nearest[1] - point[1]), 0.0]
