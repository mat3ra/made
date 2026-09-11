import copy
from typing import Any, Dict

# Two-layer square net: one atop, two bridges, and a four-fold hollow that is not fcc or hcp.
SQUARE_NET: Dict[str, Any] = {
    "name": "square net",
    "basis": {
        "elements": [{"id": 0, "value": "Cu"}, {"id": 1, "value": "Cu"}],
        "coordinates": [{"id": 0, "value": [0.5, 0.5, 0.1]}, {"id": 1, "value": [0.0, 0.0, 0.2]}],
        "units": "crystal",
    },
    "lattice": {
        "a": 2.5,
        "b": 2.5,
        "c": 15.0,
        "alpha": 90,
        "beta": 90,
        "gamma": 90,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TET",
    },
}

# Rectangular net: two distinct nearest-neighbour spacings, so two distinct bridges.
RECTANGULAR_NET: Dict[str, Any] = copy.deepcopy(SQUARE_NET)
RECTANGULAR_NET["lattice"]["b"] = 3.0
