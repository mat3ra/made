"""
Routines for calculating primitive cell vectors from conventional cell Bravais parameters.
Python equivalent of src/js/cell/primitive_cell.ts.

Following Setyawan, W., & Curtarolo, S. (2010). doi:10.1016/j.commatsci.2010.05.010
"""

import math
from typing import List

from mat3ra.esse.models.properties_directory.structural.lattice import LatticeSchema
from mat3ra.made.cell import Cell

Matrix3x3 = List[List[float]]


def _rhl(p: LatticeSchema) -> Matrix3x3:
    a = p.a
    alpha_rad = math.radians(p.alpha)

    cos_alpha = math.cos(alpha_rad)
    cos_half_alpha = math.cos(alpha_rad / 2.0)
    sin_half_alpha = math.sin(alpha_rad / 2.0)

    z_comp = a * math.sqrt(1.0 - (cos_alpha / cos_half_alpha) ** 2)

    return [
        [a * cos_half_alpha, -a * sin_half_alpha, 0.0],
        [a * cos_half_alpha, a * sin_half_alpha, 0.0],
        [(a * cos_alpha) / cos_half_alpha, 0.0, z_comp],
    ]


def _tri(p: LatticeSchema) -> Matrix3x3:
    """
    Algorithm from pymatgen (from_params).
    Mirrors the TRI case in primitive_cell.ts exactly.
    """
    alpha = math.radians(p.alpha)
    beta = math.radians(p.beta)
    gamma = math.radians(p.gamma)

    cos_alpha = math.cos(alpha)
    cos_beta = math.cos(beta)
    cos_gamma = math.cos(gamma)
    sin_alpha = math.sin(alpha)
    sin_beta = math.sin(beta)

    acos_arg = (cos_alpha * cos_beta - cos_gamma) / (sin_alpha * sin_beta)
    # Clamp to [-1, 1] to guard against floating-point drift
    acos_arg = max(-1.0, min(1.0, acos_arg))

    gamma_star = math.acos(acos_arg)
    cos_gamma_star = math.cos(gamma_star)
    sin_gamma_star = math.sin(gamma_star)

    a, b, c = p.a, p.b, p.c
    return [
        [a * sin_beta, 0.0, a * cos_beta],
        [-b * sin_alpha * cos_gamma_star, b * sin_alpha * sin_gamma_star, b * cos_alpha],
        [0.0, 0.0, c],
    ]


PRIMITIVE_CELLS = {
    "CUB": lambda p: [
        [p.a, 0, 0],
        [0, p.a, 0],
        [0, 0, p.a],
    ],
    "FCC": lambda p: [
        [0.0, p.a / 2, p.a / 2],
        [p.a / 2, 0.0, p.a / 2],
        [p.a / 2, p.a / 2, 0.0],
    ],
    "BCC": lambda p: [
        [-p.a / 2, p.a / 2, p.a / 2],
        [p.a / 2, -p.a / 2, p.a / 2],
        [p.a / 2, p.a / 2, -p.a / 2],
    ],
    "TET": lambda p: [
        [p.a, 0, 0],
        [0, p.a, 0],
        [0, 0, p.c],
    ],
    "BCT": lambda p: [
        [-p.a / 2, p.a / 2, p.c / 2],
        [p.a / 2, -p.a / 2, p.c / 2],
        [p.a / 2, p.a / 2, -p.c / 2],
    ],
    "ORC": lambda p: [
        [p.a, 0, 0],
        [0, p.b, 0],
        [0, 0, p.c],
    ],
    "ORCF": lambda p: [
        [0, p.b / 2, p.c / 2],
        [p.a / 2, 0, p.c / 2],
        [p.a / 2, p.b / 2, 0],
    ],
    "ORCI": lambda p: [
        [-p.a / 2, p.b / 2, p.c / 2],
        [p.a / 2, -p.b / 2, p.c / 2],
        [p.a / 2, p.b / 2, -p.c / 2],
    ],
    "ORCC": lambda p: [
        [p.a / 2, p.b / 2, 0],
        [-p.a / 2, p.b / 2, 0],
        [0, 0, p.c],
    ],
    "HEX": lambda p: [
        [p.a / 2, -(p.a * math.sqrt(3)) / 2, 0],
        [p.a / 2, (p.a * math.sqrt(3)) / 2, 0],
        [0, 0, p.c],
    ],
    "RHL": _rhl,
    "MCL": lambda p: [
        [p.a, 0, 0],
        [0, p.b, 0],
        [0, p.c * math.cos(math.radians(p.alpha)), p.c * math.sin(math.radians(p.alpha))],
    ],
    "MCLC": lambda p: [
        [p.a / 2, p.b / 2, 0],
        [-p.a / 2, p.b / 2, 0],
        [0, p.c * math.cos(math.radians(p.alpha)), p.c * math.sin(math.radians(p.alpha))],
    ],
    "TRI": _tri,
}


def get_primitive_lattice_vectors_from_config(lattice_config: LatticeSchema) -> Matrix3x3:
    """
    Returns lattice vectors for a primitive cell for a given lattice config.
    Python equivalent of getPrimitiveLatticeVectorsFromConfig() in primitive_cell.ts.

    Args:
        lattice_config: LatticeSchema instance with fields:
            type, a, b, c, alpha, beta, gamma.

    Returns:
        3x3 list of lists (rows = vectors a, b, c) in the same units as the
        input lattice parameters (typically Angstroms).
    """
    lattice_type = lattice_config.type.value if lattice_config.type else "TRI"
    generator = PRIMITIVE_CELLS.get(lattice_type)
    if generator is None:
        raise ValueError(
            f"Unsupported lattice type '{lattice_type}'. " f"Must be one of: {list(PRIMITIVE_CELLS.keys())}"
        )
    return generator(lattice_config)


def get_primitive_cell_from_config(lattice_config: LatticeSchema) -> Cell:
    """Returns a full Cell object instantiated with the primitive lattice vectors."""
    vectors = get_primitive_lattice_vectors_from_config(lattice_config)
    return Cell.from_vectors_array(vectors)
