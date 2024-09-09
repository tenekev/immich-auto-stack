from datetime import timedelta
from faker import Faker
from itertools import groupby
import os
import pytest
from unittest.mock import patch

from immich_auto_stack import apply_criteria

fake = Faker()
static_datetime = fake.date_time()


def asset_factory(filename="IMG_1234.jpg", date_time=static_datetime, **kwargs):
    return {
        "originalFileName": filename,
        "localDateTime": date_time,
        **kwargs
    }


@pytest.mark.parametrize(
    "file_list",
    [
        [
            "IMG_2482.jpg",
            "IMG_2482.jpg",  # same file, different folder
        ],
        [
            "IMG_2482.jpg",
            "IMG_2482.cr2",
        ],
        [
            "DSCF2482.JPG",
            "DSCF2482.RAF",
        ],
        [
            "IMG_7584.MOV",
            "IMG_7584.HEIC",
        ],
        [
            "foo_bar_biz_baz_buz.jpg",
            "foo_bar_biz_baz_buz.png",
        ],
    ],
)
def test_groupby_default_criteria_given_simple_matching_filenames_return_one_group(
    file_list,
):
    # Arrange
    asset_list = [asset_factory(f) for f in file_list]

    # Act
    result = [list(g) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == 1
    assert len(result[0]) == len(file_list)


@pytest.mark.parametrize(
    "file_list",
    [
        [
            "IMG_2482.jpg",
            "IMG_2483.cr2",
        ],
        [
            "IMG_2482.JPG",
            "IMG_2482_edit.JPG",
        ],
        [
            "foo_bar_biz_baz_buz.jpg",
            "bar_biz_baz_buz.png",
            "foo_bar_biz_baz.raw",
        ],
    ],
)
def test_groupby_default_criteria_given_simple_list_of_non_matching_filenames_return_multiple_groups(
    file_list,
):
    # Arrange
    asset_list = [asset_factory(f) for f in file_list]

    # Act
    result = [list(g) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == len(file_list)


@pytest.mark.parametrize(
    "file_list",
    [
        [
            "IMG_2482_crop_edit.jpg",
            "IMG_2482.jpg",
            "IMG_2482.cr2",
        ],
        [
            "IMG-2482_crop_edit.jpg",
            "IMG-2482.jpg",
            "IMG-2482.cr2",
        ],
        [
            "IMG_7584_edited.MOV",
            "IMG_7584_edited.HEIC",
            "IMG_7584.MOV",
            "IMG_7584.HEIC",
        ],
        [
            "IMG_3745-3747_stitch_vintage-3.jpg",
            "IMG_3745-3747_stitch_vintage.jpg",
            "IMG_3745-3747_stitch.psd",
            "IMG_3745-3747_stitch-4.jpg",
        ],
        ["IMG_3641_crop_vintage1234.jpg", "IMG_3641.JPG", "IMG_3641.CR2"],
        [
            "IMG_3594_crop2_vintage.jpg",
            "IMG_3594_crop_vintage.jpg",
            "IMG_3594_crop_vintage.psd",
            "IMG_3594.psd",
            "IMG_3594.JPG",
            "IMG_3594.CR2",
        ],
        [
            "IMG_1606-1608_mod2.jpg",
            "IMG_1606-1608_mod2_2.jpg",
            "IMG_1606-1608-hdr3-edit-edit.jpg",
            "IMG_1606-1608-hdr3-edit.tif",
        ],
        [
            "IMG_1606-Edit-edit.jpg",
            "IMG_1606-Edit.tif",
            "IMG_1606-HDR-Edit-edit.jpg",
            "IMG_1606-HDR.dng",
            "IMG_1606.CR2",
            "IMG_1606.JPG",
        ],
        [
            "IMG_4169_edit.jpg",
            "IMG_4169_edit-resized.jpg",
            "IMG_4169-edit2.jpg",
            "IMG_4169-edit2-resized.jpg",
            "IMG_4169.CR2",
            "IMG_4169.JPG",
        ],
        [
            "IMG_4153_edit (Medium).jpg",
            "IMG_4153.psd",
            "IMG_4153.JPG",
            "IMG_4153.CR2",
        ],
        [
            "IMG_2539-2540_crop_edit.jpg",
            "IMG_2539-2540_crop_edit.resized.jpg",
            "IMG_2539-2540.psd",
        ],
        [
            "DSCF3744-HDR-Pano-edit.jpg",
            "DSCF3744-HDR-Pano.dng",
            "DSCF3744-HDR.dng",
            "DSCF3744.JPG",
            "DSCF3744.RAF",
        ],
        [
            "DSCF2700-edit-12mp.jpg",
            "DSCF2700-edit.jpg",
            "DSCF2700.JPG",
            "DSCF2700.RAF",
        ],
        [
            "DSCF5278-Edit-edit-12mp.jpg",
            "DSCF5278-Edit.tif",
            "DSCF5278.RAF",
        ],
    ],
)
def test_groupby_custom_criteria_given_matching_filenames_return_one_group(file_list):
    # Arrange
    asset_list = [asset_factory(f) for f in file_list]
    # test_regex = r'([A-Z]+[-_]?[0-9]{4}([-_][0-9]{4})?)([\._-].*)?\.[\w]{3,4}$'
    test_criteria_json = r'[{"key": "originalFileName", "regex": {"key": "([A-Z]+[-_]?[0-9]{4}([-_][0-9]{4})?)([\\._-].*)?\\.[\\w]{3,4}$"}},{"key": "localDateTime"}]'

    # Act
    with patch.dict(os.environ, {"CRITERIA": test_criteria_json}):
        result = [list(g) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == 1
    assert len(result[0]) == len(file_list)


@pytest.mark.parametrize(
    "file_list",
    [
        [
            "IMG_2482_crop_edit.jpg",
            "IMG_2483_crop_edit.jpg",
        ],
        [
            "IMG_2488.jpg",
            "IMG-2488.jpg",
            "DSCF2488.jpg",
            "DSCF-2488.jpg",
            "DSCF_2488.jpg",
        ],
        [
            "IMG_2488-edit.jpg",
            "IMG-2488-edit.jpg",
            "DSCF2488-edit.jpg",
            "DSCF-2488-edit.jpg",
            "DSCF_2488-edit.jpg",
        ],
        [
            "IMG_1606-1608_mod2.jpg",
            "IMG_1606.jpg",
            "IMG_1608.jpg",
        ],
    ],
)
def test_groupby_custom_criteria_given_non_matching_filenames_return_multiple_groups(
    file_list,
):
    # Arrange
    asset_list = [asset_factory(f) for f in file_list]
    # test_regex = r'([A-Z]+[-_]?[0-9]{4}([-_][0-9]{4})?)([\._-].*)?\.[\w]{3,4}$'
    test_criteria_json = r'[{"key": "originalFileName", "regex": {"key": "([A-Z]+[-_]?[0-9]{4}([-_][0-9]{4})?)([\\._-].*)?\\.[\\w]{3,4}$"}},{"key": "localDateTime"}]'

    # Act
    with patch.dict(os.environ, {"CRITERIA": test_criteria_json}):
        result = [list(g) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == len(file_list)


def test_groupby_default_criteria_given_different_datetimes_return_multiple_groups():
    # Arrange
    test_datetime = fake.unique.date_time()
    asset_list = [
        asset_factory("IMG_1234.jpg", test_datetime),
        asset_factory("IMG_1234.jpg", test_datetime + timedelta(milliseconds=1)),
        asset_factory("IMG_1234.jpg", test_datetime - timedelta(milliseconds=1)),
    ]

    # Act
    result = [list(g) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == 3

@pytest.mark.parametrize(
    "criteria,kwargs,control_kwargs",
    [
        [
            # This scenario tests a single key with None value
            '[{"key": "thumbhash"}]',
            {"thumbhash": None},
            {"thumbhash": "foo"},
        ],
        [
            # This scenario tests multiple keys where only one is None
            '[{"key": "thumbhash"},{"key": "other_metadata"}]',
            {"thumbhash": None, "other_metadata": "foo"},
            {"thumbhash": "foo", "other_metadata": "foo"},
        ],
        [
            # This scenario tests multiple keys where all are None
            '[{"key": "thumbhash"},{"key": "other_metadata"}]',
            {"thumbhash": None, "other_metadata": None},
            {"thumbhash": "foo", "other_metadata": "foo"},
        ],
        [
            # This scenario tests multiple keys where one is absent
            '[{"key": "thumbhash"},{"key": "other_metadata"}]',
            {"other_metadata": "foo"},
            {"thumbhash": "foo", "other_metadata": "foo"},
        ],
        [
            # This scenario tests multiple keys where all are absent
            '[{"key": "thumbhash"},{"key": "other_metadata"}]',
            {},
            {"thumbhash": "foo", "other_metadata": "foo"},
        ],
    ],
)
def test_apply_criteria_returns_empty_list_when_key_is_None(criteria, kwargs, control_kwargs):
    """
    None is a undesireable key value for this project because we rely on keys to
    categorize similar photos, and typically None represents the absence of information.

    A real scenario example: suppose some photos have not yet generated thumbnails. It
    would be undesireable to create a stack of all the photos whose thumbhash is None.
    """

    # Arrange
    photo = asset_factory(**kwargs)
    # The purpose of control_photo is to prove the test results are not due
    # to a bug in our test logic.
    control_photo = asset_factory(**control_kwargs)

    # Act
    with patch.dict(os.environ, {"CRITERIA": criteria}):
        photo_keys = apply_criteria(photo)
        control_photo_keys = apply_criteria(control_photo)

    # Assert
    assert control_photo_keys == list(control_kwargs.values())
    assert photo_keys == []

def test_groupby_criteria_given_None_value_does_not_error():
    """
    Writing a failing test first for this scenario:
      CRITERIA='[{"key": "thumbhash"}]'
    can throw this error if thumbhash has a None value:
      TypeError: '<' not supported between instances of 'NoneType' and 'str'

    Once this test is passing, that proves we have fixed the error scenario.
    """

    # Arrange
    criteria = '[{"key": "thumbhash"}]'
    test_datetime = fake.unique.date_time()
    asset_list = [
        asset_factory("IMG_1234.jpg", thumbhash="foo"),
        asset_factory("IMG_1234.png", thumbhash=None),
        asset_factory("IMG_1234.raw"),
    ]

    # Act
    with patch.dict(os.environ, {"CRITERIA": criteria}):
        result = [(k, len(list(g))) for k, g in groupby(asset_list, apply_criteria)]

    # Assert
    assert len(result) == 2
    assert result[0] == (["foo"], 1)
    assert result[1] == ([], 2)
