from typing import List

from mat3ra.code.constants import Tolerance
from mat3ra.made.basis.coordinates import Coordinates

from ...convert import to_pymatgen
from ...third_party import PymatgenVoronoiInterstitialGenerator
from ...utils import get_periodic_distances_to_point, select_index_by_value
from .crystal_site_analyzer import CrystalSiteAnalyzer


class VoronoiCrystalSiteAnalyzer(CrystalSiteAnalyzer):
    """
    Attributes:
       clustering_tol: Tolerance for clustering the Voronoi nodes.
       min_dist: Minimum distance between an interstitial and the nearest atom.
       ltol: Tolerance for lattice matching.
       stol: Tolerance for structure matching.
       angle_tol: Angle tolerance for structure matching.
    """

    clustering_tol: float = 0.5
    min_dist: float = 0.9
    ltol: float = 0.2
    stol: float = 0.3
    angle_tol: float = 5

    @property
    def voronoi_site_coordinate(self) -> List[float]:
        pymatgen_structure = to_pymatgen(self.material)

        voronoi_gen = PymatgenVoronoiInterstitialGenerator(
            clustering_tol=self.clustering_tol,
            min_dist=self.min_dist,
            ltol=self.ltol,
            stol=self.stol,
            angle_tol=self.angle_tol,
        )

        interstitials = list(voronoi_gen.generate(structure=pymatgen_structure, insert_species=["Si"]))

        if not interstitials:
            raise ValueError("No Voronoi interstitial sites found.")

        sites = [site for interstitial in interstitials for site in interstitial.equivalent_sites]
        coordinates = [Coordinates.to_standard_coordinate(site.frac_coords) for site in sites]
        distances = get_periodic_distances_to_point(self.material.lattice.vector_arrays, coordinates, self.coordinate)
        return coordinates[select_index_by_value(distances, Tolerance.lengthAngstrom, coordinates)]
