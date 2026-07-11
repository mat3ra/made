from typing import Final, Type

import pytest
from mat3ra.made.tools.analyze.build_metadata_analyzer import BuildMetadataAnalyzer
from mat3ra.made.tools.analyze.build_metadata_analyzer_factory import create_build_metadata_analyzer
from mat3ra.made.tools.analyze.interface_material import (
    InterfaceMaterialAnalyzer,
    get_interface_bulk_crystal,
    get_interface_configuration,
)
from mat3ra.made.tools.analyze.slab import SlabMaterialAnalyzer
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface import InterfaceConfiguration
from unit.fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE
from unit.fixtures.slab import SI_CONVENTIONAL_SLAB_001

INTERFACE_MATERIAL: Final = MaterialWithBuildMetadata.create(GRAPHENE_NICKEL_INTERFACE)
SLAB_MATERIAL: Final = MaterialWithBuildMetadata.create(SI_CONVENTIONAL_SLAB_001)
SUBSTRATE_CRYSTAL_NAME: Final = "Ni, Nickel, FCC (Fm-3m) 3D (Bulk), mp-23"
FILM_CRYSTAL_NAME: Final = "Graphene"

GET_BULK_CRYSTAL_CASES = [
    ("substrate", SUBSTRATE_CRYSTAL_NAME),
    ("film", FILM_CRYSTAL_NAME),
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
