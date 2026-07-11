from typing import Dict, Type

from ..build_components.metadata import MaterialWithBuildMetadata
from .build_metadata_analyzer import BuildMetadataAnalyzer
from .interface_material import (
    InterfaceMaterialAnalyzer,
)
from .slab import SlabMaterialAnalyzer

BUILD_METADATA_ANALYZER_REGISTRY: Dict[str, Type[BuildMetadataAnalyzer]] = {
    "SlabConfiguration": SlabMaterialAnalyzer,
    "InterfaceConfiguration": InterfaceMaterialAnalyzer,
}


def create_build_metadata_analyzer(
    material: MaterialWithBuildMetadata,
    **analyzer_kwargs,
) -> BuildMetadataAnalyzer:
    build_metadata = material.metadata.get_latest_build_metadata()
    configuration_type = build_metadata.configuration.get("type")
    if not configuration_type:
        raise ValueError("Latest build step has no configuration type.")
    analyzer_cls = BUILD_METADATA_ANALYZER_REGISTRY.get(configuration_type)
    if analyzer_cls is None:
        registered_types = ", ".join(sorted(BUILD_METADATA_ANALYZER_REGISTRY))
        raise ValueError(
            f"No build metadata analyzer registered for '{configuration_type}'. "
            f"Registered types: {registered_types}."
        )
    return analyzer_cls(material=material, **analyzer_kwargs)
