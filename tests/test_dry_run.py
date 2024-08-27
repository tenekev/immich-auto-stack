import os
import pytest
from unittest.mock import patch, Mock

from immich_auto_stack import main


@pytest.mark.parametrize(
    "dry_run_env_var,expected_call_count",
    [
        ("True", 0),
        ("true", 0),
        ("yes", 0),
        ("False", 1),
        ("no", 1),
        ("0", 1),
        ("", 1),
        (None, 1),
    ],
)
@patch("immich_auto_stack.stratifyStack")
@patch("immich_auto_stack.stackBy")
@patch("immich_auto_stack.Immich")
def test_main_applies_dry_run_env_var_to_skip_modifyAssets(
    mock_immich_class,
    mock_stackBy,
    mock_stratifyStack,
    dry_run_env_var,
    expected_call_count,
):
    # Arrange
    # mock the function calls within main() to create predictable scenarios
    mock_stackBy.return_value = [
        (
            "dummy_key",
            [
                {"id": "parent", "originalFileName": "foo.jpg"},
                {
                    "id": "child",
                    "originalFileName": "foo.png",
                },
            ],
        )
    ]
    mock_stratifyStack.side_effect = lambda x: x  # Return the same value passed in
    test_environ = {
        "API_KEY": "123",
        "API_URL": "456",
    }
    if dry_run_env_var is not None:
        test_environ["DRY_RUN"] = dry_run_env_var

    # Act
    with patch.dict(os.environ, test_environ):
        main()

    # Assert
    assert mock_immich_class().modifyAssets.call_count == expected_call_count
