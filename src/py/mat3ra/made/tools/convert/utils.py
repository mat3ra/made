import json
from typing import Any, Dict, List, Union

import numpy as np
from mat3ra.made.data_helper import DATA_DIR
from mat3ra.made.utils import get_center_of_coordinates, map_array_to_array_with_id_value
from mat3ra.utils.object import NumpyNDArrayRoundEncoder
from scipy.spatial.distance import pdist

from ..third_party import ASEAtoms, PymatgenInterface, PymatgenStructure
from .interface_parts_enum import INTERFACE_LABELS_MAP

_CONSTANTS_FILE = DATA_DIR / "constants.json"
with open(_CONSTANTS_FILE) as _f:
    _CONSTANTS = json.load(_f)

DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE = _CONSTANTS["molecule"]["nonPeriodicMinimumLatticeSize"]
DIATOMIC_LATTICE_PADDING_FACTOR = _CONSTANTS["molecule"]["diatomicLatticePaddingFactor"]
MOLECULAR_LATTICE_PADDING_FACTOR = _CONSTANTS["molecule"]["molecularLatticePaddingFactor"]


def _get_non_periodic_lattice_padding_factor(max_distance: float, min_distance: float) -> float:
    if max_distance <= 0:
        return MOLECULAR_LATTICE_PADDING_FACTOR
    width_ratio = min_distance / max_distance
    if np.isclose(width_ratio, 1.0):
        return DIATOMIC_LATTICE_PADDING_FACTOR
    return MOLECULAR_LATTICE_PADDING_FACTOR


def _get_non_periodic_lattice_size(
    shifted_positions: np.ndarray,
    default_min_size: float = DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE,
) -> float:
    if len(shifted_positions) < 2:
        return max(default_min_size, 10.0)
    distances = pdist(shifted_positions)
    max_distance = float(np.max(distances))
    min_distance = float(np.min(distances))
    padding_factor = _get_non_periodic_lattice_padding_factor(max_distance, min_distance)
    return max(default_min_size, max_distance * padding_factor)


def extract_labels_from_pymatgen_structure(structure: PymatgenStructure) -> List[int]:
    labels = []
    if isinstance(structure, PymatgenInterface):
        labels = list(map(lambda s: INTERFACE_LABELS_MAP[s.properties["interface_label"]], structure.sites))
    return labels


def extract_metadata_from_pymatgen_structure(structure: PymatgenStructure) -> Dict[str, Any]:
    metadata = {}
    # TODO: consider using Interface JSONSchema from ESSE when such created and adapt interface_properties accordingly.
    # Add interface properties to metadata according to pymatgen Interface as a JSON object
    if hasattr(structure, "interface_properties"):
        interface_props = structure.interface_properties
        # TODO: figure out how to round the values and stringify terminations tuple
        #  in the interface properties with Encoder
        for key, value in interface_props.items():
            if isinstance(value, tuple):
                interface_props[key] = str(value)
        metadata["interface_properties"] = json.loads(json.dumps(interface_props, cls=NumpyNDArrayRoundEncoder))

    return metadata


def extract_tags_from_ase_atoms(atoms: ASEAtoms) -> List[Union[str, int]]:
    result = []
    if "tags" in atoms.arrays:
        int_tags = [int(tag) for tag in atoms.arrays["tags"] if tag is not None]
        result = map_array_to_array_with_id_value(int_tags, remove_none=True)
    return result


def calculate_padded_cell_simple_cubic(
    coordinates: List[List[float]],
    default_min_size: float = DEFAULT_NON_PERIODIC_MIN_LATTICE_SIZE,
) -> List[List[float]]:
    """
    Calculate values for a padded cell for a molecule based on its coordinates.
    Args:
        coordinates (Array[Array[float]]): A list of atomic coordinates.
        default_min_size (float): Minimum cubic lattice parameter in angstroms.
    Returns:
        Array[float]: A list containing the final cell latice vectors with padding applied.
    """
    positions = np.array(coordinates)
    center = get_center_of_coordinates(positions)
    shifted_positions = positions - center
    padding_value = _get_non_periodic_lattice_size(shifted_positions, default_min_size)

    return [
        [padding_value, 0.0, 0.0],
        [0.0, padding_value, 0.0],
        [0.0, 0.0, padding_value],
    ]
