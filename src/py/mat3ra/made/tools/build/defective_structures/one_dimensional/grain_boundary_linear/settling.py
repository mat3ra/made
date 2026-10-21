"""The boundary's moving atoms pulled to the material's bond length by least squares, the grains' bulk fixed."""
import numpy as np
from scipy.optimize import least_squares

from .network import Network


def get_bond_length_deviations(
    moving_positions: np.ndarray, network: Network, offsets: np.ndarray, bond_length: float
) -> np.ndarray:
    """Each bond's length minus the material's bond length, with the moving atoms at the given positions."""
    positions = network.positions.copy()
    positions[network.moving] = moving_positions.reshape(-1, 2)
    first, second, _ = zip(*network.bonds)
    return np.linalg.norm(positions[list(second)] + offsets - positions[list(first)], axis=1) - bond_length


def get_settled_positions(network: Network, cell_size: np.ndarray, bond_length: float) -> np.ndarray:
    """The network's positions with its moving atoms settled to the bond length."""
    offsets = np.array([shift for _, _, shift in network.bonds]) * cell_size
    start = network.positions[network.moving].ravel()
    result = least_squares(get_bond_length_deviations, start, args=(network, offsets, bond_length))
    positions = network.positions.copy()
    positions[network.moving] = result.x.reshape(-1, 2)
    return positions
