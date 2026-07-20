import numpy as np
import pytest
from mat3ra.made.material import Material, defaultMaterialConfig
from mat3ra.made.tools.analyze.crystal_site.adatom_crystal_site_material_analyzer import (
    AdatomCrystalSiteMaterialAnalyzer,
)
from mat3ra.made.tools.analyze.crystal_site.adatom_material_analyzer import AdatomMaterialAnalyzer
from mat3ra.made.tools.analyze.crystal_site.crystal_site_analyzer import CrystalSiteAnalyzer
from mat3ra.made.tools.analyze.crystal_site.voronoi_crystal_site_analyzer import VoronoiCrystalSiteAnalyzer
from mat3ra.made.tools.analyze.other import (
    SurfaceTypesEnum,
    get_average_interlayer_distance,
    get_surface_area,
    get_surface_atom_indices,
)
from mat3ra.made.tools.analyze.rdf import RadialDistributionFunction
from mat3ra.made.tools.analyze.utils import calculate_von_mises_strain
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.defective_structures.zero_dimensional.point_defect.atom_placement_method_enum import (
    AtomPlacementMethodEnum,
)
from mat3ra.made.tools.build_components.operations.core.combinations.enums import AdatomPlacementMethodEnum
from unit.fixtures.nanoribbon.nanoribbon import GRAPHENE_ZIGZAG_NANORIBBON
from unit.utils import OSPlatform, get_platform_specific_value

from .fixtures.bulk import BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVE
from .fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE
from .fixtures.slab import SI_CONVENTIONAL_SLAB_001

COMPARISON_PRECISION = 1e-4


@pytest.mark.parametrize(
    "material_config, layer_indices, expected_distance",
    [
        (GRAPHENE_NICKEL_INTERFACE, [0, 1], 3.0),
    ],
)
def test_calculate_average_interlayer_distance(material_config, layer_indices, expected_distance):
    material = Material.create(material_config)
    distance = get_average_interlayer_distance(material, *layer_indices)
    assert np.isclose(distance, expected_distance)


@pytest.mark.parametrize(
    "material_config, expected_area",
    [
        (defaultMaterialConfig, 12.950),
    ],
)
def test_calculate_surface_area(material_config, expected_area):
    material = Material.create(material_config)
    area = get_surface_area(material)
    assert np.isclose(area, expected_area, atol=1e-3)


@pytest.mark.parametrize(
    "material_config, rdf_params, expected_first_peak_distance",
    [
        (GRAPHENE_ZIGZAG_NANORIBBON, {"cutoff": 10.0, "bin_size": 0.1}, 1.42),
        (BULK_Si_CONVENTIONAL, {"cutoff": 10.0, "bin_size": 0.1}, 2.35),
    ],
)
def test_radial_distribution_function(material_config, rdf_params, expected_first_peak_distance):
    material = Material.create(material_config)

    rdf = RadialDistributionFunction.from_material(material, **rdf_params)

    # Test that RDF is non-negative
    assert np.all(rdf.rdf >= 0), "RDF contains negative values."

    # Test the first peak properties
    assert rdf.first_peak_index > 0, "First peak index should be greater than 0."
    assert rdf.first_peak_value > 0, "First peak value should be greater than 0."
    assert rdf.first_peak_width > 0, "First peak width should be greater than 0."
    assert rdf.first_peak_distance > 0, "First peak distance should be greater than 0."

    # Test that `is_within_first_peak` works as expected
    assert rdf.is_within_first_peak(rdf.first_peak_distance), "First peak distance should be within the first peak."
    assert not rdf.is_within_first_peak(0), "Zero distance should not be within the first peak."
    assert not rdf.is_within_first_peak(rdf_params["cutoff"]), "Cutoff distance should not be within the first peak."

    # Test that RDF drops to zero near the cutoff
    assert np.isclose(rdf.rdf[-1], 0, atol=1e-2), "RDF should approach zero near the cutoff."

    # Specific material related tests
    assert np.isclose(rdf.first_peak_distance, expected_first_peak_distance, atol=0.1)


VORONOI_SITE_EXPECTED = {OSPlatform.DARWIN: [0.625, 0.625, 0.125], OSPlatform.OTHER: [0.5, 0.5, 0.5]}


@pytest.mark.parametrize(
    "placement_method, coordinate, expected_coordinate",
    [
        (AtomPlacementMethodEnum.EXACT_COORDINATE, [0.25, 0.25, 0.5], [0.25, 0.25, 0.5]),
        (AtomPlacementMethodEnum.CLOSEST_SITE, [0.25, 0.25, 0.5], [0.25, 0.25, 0.25]),
        (AtomPlacementMethodEnum.EQUIDISTANT, [0.5432, 0.5123, 0.5], [0.58333, 0.58333, 0.25]),
        (AtomPlacementMethodEnum.VORONOI_SITE, [0.25, 0.25, 0.5], VORONOI_SITE_EXPECTED),
    ],
)
def test_crystal_site_analyzer(placement_method, coordinate, expected_coordinate):
    crystal = Material.create(BULK_Si_PRIMITIVE)

    if placement_method == AtomPlacementMethodEnum.VORONOI_SITE:
        analyzer = VoronoiCrystalSiteAnalyzer(material=crystal, coordinate=coordinate)
        final_coordinate = analyzer.voronoi_site_coordinate
        expected_coordinate = get_platform_specific_value(expected_coordinate)
    else:
        analyzer = CrystalSiteAnalyzer(material=crystal, coordinate=coordinate)
        if placement_method == AtomPlacementMethodEnum.EXACT_COORDINATE:
            final_coordinate = analyzer.exact_coordinate
        elif placement_method == AtomPlacementMethodEnum.CLOSEST_SITE:
            final_coordinate = analyzer.closest_site_coordinate
        elif placement_method == AtomPlacementMethodEnum.EQUIDISTANT:
            final_coordinate = analyzer.get_equidistant_coordinate()
        else:
            raise ValueError(f"Unknown method: {placement_method}")

    if placement_method == AtomPlacementMethodEnum.VORONOI_SITE:
        allowed_coords = [[0.625, 0.625, 0.125], [0.625, 0.625, 0.625], [0.5, 0.5, 0.5]]
        assert any(
            np.allclose(final_coordinate, allowed, atol=COMPARISON_PRECISION) for allowed in allowed_coords
        ), f"Voronoi coordinate {final_coordinate} not in allowed list"
    else:
        assert np.allclose(final_coordinate, expected_coordinate, atol=COMPARISON_PRECISION)


@pytest.mark.parametrize(
    "material_config, coordinate, placement_method, distance_z, element, expected_coordinate",
    [
        (
            SI_CONVENTIONAL_SLAB_001,
            [0.25, 0.25],
            AdatomPlacementMethodEnum.EXACT_COORDINATE,
            1.0,
            "Si",
            [0.25, 0.25, 0.1828],
        ),
    ],
)
def test_adatom_material_analyzer(
    material_config, coordinate, placement_method, distance_z, element, expected_coordinate
):
    crystal = MaterialWithBuildMetadata.create(material_config)

    analyzer = AdatomMaterialAnalyzer(
        material=crystal, coordinate_2d=coordinate, distance_z=distance_z, element=element
    )
    resolved_coord = analyzer.coordinate_in_added_component

    assert np.allclose(resolved_coord, expected_coordinate, atol=COMPARISON_PRECISION)


@pytest.mark.parametrize(
    "material_config, coordinate, placement_method, distance_z, element,expected_coordinate",
    [
        (
            SI_CONVENTIONAL_SLAB_001,
            [0.25, 0.25],
            AdatomPlacementMethodEnum.NEW_CRYSTAL_SITE,
            1.0,
            "Si",
            [0.25, 0.25, 0.5],
        ),
    ],
)
def test_adatom_crystal_site_material_analyzer(
    material_config, coordinate, placement_method, distance_z, element, expected_coordinate
):
    crystal = MaterialWithBuildMetadata.create(material_config)

    # Test NEW_CRYSTAL_SITE method
    analyzer = AdatomCrystalSiteMaterialAnalyzer(
        material=crystal,
        coordinate_2d=coordinate,
        distance_z=distance_z,
        element=element,
    )
    resolved_coord = analyzer.coordinate_in_added_component

    assert np.allclose(resolved_coord, expected_coordinate, atol=COMPARISON_PRECISION)


@pytest.mark.parametrize(
    "material_config, expected_indices_top, expected_indices_bottom",
    [
        (
            SI_CONVENTIONAL_SLAB_001,
            [8, 14],
            [3, 4, 5],
        ),
    ],
)
def test_get_surface_atom_indices_top_and_bottom(material_config, expected_indices_top, expected_indices_bottom):
    material = Material.create(material_config)
    top_indices = get_surface_atom_indices(material, SurfaceTypesEnum.TOP)
    bottom_indices = get_surface_atom_indices(material, SurfaceTypesEnum.BOTTOM)
    assert set(top_indices) == set(expected_indices_top)
    assert set(bottom_indices) == set(expected_indices_bottom)


@pytest.mark.parametrize(
    "strain_matrix, expected_strain",
    [
        # Identity matrix - no strain
        ([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 0.0),
        # Uniaxial compression (5% x only)
        ([[0.95, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 4.875),
        # Biaxial compression (5% x and y)
        ([[0.95, 0.0, 0.0], [0.0, 0.95, 0.0], [0.0, 0.0, 1.0]], 4.875),
        # Shear strain
        ([[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 8.675),
    ],
)
def test_calculate_von_mises_strain(strain_matrix, expected_strain):
    """Test von Mises strain calculation used in ZSL interface analysis."""
    strain_percentage = calculate_von_mises_strain(np.array(strain_matrix))
    assert np.isclose(strain_percentage, expected_strain, atol=0.01)
