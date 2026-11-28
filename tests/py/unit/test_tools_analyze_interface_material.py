from typing import Final, Type

import pytest
from mat3ra.made.tools.analyze.build_metadata_analyzer import BuildMetadataAnalyzer
from mat3ra.made.tools.analyze.build_metadata_analyzer_factory import create_build_metadata_analyzer
from mat3ra.made.tools.analyze.interface_material import (
    InterfaceMaterialAnalyzer,
    create_interface_bulk_cell,
    get_interface_bulk_crystal,
    get_interface_configuration,
)
from mat3ra.made.tools.analyze.slab import SlabMaterialAnalyzer
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface import InterfaceConfiguration
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.helpers import create_interface_simple
from unit.fixtures.bulk import BULK_Ge_CONVENTIONAL, BULK_Si_CONVENTIONAL
from unit.fixtures.interface.zsl import (
    GRAPHENE_NICKEL_INTERFACE,
    GRAPHENE_NICKEL_INTERFACE_SUBSTRATE_BULK_CELL,
    SILICON_GERMANIUM_INTERFACE_111_FILM_BULK_CELL,
)
from unit.fixtures.slab import SI_CONVENTIONAL_SLAB_001
from unit.utils import assert_two_entities_deep_almost_equal

INTERFACE_MATERIAL: Final = MaterialWithBuildMetadata.create(GRAPHENE_NICKEL_INTERFACE)
SLAB_MATERIAL: Final = MaterialWithBuildMetadata.create(SI_CONVENTIONAL_SLAB_001)
SILICON_GERMANIUM_INTERFACE_111: Final = create_interface_simple(
    MaterialWithBuildMetadata.create(BULK_Si_CONVENTIONAL),
    MaterialWithBuildMetadata.create(BULK_Ge_CONVENTIONAL),
    (1, 1, 1),
    (1, 1, 1),
    1,
    1,
    gap=None,
    vacuum=0.0,
)
SUBSTRATE_CRYSTAL_NAME: Final = "Ni, Nickel, FCC (Fm-3m) 3D (Bulk), mp-23"
FILM_CRYSTAL_NAME: Final = "Graphene"

GET_BULK_CRYSTAL_CASES = [
    ("substrate", SUBSTRATE_CRYSTAL_NAME),
    ("film", FILM_CRYSTAL_NAME),
]

CREATE_INTERFACE_BULK_CELL_CASES = [
    (INTERFACE_MATERIAL, InterfacePartsEnum.SUBSTRATE, GRAPHENE_NICKEL_INTERFACE_SUBSTRATE_BULK_CELL),
    (SILICON_GERMANIUM_INTERFACE_111, InterfacePartsEnum.FILM, SILICON_GERMANIUM_INTERFACE_111_FILM_BULK_CELL),
]

CREATE_BUILD_METADATA_ANALYZER_CASES = [
    (INTERFACE_MATERIAL, InterfaceMaterialAnalyzer),
    (SLAB_MATERIAL, SlabMaterialAnalyzer),
]


def test_build_configuration():
    configuration = InterfaceMaterialAnalyzer(material=INTERFACE_MATERIAL).build_configuration
    assert isinstance(configuration, InterfaceConfiguration)
    assert configuration.type == "InterfaceConfiguration"


@pytest.mark.parametrize("part,expected_name", GET_BULK_CRYSTAL_CASES)
def test_get_bulk_crystal(part, expected_name):
    crystal = InterfaceMaterialAnalyzer(material=INTERFACE_MATERIAL).get_bulk_crystal(part=part)
    assert crystal["name"] == expected_name


def test_get_interface_configuration():
    configuration = get_interface_configuration(INTERFACE_MATERIAL)
    assert isinstance(configuration, InterfaceConfiguration)
    assert configuration.type == "InterfaceConfiguration"


@pytest.mark.parametrize("part,expected_name", GET_BULK_CRYSTAL_CASES)
def test_get_interface_bulk_crystal(part, expected_name):
    crystal = get_interface_bulk_crystal(INTERFACE_MATERIAL, part=part)
    assert crystal["name"] == expected_name


@pytest.mark.parametrize("material,expected_analyzer_cls", CREATE_BUILD_METADATA_ANALYZER_CASES)
def test_create_build_metadata_analyzer(
    material: MaterialWithBuildMetadata,
    expected_analyzer_cls: Type[BuildMetadataAnalyzer],
):
    analyzer = create_build_metadata_analyzer(material)
    assert isinstance(analyzer, expected_analyzer_cls)


@pytest.mark.parametrize("interface,part,expected_cell", CREATE_INTERFACE_BULK_CELL_CASES)
def test_create_interface_bulk_cell(interface, part, expected_cell):
    bulk_cell = create_interface_bulk_cell(interface, part)
    assert_two_entities_deep_almost_equal(bulk_cell, expected_cell)
