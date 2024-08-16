from datetime import timedelta
from faker import Faker
from itertools import groupby
import os
import pytest
from unittest.mock import patch

from immich_auto_stack import parent_criteria

fake = Faker()
static_datetime = fake.date_time()


def asset_factory(filename="IMG_1234.jpg"):
    return {
        "originalFileName": filename,
    }


@pytest.mark.parametrize(
    "input_order,expected_order",
    [
        [
            [
                "IMG_2482.xyz",
                "IMG_2482.XYZ",
                "IMG_2482.xyzz",
                "IMG_2482.xyz2",
                "IMG_2482x.xyz",
                "IMG_2482.zzz",
                "IMG_2482.ZZZ",
            ],
            [
                "IMG_2482.XYZ",
                "IMG_2482.ZZZ",
                "IMG_2482.xyz",
                "IMG_2482.xyz2",
                "IMG_2482.xyzz",
                "IMG_2482.zzz",
                "IMG_2482x.xyz",
            ],
        ],
        [
            [
                "IMG_2482_f.jpg",
                "IMG_2482_a.jpg",
                "IMG_2482_c.jpg",
                "IMG_2482_e.jpg",
                "IMG_2482_b.jpg",
                "IMG_2482_d.jpg",
            ],
            [
                "IMG_2482_a.jpg",
                "IMG_2482_b.jpg",
                "IMG_2482_c.jpg",
                "IMG_2482_d.jpg",
                "IMG_2482_e.jpg",
                "IMG_2482_f.jpg",
            ],
        ],
    ],
)
def test_parent_criteria_given_no_promote_override_sorts_alphabetically(input_order, expected_order):
    # Arrange
    asset_list = [asset_factory(f) for f in input_order]
    expected_order = [asset_factory(f) for f in expected_order]

    # Act
    result = sorted(asset_list, key=parent_criteria)

    # Assert
    assert result == expected_order


@pytest.mark.parametrize(
    "input_order,expected_order",
    [
        [
            [
                "IMG_2482.xyz",
                "IMG_2482.jpg",
                "IMG_2482.png",
                "IMG_2482.abc",
                "IMG_2482.jpeg",
            ],
            [
                "IMG_2482.jpeg",
                "IMG_2482.jpg",
                "IMG_2482.png",
                "IMG_2482.abc",
                "IMG_2482.xyz",
            ],
        ],
        [
            [
                "IMG_2482.abc",
                "IMG_2482.ABC",
                "IMG_2482.png",
                "IMG_2482.PNG",
                "IMG_2482.jpg",
                "IMG_2482.jpeg",
                "IMG_2482.JPG",
                "IMG_2482.JPEG",
            ],
            [
                "IMG_2482.JPEG",
                "IMG_2482.JPG",
                "IMG_2482.PNG",
                "IMG_2482.jpeg",
                "IMG_2482.jpg",
                "IMG_2482.png",
                "IMG_2482.ABC",
                "IMG_2482.abc",
            ],
        ],
        [
            [
                "IMG_2482.abc",
                "IMG_2482x.jpg",
                "IMG_2482a.png",
                "IMG_2482b.xyz",
            ],
            [
                "IMG_2482a.png",
                "IMG_2482x.jpg",
                "IMG_2482.abc",
                "IMG_2482b.xyz",
            ],
        ],
    ],
)
def test_parent_criteria_given_no_promote_override_prioritizes_jpg_jpeg_png(input_order, expected_order):
    # Arrange
    asset_list = [asset_factory(f) for f in input_order]
    expected_order = [asset_factory(f) for f in expected_order]

    # Act
    result = sorted(asset_list, key=parent_criteria)

    # Assert
    assert result == expected_order


@pytest.mark.parametrize(
    "input_order,promote_str,expected_order",
    [
        [
            [
                "testIMG_2482.xyz",
                "IMG_2482.jpg",
                "IMG_2482.test.png",
                "IMG_2482.abc",
                "IMG_2482.jpeg",
            ],
            "test",
            [
                "IMG_2482.test.png",
                "IMG_2482.jpeg",
                "IMG_2482.jpg",
                "testIMG_2482.xyz",
                "IMG_2482.abc",
            ],
        ],
        [
            [
                "IMG_2482.a",
                "IMG_2482.tesb",
                "IMG_2482tesT.c",
                "IMG_2482.d",
                "IMG_2482testtest.e",
                "IMG_2482foo_test.f",
                "IMG_2482.jpg",
            ],
            "test,foo",
            [
                "IMG_2482.jpg",
                "IMG_2482foo_test.f",
                "IMG_2482tesT.c",
                "IMG_2482testtest.e",
                "IMG_2482.a",
                "IMG_2482.d",
                "IMG_2482.tesb",
            ],
        ],
        [
            [
                "IMG_2482_abc.abc",
                "IMG_2482_foo.jpg",
                "IMG_2482_test_foo.jpg",
                "IMG_2482_test_foo.xyz",
            ],
            "test,foo",
            [
                "IMG_2482_test_foo.jpg",
                "IMG_2482_foo.jpg",
                "IMG_2482_test_foo.xyz",
                "IMG_2482_abc.abc",
            ],
        ],
        [
            [
                "IMG_2482_abc.abc",
                "IMG_2482_foo.jpg",
                "IMG_2482_test_foo.jpg",
                "IMG_2482_test_foo.xyz",
            ],
            "",
            [
                "IMG_2482_foo.jpg",
                "IMG_2482_test_foo.jpg",
                "IMG_2482_abc.abc",
                "IMG_2482_test_foo.xyz",
            ],
        ],
    ],
)
def test_parent_criteria_given_promote_override_prioritizes_promote_matches(input_order, promote_str, expected_order):
    # Arrange
    asset_list = [asset_factory(f) for f in input_order]
    expected_order = [asset_factory(f) for f in expected_order]

    # Act
    with patch.dict(os.environ, {"PARENT_PROMOTE": promote_str}):
        result = sorted(asset_list, key=parent_criteria)

    # Assert
    assert result == expected_order
