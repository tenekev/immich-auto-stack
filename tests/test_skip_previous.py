import pytest
from unittest.mock import patch, Mock

from immich_auto_stack import main


@pytest.mark.parametrize(
    "args_skip_previous,expected_call_count",
    [
        (True, 0),
        (False, 1),
    ],
)
@patch("immich_auto_stack.stratifyStack")
@patch("immich_auto_stack.stackBy")
@patch("immich_auto_stack.Immich")
@patch("immich_auto_stack.parse_arguments")
def test_skip_previous_skips_modifyAssets_when_true(
    mock_parse_arguments,
    mock_immich_class,
    mock_stackBy,
    mock_stratifyStack,
    args_skip_previous,
    expected_call_count,
):
    # Arrange
    # mock the function calls within main() to create predictable scenarios
    mock_parse_arguments.return_value = Mock(
        api_key="123", api_url="456", skip_previous=args_skip_previous
    )
    mock_stackBy.return_value = [
        (
            "dummy_key",
            [
                {"id": "parent", "stackCount": None, "originalFileName": "foo.jpg"},
                {
                    "id": "child",
                    "stackCount": "not none",
                    "originalFileName": "foo.png",
                },
            ],
        )
    ]
    mock_stratifyStack.side_effect = lambda x: x  # Return the same value passed in

    # Act
    main()

    # Assert
    assert mock_immich_class().modifyAssets.call_count == expected_call_count
