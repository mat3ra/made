from enum import Enum


class SiteSelectionMethodEnum(str, Enum):
    # Selects sites purely at random (seeded for reproducibility).
    RANDOM = "random"
    # Selects sites using Farthest Point Sampling for maximal dispersion under PBC.
    UNIFORM = "uniform"
