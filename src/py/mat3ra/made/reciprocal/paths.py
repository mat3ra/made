"""
Default k-point paths according to AFLOW methodology.

Reference: https://arxiv.org/abs/1004.2974
Paths are split in parts for clarity.

Raw segment data is stored in reciprocal_paths.json (shared with JS/TS).
"""

import json
from typing import Dict, List

from mat3ra.made.data_helper import DATA_DIR

_JSON_FILE = DATA_DIR / "reciprocal_paths.json"
with open(_JSON_FILE) as f:
    _POINTS: Dict[str, List[List[str]]] = json.load(f)


def _build_reciprocal_paths() -> Dict[str, List[dict]]:
    """Flatten path segments and assign default step count to each point."""
    result: Dict[str, List[dict]] = {}
    for key, path_segments in _POINTS.items():
        flattened = [point for segment in path_segments for point in segment]
        # TODO: calculate number of steps based on distance in k-space
        result[key] = [{"point": point, "steps": 10} for point in flattened]
    return result


RECIPROCAL_PATHS: Dict[str, List[dict]] = _build_reciprocal_paths()
