import pytest
from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.made.tools.build_components.metadata import BuildMetadata, MaterialBuildMetadata


class ConfigWithToDict(InMemoryEntityPydantic):
    value: str = "test_dict"


class ConfigWithToJsonReturnsStr(InMemoryEntityPydantic):
    value: str = "test_json_str"


class MockParameters(InMemoryEntityPydantic):
    param: str = "param_value"


def test_metadata_initialization_with_data():
    initial_data = {"existing_key": "existing_value", "build": [{"configuration": {"initial": "config"}}]}
    metadata = MaterialBuildMetadata(**initial_data)

    assert metadata.existing_key == "existing_value"
    assert metadata.build[-1].configuration["initial"] == "config"


def test_metadata_empty_initialization():
    metadata = MaterialBuildMetadata()
    assert metadata.model_dump(exclude_none=True) == {"build": []}


def test_get_latest_build_metadata():
    metadata = MaterialBuildMetadata(build=[BuildMetadata(configuration={"type": "SlabConfiguration"})])
    assert metadata.get_latest_build_metadata().configuration["type"] == "SlabConfiguration"


def test_get_latest_build_metadata_raises_when_empty():
    with pytest.raises(ValueError, match="No metadata.build"):
        MaterialBuildMetadata().get_latest_build_metadata()


@pytest.mark.parametrize(
    "config_object, expected_dict",
    [
        (ConfigWithToDict(), {"value": "test_dict"}),
        (ConfigWithToJsonReturnsStr(), {"value": "test_json_str"}),
    ],
)
def test_build_metadata_update(config_object, expected_dict):
    build_metadata = BuildMetadata()

    build_metadata.update(configuration=config_object)
    assert build_metadata.configuration == expected_dict

    build_metadata.configuration = {}
    build_metadata.update(build_parameters=config_object)
    assert build_metadata.build_parameters == expected_dict


def test_full_lifecycle_and_serialization():
    # Initialize with some existing data
    metadata = MaterialBuildMetadata(existing_key="previous_material_metadata_value")

    # Update with a 'to_dict' config
    config = ConfigWithToDict(value="config_value")
    params = MockParameters(param="param_value")
    metadata.build.append(BuildMetadata(configuration=config, build_parameters=params))

    # Check the final state before serialization
    assert metadata.existing_key == "previous_material_metadata_value"
    assert metadata.build[-1].configuration["value"] == "config_value"
    assert metadata.build[-1].build_parameters["param"] == "param_value"

    # Check the final serialized dict
    final_dict = metadata.model_dump()
    expected_dict = {
        "existing_key": "previous_material_metadata_value",
        "build": [{"configuration": {"value": "config_value"}, "build_parameters": {"param": "param_value"}}],
    }
    assert final_dict == expected_dict
