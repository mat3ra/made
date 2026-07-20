import numpy as np
import pytest
from ase.build import add_adsorbate, bulk, fcc111, graphene, surface
from ase.calculators import emt
from mat3ra.made.material import Material
from mat3ra.made.tools.calculate import (
    calculate_adhesion_energy,
    calculate_interfacial_energy,
    calculate_surface_energy,
    calculate_total_energy,
    calculate_total_energy_per_atom,
)
from mat3ra.made.tools.convert import from_ase
from unit.fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE

# Interface and its constituents structures setup
nickel_slab = fcc111("Ni", size=(2, 2, 3), vacuum=10, a=3.52)
graphene_layer = graphene(size=(1, 1, 1), vacuum=10)
graphene_layer.cell = nickel_slab.cell
interface = nickel_slab.copy()
add_adsorbate(interface, graphene_layer, height=2, position="ontop")

# Material objects setup
interface_material = Material.create(GRAPHENE_NICKEL_INTERFACE)
nickel_slab_material = Material.create(from_ase(nickel_slab))
nickel_bulk_material = Material.create(from_ase(bulk("Ni", "fcc", a=3.52)))
graphene_layer_material = Material.create(from_ase(graphene_layer))
graphene_bulk_material = graphene_layer

# Calculator setup
calculator = emt.EMT()


def test_calculate_total_energy():
    atoms = bulk("C", cubic=True)
    calculator = emt.EMT()
    energy = calculate_total_energy(atoms, calculator)
    assert np.isclose(energy, 1.3612647524769237)


def test_calculate_total_energy_per_atom():
    atoms = bulk("C", cubic=True)
    calculator = emt.EMT()
    print(atoms.get_global_number_of_atoms())
    energy_per_atom = calculate_total_energy_per_atom(atoms, calculator)
    assert np.isclose(energy_per_atom, 0.1701580940596)


def test_calculate_surface_energy():
    atoms_slab = surface("C", (1, 1, 1), 3, vacuum=10)
    atoms_bulk = bulk("C", cubic=True)
    calculator = emt.EMT()
    surface_energy = calculate_surface_energy(atoms_slab, atoms_bulk, calculator)
    assert np.isclose(surface_energy, 0.148845)


def test_calculate_adhesion_energy():
    adhesion_energy = calculate_adhesion_energy(interface, nickel_slab, graphene_layer, calculator)
    assert np.isclose(adhesion_energy, 0.07345)


@pytest.mark.skip(reason="This test is not working as expected")
def test_calculate_interfacial_energy():
    interfacial_energy = calculate_interfacial_energy(
        interface_material,
        nickel_slab_material,
        nickel_bulk_material,
        graphene_layer,
        graphene_bulk_material,
        calculator,
    )
    assert np.isclose(
        interfacial_energy,
        -0.78488,
    )
