from ase import Atoms as ASEAtoms
from ase.build import add_vacuum as ase_add_vacuum
from ase.build.supercells import make_supercell as ase_make_supercell
from ase.calculators.calculator import Calculator as ASECalculator
from ase.calculators.calculator import all_changes as ase_all_changes
from ase.calculators.emt import EMT as ASECalculatorEMT
from ase.cluster import BodyCenteredCubic as ASEBodyCenteredCubic
from ase.cluster import Decahedron as ASEDecahedron
from ase.cluster import FaceCenteredCubic as ASEFaceCenteredCubic
from ase.cluster import HexagonalClosedPacked as ASEHexagonalClosedPacked
from ase.cluster import Icosahedron as ASEIcosahedron
from ase.cluster import Octahedron as ASEOctahedron
from ase.cluster import SimpleCubic as ASESimpleCubic
from ase.cluster.wulff import wulff_construction as ASEWulffConstruction
from ase.constraints import FixAtoms as ASEFixAtoms
from ase.constraints import FixedPlane as ASEFixedPlane
from pymatgen.analysis.defects.core import Interstitial as PymatgenInterstitial
from pymatgen.analysis.defects.core import Substitution as PymatgenSubstitution
from pymatgen.analysis.defects.core import Vacancy as PymatgenVacancy
from pymatgen.analysis.defects.generators import VoronoiInterstitialGenerator as PymatgenVoronoiInterstitialGenerator
from pymatgen.analysis.local_env import VoronoiNN as PymatgenVoronoiNN
from pymatgen.core import IStructure as PymatgenIStructure
from pymatgen.core import PeriodicSite as PymatgenPeriodicSite
from pymatgen.core.interface import Interface as PymatgenInterface
from pymatgen.core.interface import label_termination as label_pymatgen_slab_termination
from pymatgen.core.structure import Lattice as PymatgenLattice
from pymatgen.core.structure import Structure as PymatgenStructure
from pymatgen.core.surface import Slab as PymatgenSlab
from pymatgen.core.surface import SlabGenerator as PymatgenSlabGenerator
from pymatgen.io.ase import AseAtomsAdaptor as PymatgenAseAtomsAdaptor
from pymatgen.io.vasp.inputs import Poscar as PymatgenPoscar
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer as PymatgenSpacegroupAnalyzer

# Re-exported imports to allow for both use in type hints and instantiation

__all__ = [
    "ASEAtoms",
    "ASECalculator",
    "ASECalculatorEMT",
    "ASEFixAtoms",
    "ASEFixedPlane",
    "ase_all_changes",
    "PymatgenLattice",
    "PymatgenStructure",
    "PymatgenIStructure",
    "PymatgenSlab",
    "PymatgenSlabGenerator",
    "PymatgenInterface",
    "PymatgenPeriodicSite",
    "PymatgenSpacegroupAnalyzer",
    "PymatgenVacancy",
    "PymatgenSubstitution",
    "PymatgenInterstitial",
    "PymatgenVoronoiInterstitialGenerator",
    "label_pymatgen_slab_termination",
    "ase_make_supercell",
    "ase_add_vacuum",
    "PymatgenAseAtomsAdaptor",
    "PymatgenPoscar",
    "PymatgenVoronoiNN",
    "ASESimpleCubic",
    "ASEBodyCenteredCubic",
    "ASEFaceCenteredCubic",
    "ASEIcosahedron",
    "ASEOctahedron",
    "ASEDecahedron",
    "ASEHexagonalClosedPacked",
    "ASEWulffConstruction",
]
