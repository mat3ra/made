from typing import Optional, Union

import sympy as sp
from mat3ra.made.material import Material

from ..... import MaterialWithBuildMetadata
from .builders.base import PerturbationBuilder
from .builders.isometric import IsometricPerturbationBuilder
from .configuration import PerturbationConfiguration
from .functions import PerturbationFunctionHolder
from .functions.maxwell_boltzmann import MaxwellBoltzmannDisplacementHolder


def create_perturbation(
    material: Union[Material, MaterialWithBuildMetadata],
    perturbation_function: Union[sp.Expr, str],
    use_cartesian_coordinates: bool = True,
    is_isometric: bool = False,
):
    """
    Create a perturbation for a material.
    With a function of delta for coordinate [∆x, ∆y, ∆z] = f(x, y, z) applied to each atom in the material.

    Args:
        material (Material): The material to be perturbed.
        perturbation_function (PerturbationFunctionHolder): The perturbation function to apply.
        is_isometric (bool): If True, the lattice will be adjusted to preserve distances between atoms.

    Returns:
        Material: The perturbed material.
    """

    configuration = PerturbationConfiguration(
        material=material,
        perturbation_function_holder=PerturbationFunctionHolder(function=perturbation_function),
        use_cartesian_coordinates=use_cartesian_coordinates,
    )
    if is_isometric:
        builder = IsometricPerturbationBuilder()
    else:
        builder = PerturbationBuilder()
    return builder.get_material(configuration)


def create_maxwell_displacement(
    material: Union[Material, MaterialWithBuildMetadata],
    disorder_parameter: float,
    random_seed: Optional[int] = None,
    is_mass_used: bool = True,
) -> Material:
    """
    Apply Maxwell-Boltzmann random displacements to a material.

    Generates random 3D displacement vectors where each component follows a normal
    distribution with variance proportional to disorder_parameter/m (if is_mass_used=True)
    or disorder_parameter (if is_mass_used=False), where m is atomic mass.

    Args:
        material: The material to be perturbed.
        disorder_parameter: Disorder parameter controlling displacement magnitude,
                            can be viewed as effective temperature in eV.
        random_seed: Optional random seed for reproducibility for the same material and parameters.
        is_mass_used: If True, displacement variance is disorder_parameter/m (mass-dependent).
                     If False, displacement variance is disorder_parameter (mass-independent).

    Returns:
        Material with applied Maxwell-Boltzmann displacements.
    """
    displacement_holder = MaxwellBoltzmannDisplacementHolder(
        disorder_parameter=disorder_parameter,
        random_seed=random_seed,
        is_mass_used=is_mass_used,
    )

    configuration = PerturbationConfiguration(
        material=material,
        perturbation_function_holder=displacement_holder,
        use_cartesian_coordinates=True,
    )

    builder = PerturbationBuilder()

    return builder.get_material(configuration)
