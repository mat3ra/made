from typing import List, Optional

import numpy as np
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.materials_category_components.entities.auxiliary.zero_dimensional.crystal_site import (
    CrystalSiteSchema,
)
from mat3ra.made.material import Material
from pydantic import Field


class CrystalSite(CrystalSiteSchema, InMemoryEntityPydantic):
    crystal: Optional[Material] = Field(None, exclude=True)
    # element: str
    coordinate: Optional[List[float]] = None
    nearest_neighbor_vectors: List[np.ndarray] = Field([], exclude=True)
    # coordination_number: int = 0
    # see https://www.cryst.ehu.es/cgi-bin/cryst/programs/nph-wp-list for an example

    wyckoff_letter: Optional[str] = None

    @property
    def coordination_number(self):
        return len(self.nearest_neighbor_vectors)
