from typing import Dict, Optional

import numpy as np
from mat3ra.made.material import Material

from ...convert.interface_parts_enum import InterfacePartsEnum
from .surface_site_analyzer import SurfaceSiteAnalyzer


def get_film_site_occupation(
    interface: Material, analyzer: Optional[SurfaceSiteAnalyzer] = None
) -> Dict[int, Optional[str]]:
    """
    Which named substrate site each film atom sits on — atom index -> site name, None for no site.
    The default analyzer takes the substrate's top surface.

    Args:
        interface (Material): The interface material, film and substrate labelled.
        analyzer (Optional[SurfaceSiteAnalyzer]): The substrate surface to resolve film atoms against.

    Returns:
        Dict[int, Optional[str]]: Film atom index -> site name, None where no site matches.

    Raises:
        ValueError: when the material carries no film-labelled or no substrate-labelled atoms.
    """
    labels = interface.basis.labels.values
    if InterfacePartsEnum.FILM.value not in labels:
        raise ValueError("The material is not an interface — no film labels.")
    if InterfacePartsEnum.SUBSTRATE.value not in labels:
        raise ValueError("The material is not an interface — no substrate labels.")
    if analyzer is None:
        substrate = interface.clone()
        substrate.basis.filter_atoms_by_labels([InterfacePartsEnum.SUBSTRATE.value])
        analyzer = SurfaceSiteAnalyzer(material=substrate)
    cartesian = interface.clone()
    cartesian.to_cartesian()
    coordinates = np.array(cartesian.coordinates_array)
    return {
        i: analyzer.get_site_name(coordinates[i].tolist(), use_cartesian_coordinates=True)
        for i, label in enumerate(labels)
        if label == InterfacePartsEnum.FILM.value
    }
