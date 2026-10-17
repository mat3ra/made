"""Algorithm knobs of the grain boundary builder: band width, settling tolerance, primitive reduction."""
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilderParameters


class GrainBoundaryLinearBuilderParameters(InterfaceBuilderParameters):
    # the cell holds the periods the grains were cut to
    make_primitive: bool = False
    # a core ring's centre lies in the first row beside its line (< a), its atoms a / sqrt(3) further (< 1.6 a)
    band_width: float = 2.0  # lattice constants
    # converged far below the 1e-9 angstrom to which coordinates are stored
    settling_tolerance: float = 1e-10
