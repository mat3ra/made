from __future__ import annotations

from typing import Generic, Type, TypeVar

from ..build_components.metadata import BuildMetadata, MaterialWithBuildMetadata
from . import BaseMaterialAnalyzer

TypeConfiguration = TypeVar("TypeConfiguration")
TypeBuildParameters = TypeVar("TypeBuildParameters")


class BuildMetadataAnalyzer(BaseMaterialAnalyzer, Generic[TypeConfiguration, TypeBuildParameters]):
    material: MaterialWithBuildMetadata
    configuration_cls: Type[TypeConfiguration]
    build_parameters_cls: Type[TypeBuildParameters]

    @property
    def build_metadata(self) -> BuildMetadata:
        if not self.material.metadata.build:
            raise ValueError("No metadata.build on the material.")
        metadata = self.material.metadata.get_build_metadata_of_type(self.configuration_cls.__name__)
        if not metadata:
            raise ValueError(f"Build metadata for {self.configuration_cls.__name__} not found.")
        return metadata

    @property
    def build_configuration(self) -> TypeConfiguration:
        return self.configuration_cls(**self.build_metadata.configuration)

    @property
    def build_parameters(self) -> TypeBuildParameters:
        return self.build_parameters_cls(**self.build_metadata.build_parameters)
