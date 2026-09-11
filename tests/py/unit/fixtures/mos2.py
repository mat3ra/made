from typing import Any, Dict

MOS2: Dict[str, Any] = {
    "name": "MoS2 monolayer",
    "basis": {
        "elements": [{"id": 0, "value": "Mo"}, {"id": 1, "value": "S"}, {"id": 2, "value": "S"}],
        "coordinates": [
            {"id": 0, "value": [0.3333, 0.6667, 0.5]},
            {"id": 1, "value": [0.6667, 0.3333, 0.42]},
            {"id": 2, "value": [0.6667, 0.3333, 0.58]},
        ],
        "units": "crystal",
    },
    "lattice": {
        "a": 3.19,
        "b": 3.19,
        "c": 20.0,
        "alpha": 90,
        "beta": 90,
        "gamma": 120,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "HEX",
    },
}
