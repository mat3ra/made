from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseBuilderParameters


class RingNetworkReconstructionBuilderParameters(BaseBuilderParameters):
    # a core ring's centre lies in the first row beside its line (< a), its atoms a / sqrt(3) further (< 1.6 a)
    band_width: float = 2.0  # lattice constants
    # converged far below the precision of stored coordinates (1e-9 of a cell vector, 3e-8 angstrom and more)
    settling_tolerance: float = 1e-10  # angstrom
