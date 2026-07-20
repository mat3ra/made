import pytest
from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.basis import BasisMaterialAnalyzer
from mat3ra.made.tools.analyze.fingerprint import LayeredFingerprintAlongAxis
from mat3ra.made.tools.operations.core.unary import supercell

from .fixtures.bulk import BULK_Si_CONVENTIONAL
from .fixtures.slab import SI_CONVENTIONAL_SLAB_001, SLAB_SrTiO3_011_TERMINATION_O2, SLAB_SrTiO3_011_TERMINATION_SrTiO


@pytest.mark.parametrize(
    "material_config",
    [SLAB_SrTiO3_011_TERMINATION_O2, SLAB_SrTiO3_011_TERMINATION_SrTiO, SI_CONVENTIONAL_SLAB_001],
)
def test_basis_analyzer_fingerprint(material_config):
    material = Material.create(material_config)
    analyzer = BasisMaterialAnalyzer(material=material)

    fingerprint = analyzer.get_layer_fingerprint(layer_thickness=1.0)
    assert isinstance(fingerprint, LayeredFingerprintAlongAxis)
    assert len(fingerprint.layers) > 0
    assert fingerprint.axis == AxisEnum.z
    assert fingerprint.layer_thickness == 1.0

    for layer in fingerprint.layers:
        assert hasattr(layer, "min_coord")
        assert hasattr(layer, "max_coord")
        assert hasattr(layer, "elements")
        assert isinstance(layer.min_coord, float)
        assert isinstance(layer.max_coord, float)
        assert layer.max_coord > layer.min_coord
        assert isinstance(layer.elements, list)
        assert all(isinstance(elem, str) for elem in layer.elements)

    non_empty_layers = fingerprint.non_empty_layers
    assert isinstance(non_empty_layers, list)
    assert all(isinstance(layer, type(fingerprint.layers[0])) for layer in non_empty_layers)

    element_sequence = fingerprint.element_sequence
    assert isinstance(element_sequence, list)
    assert all(isinstance(elements, list) for elements in element_sequence)


@pytest.mark.parametrize(
    "material_config, layer_thickness",
    [
        (BULK_Si_CONVENTIONAL, 1.0),
        (SI_CONVENTIONAL_SLAB_001, 1.0),
        (SLAB_SrTiO3_011_TERMINATION_O2, 0.5),
    ],
)
def test_get_layer_fingerprint(material_config, layer_thickness):
    material = Material.create(material_config)
    analyzer = BasisMaterialAnalyzer(material=material)

    fingerprint = analyzer.get_layer_fingerprint(layer_thickness=layer_thickness)
    assert isinstance(fingerprint, LayeredFingerprintAlongAxis)
    assert len(fingerprint.layers) > 0
    assert fingerprint.axis == AxisEnum.z
    assert fingerprint.layer_thickness == layer_thickness

    for axis in [AxisEnum.x, AxisEnum.y, AxisEnum.z]:
        fingerprint = analyzer.get_layer_fingerprint(layer_thickness=layer_thickness, axis=axis)
        assert isinstance(fingerprint, LayeredFingerprintAlongAxis)
        assert fingerprint.axis == axis
        assert fingerprint.layer_thickness == layer_thickness
        assert len(fingerprint.layers) > 0


@pytest.mark.parametrize(
    "material_config, supercell_matrix, repetition_axis",
    [
        (SLAB_SrTiO3_011_TERMINATION_O2, [[2, 0, 0], [0, 2, 0], [0, 0, 1]], AxisEnum.y),
        (SLAB_SrTiO3_011_TERMINATION_SrTiO, [[2, 0, 0], [0, 2, 0], [0, 0, 1]], AxisEnum.y),
        (SI_CONVENTIONAL_SLAB_001, [[2, 0, 0], [0, 2, 0], [0, 0, 1]], AxisEnum.x),
    ],
)
def test_fingerprint_similarity_scores(material_config, supercell_matrix, repetition_axis):
    slab = Material.create(material_config)
    supercell_material = supercell(slab, supercell_matrix)

    analyzer_slab = BasisMaterialAnalyzer(material=slab)
    analyzer_supercell = BasisMaterialAnalyzer(material=supercell_material)

    layer_thickness = 1.0

    fingerprint_slab = analyzer_slab.get_layer_fingerprint(layer_thickness=layer_thickness, axis=repetition_axis)
    fingerprint_supercell = analyzer_supercell.get_layer_fingerprint(
        layer_thickness=layer_thickness, axis=repetition_axis
    )

    assert fingerprint_slab.get_similarity_score(fingerprint_supercell) == 0.0

    score_periodic = fingerprint_slab.get_similarity_score_ignore_periodicity(fingerprint_supercell)
    assert score_periodic > 0.0
    assert len(fingerprint_supercell.layers) % len(fingerprint_slab.layers) == 0

    assert fingerprint_supercell.get_similarity_score_ignore_periodicity(fingerprint_slab) > 0.0

    fingerprint_slab_z = analyzer_slab.get_layer_fingerprint(layer_thickness=layer_thickness, axis=AxisEnum.z)
    fingerprint_supercell_z = analyzer_supercell.get_layer_fingerprint(layer_thickness=layer_thickness, axis=AxisEnum.z)

    assert len(fingerprint_slab_z.layers) == len(fingerprint_supercell_z.layers)
    assert fingerprint_slab_z.get_similarity_score(fingerprint_supercell_z) == 1.0
