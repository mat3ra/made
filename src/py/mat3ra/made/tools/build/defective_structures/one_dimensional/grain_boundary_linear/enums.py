"""The homo-bond choices other than an element symbol."""
from enum import Enum


class HomoBondsEnum(str, Enum):
    alternating = "alternating"
    none = "none"
