from enum import Enum


class SurfaceSiteTypesEnum(str, Enum):
    ATOP = "atop"
    BRIDGE = "bridge"
    FCC = "fcc"
    HCP = "hcp"
    HOLLOW = "hollow"
