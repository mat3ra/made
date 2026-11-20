from typing import Any, Dict

from ..monolayer import GRAPHENE

GRAPHENE_ZIGZAG_NANORIBBON: Dict[str, Any] = {
    "name": "Graphene (Zigzag nanoribbon)",
    "basis": {
        "elements": [
            {"id": 0, "value": "C"},
            {"id": 1, "value": "C"},
            {"id": 2, "value": "C"},
            {"id": 3, "value": "C"},
            {"id": 4, "value": "C"},
            {"id": 5, "value": "C"},
            {"id": 6, "value": "C"},
            {"id": 7, "value": "C"},
            {"id": 8, "value": "C"},
            {"id": 9, "value": "C"},
            {"id": 10, "value": "C"},
            {"id": 11, "value": "C"},
            {"id": 12, "value": "C"},
            {"id": 13, "value": "C"},
            {"id": 14, "value": "C"},
            {"id": 15, "value": "C"},
        ],
        "coordinates": [
            {"id": 0, "value": [0.062499937, 0.366666681, 0.5]},
            {"id": 1, "value": [0.312499937, 0.366666681, 0.5]},
            {"id": 2, "value": [0.187500062, 0.433333286, 0.5]},
            {"id": 3, "value": [0.187499937, 0.566666695, 0.5]},
            {"id": 4, "value": [0.062500062, 0.6333333, 0.5]},
            {"id": 5, "value": [0.562499937, 0.366666681, 0.5]},
            {"id": 6, "value": [0.437500062, 0.433333286, 0.5]},
            {"id": 7, "value": [0.437499937, 0.566666695, 0.5]},
            {"id": 8, "value": [0.312500062, 0.6333333, 0.5]},
            {"id": 9, "value": [0.812499938, 0.366666681, 0.5]},
            {"id": 10, "value": [0.687500062, 0.433333286, 0.5]},
            {"id": 11, "value": [0.687499937, 0.566666695, 0.5]},
            {"id": 12, "value": [0.562500062, 0.6333333, 0.5]},
            {"id": 13, "value": [0.937500063, 0.433333286, 0.5]},
            {"id": 14, "value": [0.937499937, 0.566666695, 0.5]},
            {"id": 15, "value": [0.812500063, 0.6333333, 0.5]},
        ],
        "units": "crystal",
        "constraints": [],
        "labels": [],
    },
    "lattice": {
        "a": 9.869164,
        "b": 10.683683422,
        "c": 20.0,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
    "isNonPeriodic": False,
    "metadata": {
        "boundaryConditions": {"type": "pbc", "offset": 0},
        "build": [
            {
                "configuration": {
                    "material": GRAPHENE,
                    "width": 2,
                    "length": 4,
                    "vacuum_width": 3,
                    "vacuum_length": 0,
                    "edge_type": "zigzag",
                }
            }
        ],
    },
}

GRAPHENE_ARMCHAIR_NANORIBBON = {
    "name": "Graphene (Armchair nanoribbon)",
    "basis": {
        "elements": [
            {"id": 0, "value": "C"},
            {"id": 1, "value": "C"},
            {"id": 2, "value": "C"},
            {"id": 3, "value": "C"},
            {"id": 4, "value": "C"},
            {"id": 5, "value": "C"},
            {"id": 6, "value": "C"},
            {"id": 7, "value": "C"},
            {"id": 8, "value": "C"},
            {"id": 9, "value": "C"},
            {"id": 10, "value": "C"},
            {"id": 11, "value": "C"},
            {"id": 12, "value": "C"},
            {"id": 13, "value": "C"},
            {"id": 14, "value": "C"},
            {"id": 15, "value": "C"},
        ],
        "coordinates": [
            {"id": 0, "value": [0.958333362, 0.35000006, 0.5]},
            {"id": 1, "value": [0.791666617, 0.34999996, 0.5]},
            {"id": 2, "value": [0.958333362, 0.550000054, 0.5]},
            {"id": 3, "value": [0.791666617, 0.549999954, 0.5]},
            {"id": 4, "value": [0.708333369, 0.450000057, 0.5]},
            {"id": 5, "value": [0.541666624, 0.449999957, 0.5]},
            {"id": 6, "value": [0.458333376, 0.35000006, 0.5]},
            {"id": 7, "value": [0.291666631, 0.34999996, 0.5]},
            {"id": 8, "value": [0.708333369, 0.650000051, 0.5]},
            {"id": 9, "value": [0.541666624, 0.649999951, 0.5]},
            {"id": 10, "value": [0.458333376, 0.550000054, 0.5]},
            {"id": 11, "value": [0.291666631, 0.549999954, 0.5]},
            {"id": 12, "value": [0.208333383, 0.450000057, 0.5]},
            {"id": 13, "value": [0.041666638, 0.449999957, 0.5]},
            {"id": 14, "value": [0.208333383, 0.650000051, 0.5]},
            {"id": 15, "value": [0.041666638, 0.649999951, 0.5]},
        ],
        "units": "crystal",
        "constraints": [],
        "labels": [],
    },
    "lattice": {
        "a": 8.546946738,
        "b": 12.336455,
        "c": 20.0,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
    "isNonPeriodic": False,
    "metadata": {
        "boundaryConditions": {"type": "pbc", "offset": 0},
        "build": [
            {
                "configuration": {
                    "material": GRAPHENE,
                    "width": 2,
                    "length": 4,
                    "vacuum_width": 3,
                    "vacuum_length": 0,
                    "edge_type": "armchair",
                }
            }
        ],
    },
}
