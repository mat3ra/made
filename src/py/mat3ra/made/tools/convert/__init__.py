import inspect
from functools import wraps
from typing import Any, Callable, Dict, Union

from mat3ra.made.material import Material
from mat3ra.made.utils import map_array_to_array_with_id_value, map_array_with_id_value_to_array
from mat3ra.utils import remove_comments_from_source_code
from mat3ra.utils.mixins import RoundNumericValuesMixin

from ..third_party import (
    ASEAtoms,
    PymatgenAseAtomsAdaptor,
    PymatgenInterface,
    PymatgenLattice,
    PymatgenPoscar,
    PymatgenStructure,
)
from .utils import (
    calculate_padded_cell_simple_cubic,
    extract_labels_from_pymatgen_structure,
    extract_metadata_from_pymatgen_structure,
    extract_tags_from_ase_atoms,
)


def to_pymatgen(material_or_material_data: Union[Material, Dict[str, Any]]) -> PymatgenStructure:
    """
    Converts material object in ESSE format to a pymatgen Structure object.

    Args:
        material_or_material_data (dict|class): A dictionary containing the material information in ESSE format.

    Returns:
        Structure: A pymatgen Structure object.
    """
    material_data = material_or_material_data

    if isinstance(material_or_material_data, Material):
        material_data = material_or_material_data.to_dict()

    lattice_params = material_data["lattice"]
    lattice = PymatgenLattice.from_parameters(
        a=lattice_params["a"],
        b=lattice_params["b"],
        c=lattice_params["c"],
        alpha=lattice_params["alpha"],
        beta=lattice_params["beta"],
        gamma=lattice_params["gamma"],
    )

    basis = material_data["basis"]
    elements = [element["value"] for element in basis["elements"]]
    coordinates = [coord["value"] for coord in basis["coordinates"]]
    labels_data = basis.get("labels", []) or []
    labels = [label["value"] for label in labels_data]
    # Assuming that the basis units are fractional since it's a crystal basis
    coords_are_cartesian = "units" in basis and basis["units"] == "angstrom"

    if "labels" in inspect.signature(PymatgenStructure.__init__).parameters:
        structure = PymatgenStructure(
            lattice, elements, coordinates, coords_are_cartesian=coords_are_cartesian, labels=labels
        )
    else:
        # Passing labels does not work for pymatgen `2023.6.23` supporting py3.8
        print(f"labels: {labels}. Not passing labels to pymatgen.")
        structure = PymatgenStructure(lattice, elements, coordinates, coords_are_cartesian=coords_are_cartesian)

    return structure


def from_pymatgen(structure: Union[PymatgenStructure, PymatgenInterface]) -> Dict[str, Any]:
    """
    Converts a pymatgen Structure object to a material object in ESSE format.

    Args:
        structure (Structure): A pymatgen Structure object.

    Returns:
        dict: A dictionary containing the material information in ESSE format.
    """
    __round__ = RoundNumericValuesMixin.round_array_or_number
    basis = {
        "elements": [{"id": i, "value": str(site.specie)} for i, site in enumerate(structure.sites)],
        "coordinates": [
            {"id": i, "value": __round__(list(site.frac_coords))} for i, site in enumerate(structure.sites)
        ],
        "units": "crystal",
        # `cell` is assigned by the `lattice` object during Material initialization
        # "cell": __round__(structure.lattice.matrix.tolist()),
        "constraints": [],
    }

    lattice = {
        "a": __round__(structure.lattice.a),
        "b": __round__(structure.lattice.b),
        "c": __round__(structure.lattice.c),
        "alpha": __round__(structure.lattice.alpha),
        "beta": __round__(structure.lattice.beta),
        "gamma": __round__(structure.lattice.gamma),
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
        "vectors": {
            "a": __round__(structure.lattice.matrix[0].tolist()),
            "b": __round__(structure.lattice.matrix[1].tolist()),
            "c": __round__(structure.lattice.matrix[2].tolist()),
            "alat": 1,
            "units": "angstrom",
        },
    }

    metadata = {
        **extract_metadata_from_pymatgen_structure(structure),
        "boundaryConditions": {"type": "pbc", "offset": 0},
    }

    basis["labels"] = map_array_to_array_with_id_value(
        extract_labels_from_pymatgen_structure(structure), remove_none=True
    )

    material_data = {
        "name": structure.formula,
        "basis": basis,
        "lattice": lattice,
        "isNonPeriodic": not structure.is_ordered,
        "_id": "",
        "metadata": metadata,
        "isUpdated": True,
    }

    return material_data


def to_poscar(material_or_material_data: Union[Material, Dict[str, Any]]) -> str:
    """
    Converts material object in ESSE format to a POSCAR string.

    Args:
        material_or_material_data (dict|class): A dictionary containing the material information in ESSE format.

    Returns:
        str: A POSCAR string.
    """
    structure = to_pymatgen(material_or_material_data)
    poscar = PymatgenPoscar(structure)
    # For pymatgen `2023.6.23` supporting py3.8 the method name is "get_string"
    # TODO: cleanup the if statement when dropping support for py3.8
    if hasattr(poscar, "get_string"):
        return poscar.get_string()
    return poscar.get_str()


def clean_qe_input(poscar):
    return remove_comments_from_source_code(remove_comments_from_source_code(poscar, "fortran"), "python")


def from_poscar(poscar: str) -> Dict[str, Any]:
    """
    Converts a POSCAR string to a material object in ESSE format.

    Args:
        poscar (str): A POSCAR string.

    Returns:
        dict: A dictionary containing the material information in ESSE format.
    """
    poscar_clean = clean_qe_input(poscar)
    structure = PymatgenStructure.from_str(poscar_clean, "poscar")
    return from_pymatgen(structure)


def from_poscar_molecule(poscar: str) -> Dict[str, Any]:
    """
    Converts a molecule POSCAR string to a non-periodic ESSE material.
    """
    poscar_clean = clean_qe_input(poscar)
    structure = PymatgenStructure.from_str(poscar_clean, "poscar")
    ase_atoms = PymatgenAseAtomsAdaptor.get_atoms(structure)
    ase_atoms.set_pbc(False)
    return from_ase(ase_atoms)


def to_ase(material_or_material_data: Union[Material, Dict[str, Any]]) -> ASEAtoms:
    """
    Converts material object in ESSE format to an ASE Atoms object.

    Args:
        material_or_material_data (dict|class): A dictionary containing the material information in ESSE format.

    Returns:
        Any: An ASE Atoms object.
    """
    if isinstance(material_or_material_data, Material):
        material_config = material_or_material_data.to_dict()
    else:
        material_config = material_or_material_data
    structure = to_pymatgen(material_config)
    atoms = PymatgenAseAtomsAdaptor.get_atoms(structure)

    atomic_labels = material_config["basis"].get("labels", [])
    if atomic_labels:
        atoms.set_tags(map_array_with_id_value_to_array(atomic_labels))
    if "metadata" in material_config:
        atoms.info.update({"metadata": material_config["metadata"]})

    atoms.info.update({"name": material_config["name"]})
    return atoms


def from_ase(ase_atoms: ASEAtoms) -> Dict[str, Any]:
    """
    Converts an ASE Atoms object to a material object in ESSE format.

    Args:
        ase_atoms (Atoms): An ASE Atoms object.

    Returns:
        dict: A dictionary containing the material information in ESSE format.
    """
    is_molecule = not any(ase_atoms.pbc)

    if is_molecule:
        lattice_vectors = calculate_padded_cell_simple_cubic(ase_atoms.get_positions())
        ase_atoms.set_cell(lattice_vectors)
        ase_atoms.center()

    # TODO: check that atomic labels/tags are properly handled
    structure = PymatgenAseAtomsAdaptor.get_structure(ase_atoms)

    material = from_pymatgen(structure)
    material["isNonPeriodic"] = is_molecule
    if is_molecule:
        material["lattice"]["type"] = "CUB"

    ase_tags = extract_tags_from_ase_atoms(ase_atoms)
    material["basis"]["labels"] = ase_tags
    ase_metadata = ase_atoms.info.get("metadata", {})
    if ase_metadata:
        material["metadata"].update(ase_metadata)
    material["name"] = ase_atoms.info.get("name", ase_atoms.get_chemical_formula())
    return material


def decorator_convert_material_args_kwargs_to_atoms(func: Callable) -> Callable:
    """
    Decorator that converts ESSE Material objects to ASE Atoms objects.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Convert args if they are of type ESSE Material
        new_args = [to_ase(arg) if isinstance(arg, Material) else arg for arg in args]

        # Convert kwargs if they are of type ESSE Material
        new_kwargs = {k: to_ase(v) if isinstance(v, Material) else v for k, v in kwargs.items()}

        # Call the original function with the converted arguments
        return func(*new_args, **new_kwargs)

    return wrapper


def decorator_convert_material_args_kwargs_to_structure(func: Callable) -> Callable:
    """
    Decorator that converts ESSE Material objects to pymatgen Structure objects.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Convert args if they are of type ESSE Material
        new_args = [to_pymatgen(arg) if isinstance(arg, Material) else arg for arg in args]

        # Convert kwargs if they are of type ESSE Material
        new_kwargs = {k: to_pymatgen(v) if isinstance(v, Material) else v for k, v in kwargs.items()}

        # Call the original function with the converted arguments
        return func(*new_args, **new_kwargs)

    return wrapper


def convert_atoms_or_structure_to_material(item):
    if isinstance(item, PymatgenStructure):
        return from_pymatgen(item)
    elif isinstance(item, ASEAtoms):
        return from_ase(item)
    return item
