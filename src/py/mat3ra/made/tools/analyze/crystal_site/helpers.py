from typing import Dict, Optional

import numpy as np
from mat3ra.made.material import Material

from ...convert.interface_parts_enum import InterfacePartsEnum
from .enums import SurfaceSiteTypesEnum
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


def get_film_buckling(interface: Material, analyzer: Optional[SurfaceSiteAnalyzer] = None) -> Optional[float]:
    """
    The signed height of the film atom on the substrate's atop site above the other film atoms
    (their mean height when there is more than one), in Angstrom. None when no film atom is atop.

    Args:
        interface (Material): The interface material, film and substrate labelled.
        analyzer (Optional[SurfaceSiteAnalyzer]): The substrate surface to resolve film atoms against.

    Returns:
        Optional[float]: The atop film atom's height above the other film atoms, or None when no
            film atom is on an atop site.
    """
    occupation = get_film_site_occupation(interface, analyzer)
    atop_indices = [i for i, site in occupation.items() if site == SurfaceSiteTypesEnum.ATOP.value]
    if not atop_indices:
        return None
    other_indices = [i for i in occupation if i not in atop_indices]
    cartesian = interface.clone()
    cartesian.to_cartesian()
    heights = np.array(cartesian.coordinates_array)[:, 2]
    return float(np.mean(heights[atop_indices]) - np.mean(heights[other_indices]))
