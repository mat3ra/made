"""
Reciprocal lattice class with k-point path and symmetry point utilities.

Extends the base Lattice class with reciprocal-space functionality
for Brillouin zone analysis.
"""

from typing import List, Optional

import numpy as np

from ..lattice import Lattice
from .paths import RECIPROCAL_PATHS
from .symmetry_points import get_symmetry_points


class ReciprocalLattice(Lattice):
    """Lattice with reciprocal-space utilities.

    Provides methods for working with reciprocal lattice vectors,
    high-symmetry points, k-point paths, and k-grid dimensions.
    """

    def cartesian_coordinates(self, point: List[float]) -> List[float]:
        """Convert a point in crystal (fractional) coordinates to Cartesian coordinates.

        The Cartesian coordinates are in units of 2π/a.

        Args:
            point: A 3D point in fractional reciprocal-space coordinates.

        Returns:
            The point in Cartesian coordinates.
        """
        return np.dot(point, self.reciprocal_vectors).tolist()

    @property
    def symmetry_points(self) -> List[dict]:
        """Get the list of high-symmetry points for the current lattice.

        Returns:
            List of dicts with 'point' (str) and 'coordinates' ([float, float, float]).
        """
        return get_symmetry_points(self)

    @property
    def default_kpoint_path(self) -> List[dict]:
        """Get the default path in reciprocal space for the current lattice.

        Looks up the path by extended type first (e.g., 'BCT-1'), falling back
        to the base type (e.g., 'BCT').

        Returns:
            List of dicts with 'point' (str) and 'steps' (int).
        """
        path = RECIPROCAL_PATHS.get(self.type_extended)
        if path is None:
            lattice_type = self.type.value if hasattr(self.type, "value") else str(self.type)
            path = RECIPROCAL_PATHS.get(lattice_type, [])
        return path

    def extract_kpoint_path(self, data_points: Optional[List[List[float]]] = None) -> List[dict]:
        """Find and label high-symmetry points in a list of raw k-point coordinates.

        Scans through the provided data points and identifies any that match
        known symmetry points (within tolerance).

        Args:
            data_points: List of 3D k-point coordinates.

        Returns:
            List of dicts with 'point' (str), 'steps' (int), and
            'coordinates' ([float, float, float]) for each matched symmetry point.
        """
        if data_points is None:
            data_points = []

        kpoint_path: List[dict] = []
        symm_points = self.symmetry_points

        for index, point in enumerate(data_points):
            for sp in symm_points:
                if np.allclose(sp["coordinates"], point, atol=1e-4):
                    kpoint_path.append(
                        {
                            "point": sp["point"],
                            "steps": index,
                            "coordinates": sp["coordinates"],
                        }
                    )
                    break

        return kpoint_path

    def calculate_dimension(self, n_points: int, index: int) -> int:
        """Calculate k-grid dimension for one reciprocal direction.

        Args:
            n_points: Total number of k-points.
            index: Index of the reciprocal vector direction (0, 1, or 2).

        Returns:
            Grid dimension in the specified direction.
        """
        norms = self.reciprocal_vector_norms
        others = [i for i in range(3) if i != index]
        j, k = others[0], others[1]
        n = np.cbrt((n_points * norms[index] ** 2) / (norms[j] * norms[k]))
        return max(1, int(np.ceil(n)))

    def get_dimensions_from_points_count(self, n_kpoints: int) -> List[int]:
        """Calculate 3D grid dimensions from total number of k-points.

        Args:
            n_kpoints: Total number of k-points.

        Returns:
            List of three grid dimensions [n1, n2, n3].
        """
        return [self.calculate_dimension(n_kpoints, i) for i in range(3)]

    def get_dimensions_from_spacing(self, spacing: float) -> List[int]:
        """Calculate grid dimensions from k-point spacing.

        The spacing is in Cartesian (2π/a) units.

        Args:
            spacing: Maximum spacing between k-points.

        Returns:
            List of three grid dimensions [n1, n2, n3].
        """
        norms = self.reciprocal_vector_norms
        return [max(1, int(np.ceil(round(norm / spacing, 4)))) for norm in norms]

    def get_spacing_from_dimensions(self, dimensions: List[int]) -> float:
        """Calculate average k-point spacing from grid dimensions.

        Args:
            dimensions: List of three grid dimensions [n1, n2, n3].

        Returns:
            Average spacing in Cartesian (2π/a) units.
        """
        norms = self.reciprocal_vector_norms
        spacings = [norms[i] / max(1, dimensions[i]) for i in range(3)]
        return float(np.mean(spacings))
