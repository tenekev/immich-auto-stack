from faker import Faker
import pytest
from unittest.mock import ANY

from immich_auto_stack import stratifyStack


def asset_factory(extensions):
    file_list = [f"foo.{ext}" for ext in extensions]
    return [{"originalFileName": file} for file in file_list]


@pytest.mark.parametrize(
    "extensions",
    [
        ["jpg"],
        ["rw2"],
        ["jpg", "rw2"],
        ["jpg", "jpeg"],
        ["png", "raw", "cr2", "xmp"],
        ["png", "jpg", "png", "png"],
    ],
)
def test_stratifyStack_returns_list_with_same_length_as_input(extensions):
    # Arrange
    file_list = asset_factory(extensions)
    assert len(file_list) > 0

    # Act
    result = stratifyStack(file_list)

    # Assert
    assert len(result) == len(file_list)


@pytest.mark.parametrize(
    "extensions,expected_first_ext",
    [
        (["rw2", "jpeg"], "jpeg"),
        (["rw2"], "rw2"),
        (["png", "raw", "cr2", "xmp"], "png"),
        (["raw", "cr2", "xmp", "jpg"], "jpg"),
    ],
)
def test_stratifyStack_puts_single_parent_at_front(extensions, expected_first_ext):
    # Arrange
    file_list = asset_factory(extensions)
    expected_first_file = f"foo.{expected_first_ext}"

    # Act
    result = stratifyStack(file_list)

    # Assert
    assert result[0]["originalFileName"] == expected_first_file


@pytest.mark.parametrize(
    "extensions,expected_parents",
    [
        (["jpg", "jpeg"], ["jpeg", "jpg"]),
        (["png", "raw", "cr2", "xmp", "jpg"], ["jpg", "png"]),
        (["png", "jpg", "png", "png"], ["jpg", "png", "png", "png"]),
    ],
)
def test_stratifyStack_handles_multiple_parents(extensions, expected_parents):
    # Arrange
    file_list = asset_factory(extensions)
    expected_parents_list = asset_factory(expected_parents)

    # Act
    result = stratifyStack(file_list)
    result_parents = result[: len(expected_parents_list)]

    # Assert
    assert result_parents == expected_parents_list
