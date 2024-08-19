import pytest
import sys
from unittest.mock import patch

from immich_auto_stack import parse_arguments


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (None, True),  # The default value
        ("True", True),
        ("true", True),
        ("yes", True),
        ("1", True),
        ("False", False),
        ("false", False),
        ("no", False),
        ("0", False),
    ],
)
def test_skip_previous_input_value_maps_to_expected_boolean(
    input_value, expected_value
):
    # Arrange
    testargs = ["immich_auto_stack.py"]
    if input_value:
        testargs += ["--skip_previous", input_value]

    # Act
    with patch.object(sys, "argv", testargs):
        args = parse_arguments()

    # Assert
    assert args.skip_previous is expected_value
