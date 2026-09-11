from typing import Callable, List, Literal, Optional

import numpy as np
from mat3ra.made.material import Material
from scipy.spatial import cKDTree

from ..build.processed_structures.two_dimensional.passivation.enums import SurfaceTypesEnum
from ..convert import decorator_convert_material_args_kwargs_to_atoms, to_pymatgen
from ..third_party import ASEAtoms, PymatgenIStructure
from ..utils import decorator_convert_position_to_coordinate
from .utils import decorator_handle_periodic_boundary_conditions


@decorator_convert_material_args_kwargs_to_atoms
def get_average_interlayer_distance(
    interface_atoms: ASEAtoms, tag_substrate: str, tag_film: str, threshold: float = 0.5
) -> float:
    """
    Calculate the average distance between the top layer of substrate atoms and the bottom layer of film atoms.

    Args:
        interface_atoms (ase.ASEAtoms): The ASE ASEAtoms object containing both sets of atoms.
        tag_substrate (int): The tag representing the substrate atoms.
        tag_film (int): The tag representing the film atoms.
        threshold (float): The threshold for identifying the top and bottom layers of atoms.

    Returns:
        float: The average distance between the top layer of substrate and the bottom layer of film.
    """
    # Extract z-coordinates of substrate and film atoms
    z_substrate = interface_atoms.positions[interface_atoms.get_tags() == tag_substrate][:, 2]
    z_film = interface_atoms.positions[interface_atoms.get_tags() == tag_film][:, 2]

    # Identify the top layer of substrate atoms and bottom layer of film atoms by z-coordinate
    top_substrate_layer_z = np.max(z_substrate)
    bottom_film_layer_z = np.min(z_film)

    # Get the average z-coordinate of the top substrate atoms (within a threshold from the top)
    top_substrate_atoms = z_substrate[z_substrate >= top_substrate_layer_z - threshold]
    avg_z_top_substrate = np.mean(top_substrate_atoms)

    # Get the average z-coordinate of the bottom film atoms (within a threshold from the bottom)
    bottom_film_atoms = z_film[z_film <= bottom_film_layer_z + threshold]
    avg_z_bottom_film = np.mean(bottom_film_atoms)

    # Calculate the average distance between the top layer of substrate and the bottom layer of film
    average_interlayer_distance = avg_z_bottom_film - avg_z_top_substrate
    return abs(average_interlayer_distance)


@decorator_convert_material_args_kwargs_to_atoms
def get_surface_area(atoms: ASEAtoms):
    """
    Calculate the area of the surface perpendicular to the z-axis of the atoms structure.

    Args:
        atoms (ase.ASEAtoms): The ASEAtoms object to calculate the surface area of.

    Returns:
        float: The surface area of the atoms.
    """
    matrix = atoms.cell
    cross_product = np.cross(matrix[0], matrix[1])
    return np.linalg.norm(cross_product)


@decorator_convert_material_args_kwargs_to_atoms
def get_chemical_formula_empirical(atoms: ASEAtoms) -> str:
    """
    Calculate the formula of the atoms structure.

    Args:
        atoms (ase.ASEAtoms): The ASEAtoms object to calculate the formula of.

    Returns:
        str: The formula of the atoms.
    """
    return atoms.get_chemical_formula(empirical=True)


def get_closest_site_id_from_coordinate(
    material: Material, coordinate: List[float], use_cartesian_coordinates: bool = False
) -> int:
    """
    Get the site ID of the closest site to a given coordinate in the crystal.

    Args:
        material (Material): The material object to find the closest site in.
        coordinate (List[float]): The coordinate to find the closest site to.
        use_cartesian_coordinates (bool): Whether to use Cartesian coordinates for the calculation.

    Returns:
        int: The site ID of the closest site.
    """
    new_material = material.clone()
    if use_cartesian_coordinates:
        new_material.to_cartesian()
    coordinates = np.array(new_material.coordinates_array)
    coordinate = np.array(coordinate)  # type: ignore
    distances = np.linalg.norm(coordinates - coordinate, axis=1)
    return int(np.argmin(distances))


def get_closest_site_id_from_coordinate_and_element(
    material: Material,
    coordinate: List[float],
    chemical_element: Optional[str] = None,
    use_cartesian_coordinates: bool = False,
) -> int:
    """
    Get the site ID of the closest site with a given element to a given coordinate in the crystal.

    Args:
        material (Material): The material object to find the closest site in.
        coordinate (List[float]): The coordinate to find the closest site to.
        chemical_element (str): The element of the site to find.
        use_cartesian_coordinates (bool): Whether to use Cartesian coordinates for the calculation.

    Returns:
        int: The site ID of the closest site with the given element.
    """
    new_material = material.clone()
    if use_cartesian_coordinates:
        new_material.to_cartesian()
    coordinates = np.array(new_material.basis.coordinates.values)
    coordinate = np.array(coordinate)  # type: ignore
    distances = np.linalg.norm(coordinates - coordinate, axis=1)

    if chemical_element is not None:
        elements = np.array(new_material.basis.elements.values)
        element_indices = np.where(elements == chemical_element)[0]
        distances = distances[element_indices]
        return int(element_indices[np.argmin(distances)])
    else:
        return int(np.argmin(distances))


def get_closest_site_id_from_coordinate_within_radius(
    material: Material,
    coordinate: List[float],
    radius: float,
    chemical_element: Optional[str] = None,
    use_cartesian_coordinates: bool = False,
) -> int:
    """
    The site ID of the closest site (of `chemical_element`, when given) within `radius` Angstrom of
    a coordinate in the crystal — the way a person points at an atom: "the Mo near (0.9, 0.1, 0.5)".

    Args:
        material (Material): The material object to find the closest site in.
        coordinate (List[float]): The coordinate to find the closest site to.
        radius (float): Search radius, in Angstrom.
        chemical_element (str): Restrict the search to this element.
        use_cartesian_coordinates (bool): Whether `coordinate` is cartesian.

    Returns:
        int: The site ID of the closest qualifying site.

    Raises:
        ValueError: when no site qualifies, stating how far the nearest one of that element is.
    """
    found = get_atom_indices_within_radius_pbc(
        material,
        atom_index=None,
        coordinate=coordinate,
        radius=radius,
        chemical_element=chemical_element,
        use_cartesian_coordinates=use_cartesian_coordinates,
        centre_on_coordinate=True,
    )
    if found:
        return found[0]

    elements = material.basis.elements.values
    candidates = [
        index for index, element in enumerate(elements) if chemical_element is None or element == chemical_element
    ]
    what = chemical_element or "atom"
    if not candidates:
        raise ValueError(f"No {what} in the material")

    structure = to_pymatgen(material)
    point = np.array(coordinate, dtype=float)
    fractional_point = structure.lattice.get_fractional_coords(point) if use_cartesian_coordinates else point
    nearest = min(
        structure.lattice.get_distance_and_image(fractional_point, structure.frac_coords[index])[0]
        for index in candidates
    )
    raise ValueError(f"No {what} within {radius} A of {coordinate}; the nearest {what} is {nearest:.2f} A away")


def get_atom_indices_within_layer_by_atom_index(material: Material, atom_index: int, layer_thickness: float):
    """
    Select all atoms within a specified layer thickness of a central atom along a direction.
    This direction will be orthogonal to the AB plane.
    Layer thickness is converted from angstroms to fractional units based on the lattice vector length.

    Args:
        material (Material): Material object
        atom_index (int): Index of the central atom
        layer_thickness (float): Thickness of the layer in angstroms

    Returns:
        List[int]: List of indices of atoms within the specified layer
    """
    # TODO: use Coordinates class functions
    coordinates = material.basis.coordinates.to_array_of_values_with_ids()
    vectors = material.lattice.vectors
    direction_vector = np.array(vectors[2])

    # Normalize the direction vector
    direction_length = np.linalg.norm(direction_vector)
    direction_norm = direction_vector / direction_length
    central_atom_coordinate = coordinates[atom_index]
    central_atom_projection = np.dot(central_atom_coordinate.value, direction_norm)

    layer_thickness_frac = layer_thickness / direction_length

    lower_bound = central_atom_projection - layer_thickness_frac / 2
    upper_bound = central_atom_projection + layer_thickness_frac / 2

    selected_indices = []
    for coord in coordinates:
        # Project each coordinate onto the direction vector
        projection = np.dot(coord.value, direction_norm)
        if lower_bound <= projection <= upper_bound:
            selected_indices.append(coord.id)
    return selected_indices


def get_atom_indices_within_layer_by_atom_coordinate(
    material: Material, coordinate: List[float], layer_thickness: float
):
    """
    Select all atoms within a specified layer thickness of a central atom along a direction.
    This direction will be orthogonal to the AB plane.
    Layer thickness is converted from angstroms to fractional units based on the lattice vector length.

    Args:
        material (Material): Material object
        coordinate (List[float]): Coordinate of the central atom in crystal coordinates
        layer_thickness (float): Thickness of the layer in angstroms

    Returns:
        List[int]: List of indices of atoms within the specified layer
    """
    site_id = get_closest_site_id_from_coordinate(material, coordinate)
    return get_atom_indices_within_layer_by_atom_index(material, site_id, layer_thickness)


def get_atom_indices_within_layer(
    material: Material,
    atom_index: Optional[int] = 0,
    coordinate: Optional[List[float]] = None,
    layer_thickness: float = 1,
):
    """
    Select all atoms within a specified layer thickness of the central atom along the c-vector direction.

    Args:
        material (Material): Material object
        atom_index (int): Index of the central atom
        coordinate (List[float]): Coordinate of the central atom in crystal coordinates
        layer_thickness (float): Thickness of the layer in angstroms

    Returns:
        List[int]: List of indices of atoms within the specified layer
    """
    if coordinate is not None:
        return get_atom_indices_within_layer_by_atom_coordinate(material, coordinate, layer_thickness)
    if atom_index is not None:
        return get_atom_indices_within_layer_by_atom_index(material, atom_index, layer_thickness)


def get_atom_indices_within_radius_pbc(
    material: Material,
    atom_index: Optional[int] = 0,
    coordinate: Optional[List[float]] = None,
    radius: float = 1,
    chemical_element: Optional[str] = None,
    use_cartesian_coordinates: bool = False,
    centre_on_coordinate: bool = False,
) -> List[int]:
    """
    Select the atoms (of `chemical_element`, when given) within a specified radius of a point,
    nearest first, considering periodic boundary conditions via pymatgen's `get_sites_in_sphere` —
    the correct minimum image on any cell, including non-orthogonal ones.

    When `coordinate` is given and `centre_on_coordinate` is False (the default), the sphere is
    centred on the atom closest to the coordinate — the pre-existing behaviour that
    `filter_by_sphere` and `create_cluster_sphere.ipynb` rely on. When `centre_on_coordinate` is
    True, the sphere is centred on the coordinate itself — the way a person points at an atom: "the
    Mo near (0.25, 0.25, 0.5)". Without a `coordinate`, the sphere is centred on `atom_index`.

    Args:
        material (Material): Material object
        atom_index (int): Index of the central atom; used when `coordinate` is None
        coordinate (List[float]): Centre (or near-centre) of the sphere; crystal unless
            `use_cartesian_coordinates`
        radius (float): Radius of the sphere in angstroms
        chemical_element (str): Restrict the result to this element
        use_cartesian_coordinates (bool): Whether `coordinate` is cartesian
        centre_on_coordinate (bool): Whether the sphere is centred on `coordinate` itself rather
            than on the atom closest to it

    Returns:
        List[int]: Indices of atoms within the radius, nearest first
    """
    structure = to_pymatgen(material)

    if coordinate is not None and centre_on_coordinate:
        point = np.array(coordinate, dtype=float)
        center = point if use_cartesian_coordinates else structure.lattice.get_cartesian_coords(point)
    else:
        if coordinate is not None:
            atom_index = get_closest_site_id_from_coordinate(material, coordinate, use_cartesian_coordinates)
        immutable_structure = PymatgenIStructure.from_sites(structure.sites)
        center = immutable_structure[atom_index].coords

    sites_within_radius = sorted(structure.get_sites_in_sphere(center, radius), key=lambda site: site.nn_distance)
    selected_indices: List[int] = []
    for site in sites_within_radius:
        if chemical_element is not None and site.species_string != chemical_element:
            continue
        if int(site.index) not in selected_indices:
            selected_indices.append(int(site.index))
    return selected_indices


def get_atom_indices_with_condition_on_coordinates(
    material: Material,
    condition: Callable[[List[float]], bool],
    use_cartesian_coordinates: bool = False,
) -> List[int]:
    """
    Select atoms whose coordinates satisfy the given condition.

    Args:
        material (Material): Material object
        condition (Callable[List[float], bool]): Function that checks if coordinates satisfy the condition.
        use_cartesian_coordinates (bool): Whether to use Cartesian coordinates for the condition evaluation.

    Returns:
        List[int]: List of indices of atoms whose coordinates satisfy the condition.
    """
    new_material = material.clone()
    new_basis = new_material.basis
    if use_cartesian_coordinates:
        new_basis.to_cartesian()
    else:
        new_basis.to_crystal()
    new_material.basis = new_basis
    # TODO: use Coordinates class functions
    coordinates = new_material.basis.coordinates.to_array_of_values_with_ids()

    selected_indices = []
    for coord in coordinates:
        if condition(coord.value):
            selected_indices.append(coord.id)

    return selected_indices


def is_height_within_limits(z: float, z_extremum: float, depth: float, surface: SurfaceTypesEnum) -> bool:
    """
    Check if the height of an atom is within the specified limits.

    Args:
        z (float): The z-coordinate of the atom.
        z_extremum (float): The extremum z-coordinate of the surface.
        depth (float): The depth from the surface to look for exposed atoms.
        surface (SurfaceTypesEnum): The surface type (top or bottom).

    Returns:
        bool: True if the height is within the limits, False otherwise.
    """
    return (z >= z_extremum - depth) if surface == SurfaceTypesEnum.TOP else (z <= z_extremum + depth)


def is_shadowed_by_neighbors_from_surface(
    z: float, neighbors_indices: List[int], surface: SurfaceTypesEnum, coordinates: np.ndarray
) -> bool:
    """
    Check if any one of the neighboring atoms shadow the atom from the surface by being closer to the specified surface.

    Args:
        z (float): The z-coordinate of the atom.
        neighbors_indices (List[int]): List of indices of neighboring atoms.
        surface (SurfaceTypesEnum): The surface type (top or bottom).
        coordinates (np.ndarray): The coordinates of the atoms.

    Returns:
        bool: True if the atom is not shadowed, False otherwise.
    """
    return not any(
        (coordinates[n][2] > z if surface == SurfaceTypesEnum.TOP else coordinates[n][2] < z) for n in neighbors_indices
    )


@decorator_handle_periodic_boundary_conditions(cutoff=0.25)
def get_surface_atom_indices(
    material: Material,
    surface: SurfaceTypesEnum = SurfaceTypesEnum.TOP,
    shadowing_radius: float = 2.5,
    depth: float = 5,
) -> List[int]:
    """
    Identify exposed atoms on the top or bottom surface of the material.

    Args:
        material (Material): Material object to get surface atoms from.
        surface (SurfaceTypesEnum): Specify "top" or "bottom" to detect the respective surface atoms.
        shadowing_radius (float): Radius for atoms shadowing underlying from detecting as exposed.
        depth (float): Depth from the surface to look for exposed atoms.

    Returns:
        List[int]: List of indices of exposed surface atoms.
    """
    new_material = material.clone()
    new_material.to_cartesian()
    coordinates = np.array(new_material.basis.coordinates.values)
    ids = new_material.basis.coordinates.ids

    # Get z-extremum of atoms inside the unit cell and sort atoms by z-coordinate
    z_coords = coordinates[:, 2]
    unit_cell_mask = (z_coords > 0) & (z_coords <= material.lattice.c)
    coords_inside_unit_cell = coordinates[unit_cell_mask]
    z_extremum = (
        np.max(coords_inside_unit_cell[:, 2])
        if surface == SurfaceTypesEnum.TOP
        else np.min(coords_inside_unit_cell[:, 2])
    )

    # First filter by height to be within the specified depth from the surface
    height_mask = np.array([is_height_within_limits(z, z_extremum, depth, surface) for z in z_coords])
    potential_surface_indices = np.where(height_mask)[0]

    if len(potential_surface_indices) == 0:
        return []

    # For remaining atoms, check shadowing using KDTree
    try:
        kd_tree = cKDTree(coordinates)
        exposed_atoms_indices = []

        for idx in potential_surface_indices:
            x, y, z = coordinates[idx]
            try:
                neighbors_indices = kd_tree.query_ball_point([x, y, z], r=shadowing_radius)
                if is_shadowed_by_neighbors_from_surface(z, neighbors_indices, surface, coordinates):
                    exposed_atoms_indices.append(ids[idx])
            except Exception:
                # Fallback if KDTree query fails - manual distance calculation
                neighbors_indices = []
                for i, coord in enumerate(coordinates):
                    if i != idx:
                        dist = np.linalg.norm(coord - coordinates[idx])
                        if dist <= shadowing_radius:
                            neighbors_indices.append(i)
                if is_shadowed_by_neighbors_from_surface(z, neighbors_indices, surface, coordinates):
                    exposed_atoms_indices.append(ids[idx])

    except Exception:
        # Fallback if KDTree fails completely - use simple z-coordinate based detection
        z_threshold = z_extremum - (0.5 * depth) if surface == SurfaceTypesEnum.TOP else z_extremum + (0.5 * depth)
        exposed_atoms_indices = [
            ids[i]
            for i in potential_surface_indices
            if (surface == SurfaceTypesEnum.TOP and z_coords[i] >= z_threshold)
            or (surface == SurfaceTypesEnum.BOTTOM and z_coords[i] <= z_threshold)
        ]

    return exposed_atoms_indices


@decorator_convert_position_to_coordinate
def get_local_extremum_atom_index(
    material: Material,
    coordinate: List[float],
    extremum: Literal["max", "min"] = "max",
    vicinity: float = 1.0,
    use_cartesian_coordinates: bool = False,
) -> int:
    """
    Return the id of the atom with the minimum or maximum z-coordinate
    within a certain vicinity of a given (x, y) coordinate.

    Args:
        material (Material): Material object.
        coordinate (List[float]): (x, y, z) coordinate to find the local extremum atom index for.
        extremum (str): "min" or "max".
        vicinity (float): Radius of the vicinity, in Angstroms.
        use_cartesian_coordinates (bool): Whether to use Cartesian coordinates.

    Returns:
        int: id of the atom with the minimum or maximum z-coordinate.
    """
    new_material = material.clone()
    new_material.to_cartesian()
    if not use_cartesian_coordinates:
        coordinate = new_material.basis.cell.convert_point_to_cartesian(coordinate)

    coordinates = np.array(new_material.basis.coordinates.values)
    ids = np.array(new_material.basis.coordinates.ids)
    tree = cKDTree(coordinates[:, :2])
    indices = tree.query_ball_point(coordinate[:2], vicinity)
    z_values = [(id, coord[2]) for id, coord in zip(ids[indices], coordinates[indices])]

    if extremum == "max":
        extremum_z_atom = max(z_values, key=lambda item: item[1])
    else:
        extremum_z_atom = min(z_values, key=lambda item: item[1])

    return extremum_z_atom[0]


def get_atom_indices_by_layer(material: Material, tolerance: float = 0.5) -> List[List[int]]:
    """
    Atom indices grouped into layers along z, bottom layer first.

    Consecutive heights closer than `tolerance` Angstrom belong to one layer, so the grouping is
    the same whatever order the basis lists the atoms in.

    Args:
        material: Material object.
        tolerance: Height gap, in Angstrom, that separates two layers.
    """
    cartesian = material.clone()
    cartesian.to_cartesian()
    heights = np.array(cartesian.coordinates_array)[:, 2]
    layers: List[List[int]] = []
    previous_height: Optional[float] = None
    for index in np.argsort(heights, kind="stable"):
        if previous_height is None or heights[index] - previous_height > tolerance:
            layers.append([])
        layers[-1].append(int(index))
        previous_height = float(heights[index])
    return layers


def get_atom_indices_in_bottom_layers(
    material: Material,
    layer_count: int,
    atom_indices: Optional[List[int]] = None,
    tolerance: float = 0.5,
) -> List[int]:
    """
    Indices of the atoms in the `layer_count` lowest layers, restricted to `atom_indices` when
    given — e.g. the substrate's, to hold its deepest layers fixed during a relaxation.

    Args:
        material: Material object.
        layer_count: How many layers to take, counting from the bottom.
        atom_indices: Restrict the selection to these atoms; all atoms when None.
        tolerance: Height gap, in Angstrom, that separates two layers.
    """
    if layer_count < 1:
        raise ValueError("layer_count must be at least 1")
    selected = None if atom_indices is None else set(atom_indices)
    layers = [
        [index for index in layer if selected is None or index in selected]
        for layer in get_atom_indices_by_layer(material, tolerance)
    ]
    occupied = [layer for layer in layers if layer]
    return sorted(index for layer in occupied[:layer_count] for index in layer)
