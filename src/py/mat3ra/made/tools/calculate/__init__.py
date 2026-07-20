from typing import Optional

from ...material import Material
from ..analyze.other import get_surface_area
from ..analyze.interface_material import get_interface_bulk_crystal
from ..build.compound_pristine_structures.two_dimensional.interface import get_slab
from ..build_components.metadata import MaterialWithBuildMetadata
from ..convert import decorator_convert_material_args_kwargs_to_atoms
from ..third_party import ASEAtoms, ASECalculator, ASECalculatorEMT
from .calculators import InterfaceMaterialCalculatorParameters
from .interaction_functions import sum_of_inverse_distances_squared


@decorator_convert_material_args_kwargs_to_atoms
def calculate_total_energy(atoms: ASEAtoms, calculator: ASECalculator):
    """
    Set calculator for ASE Atoms and calculate the total energy.

    Args:
        atoms (ASEAtoms): The Atoms object to calculate the energy of.
        calculator (ase.calculators.calculator.Calculator): The calculator to use for the energy calculation.

    Returns:
        float: The total energy of the atoms.
    """
    atoms.calc = calculator
    return atoms.get_total_energy()


@decorator_convert_material_args_kwargs_to_atoms
def calculate_total_energy_per_atom(atoms: ASEAtoms, calculator: ASECalculator):
    """
    Set calculator for ASE Atoms and calculate the total energy per atom.

    Args:
            atoms (ASEAtoms): The Atoms object to calculate the energy of.
            calculator (ase.calculators.calculator.Calculator): The calculator to use for the energy calculation.

    Returns:
            float: The energy per atom of the atoms.
    """
    return calculate_total_energy(atoms, calculator) / atoms.get_global_number_of_atoms()


@decorator_convert_material_args_kwargs_to_atoms
def calculate_surface_energy(slab: ASEAtoms, bulk: ASEAtoms, calculator: ASECalculator):
    """
    Calculate the surface energy by subtracting the weighted bulk energy from the slab energy.

    Args:
        slab (ASEAtoms): The slab Atoms object to calculate the surface energy of.
        bulk (ASEAtoms): The bulk Atoms object to calculate the surface energy of.
        calculator (ase.calculators.calculator.Calculator): The calculator to use for the energy calculation.

    Returns:
        float: The surface energy of the slab.
    """
    number_of_atoms = slab.get_global_number_of_atoms()
    area = get_surface_area(slab)
    return (
        calculate_total_energy(slab, calculator) - calculate_total_energy_per_atom(bulk, calculator) * number_of_atoms
    ) / (2 * area)


@decorator_convert_material_args_kwargs_to_atoms
def calculate_adhesion_energy(
    interface: ASEAtoms, substrate_slab: ASEAtoms, film_slab: ASEAtoms, calculator: ASECalculator
):
    """
    Calculate the adhesion energy.
    The adhesion energy is the difference between the energy of the interface and
    the sum of the energies of the substrate and film.
    According to: 10.1088/0953-8984/27/30/305004

    Args:
        interface (ASEAtoms): The interface ASEAtoms object to calculate the adhesion energy of.
        substrate_slab (ASEAtoms): The substrate slab ASEAtoms object to calculate the adhesion energy of.
        film_slab (ASEAtoms): The film slab ASEAtoms object to calculate the adhesion energy of.
        calculator (ase.calculators.calculator.Calculator): The calculator to use for the energy calculation.

    Returns:
        float: The adhesion energy of the interface.
    """
    energy_substrate_slab = calculate_total_energy(substrate_slab, calculator)
    energy_film_slab = calculate_total_energy(film_slab, calculator)
    energy_interface = calculate_total_energy(interface, calculator)
    area = get_surface_area(interface)
    return (energy_substrate_slab + energy_film_slab - energy_interface) / area


def calculate_interfacial_energy(
    interface: Material,
    substrate_slab: Optional[Material] = None,
    substrate_bulk: Optional[Material] = None,
    film_slab: Optional[Material] = None,
    film_bulk: Optional[Material] = None,
    calculator: ASECalculator = ASECalculatorEMT(),
):
    """
    Calculate the interfacial energy.
    The interfacial energy is the sum of the surface energies of the substrate and film minus the adhesion energy.
    According to Dupré's formula

    Args:
        interface (Material): The interface Material object to calculate the interfacial energy of.
        substrate_slab (Material): The substrate slab Material object to calculate the interfacial energy of.
        substrate_bulk (Material): The substrate bulk Material object to calculate the interfacial energy of.
        film_slab (Material): The film slab Material object to calculate the interfacial energy of.
        film_bulk (Material): The film bulk Material object to calculate the interfacial energy of.
        calculator (ase.calculators.calculator.Calculator): The calculator to use for the energy calculation

    Returns:
        float: The interfacial energy of the interface.
    """
    substrate_slab = get_slab(interface, part="substrate") if substrate_slab is None else substrate_slab
    film_slab = get_slab(interface, part="film") if film_slab is None else film_slab

    try:
        interface_with_metadata = MaterialWithBuildMetadata.create(interface.to_dict())
        substrate_bulk = Material.create(get_interface_bulk_crystal(interface_with_metadata, part="substrate"))
        film_bulk = Material.create(get_interface_bulk_crystal(interface_with_metadata, part="film"))
    except ValueError as exc:
        raise ValueError(
            "The substrate and film bulk materials must be provided or defined in the interface metadata."
        ) from exc
    surface_energy_substrate = calculate_surface_energy(substrate_slab, substrate_bulk, calculator)
    surface_energy_film = calculate_surface_energy(film_slab, film_bulk, calculator)
    adhesion_energy = calculate_adhesion_energy(interface, substrate_slab, film_slab, calculator)
    return surface_energy_film + surface_energy_substrate - adhesion_energy
