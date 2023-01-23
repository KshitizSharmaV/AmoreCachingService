import pytest
import json
from unittest.mock import patch
from Utilities.DictOps import *

def test_flatten_dict():
    # Arrange
    d = {"a": 1, "b": {"c": 2, "d": 3}}
    parent_key = "f"
    sep = "_"
    expected = {"f_a": 1, "f_b_c": 2, "f_b_d": 3}

    # Act
    result = flatten_dict(d, parent_key, sep)

    # Assert
    assert result == expected


def test_decode_binary_dict():
    # Arrange
    binary_dict = {b'key1': b'value1', b'key2': b'value2', b'key3': b'value3'}
    expected_output = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

    # Act
    result = decode_binary_dict(binary_dict)

    # Assert
    assert result == expected_output

    # Arrange
    non_binary_dict = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

    # Act
    result = decode_binary_dict(non_binary_dict)

    # Assert
    assert result == non_binary_dict


def test_decode_with_type_casting():
    # Arrange
    key = 'key1'
    val = '2022-01-01T00:00:00'
    cast_type = datetime.datetime
    expected_output = {'key1': datetime.datetime(2022, 1, 1, 0, 0)}

    # Act
    result = decode_with_type_casting(key, val, cast_type)

    # Assert
    assert result == expected_output

    # Arrange
    key = 'key2'
    val = 'true'


