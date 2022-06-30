import datetime
from functools import partial
from collections.abc import MutableMapping, Mapping, Sequence
import json


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping) or isinstance(v, Mapping) or isinstance(v, Sequence):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif type(v) == bool:
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_dict_str(d: dict) -> dict:
    """
    Flatten the dict since Redis Hash accepts only flattened dicts without any complex types

    :param d: Dict to be flattened
    :type d: dict
    :return: Flattened Dict
    """
    items = []
    json_cast_types = [MutableMapping, Mapping, list, tuple, set, bool]
    for k, v in d.items():
        if v is not None:
            if True in list(map(partial(isinstance, v), json_cast_types)):
                items.append((k, json.dumps(v)))
            elif isinstance(v, datetime.datetime):
                items.append((k, v.isoformat(' ', timespec='microseconds')))
            else:
                items.append((k, v))
    return dict(items)


def is_dict_with_byte_data(d: dict) -> bool:
    """
    Check if dict has keys and values as bytes or bytearray

    :param d: Dict to be checked
    :type d: dict
    :return: Boolean
    """
    for k, v in d.items():
        if isinstance(k, (bytes, bytearray)) or isinstance(v, (bytes, bytearray)):
            return True
        else:
            return False
    return False


def decode_binary_dict(d: dict) -> dict:
    """
    Decode byte encoded dict

    :param d: Dict to be decoded
    :type d: dict
    :return: UTF-8 decoded Dict
    """
    if not is_dict_with_byte_data(d):
        return d
    return {key.decode('utf-8'): value.decode('utf-8') for key, value in d.items()}


def decode_with_type_casting(key, val, cast_type):
    """
    Decode '{key: val}' dict with type casting the values according to the suggested 'cast_type' of 'val' for 'key'

    :param key: key of the dict
    :param val: value for the corresponding key
    :param cast_type: suggested type for the val of given key
    :return: Dict with type-casted values
    """
    json_cast_types = [list, tuple, set, bool]
    if val is not None:
        if cast_type == datetime.datetime:
            return {key: cast_type.fromisoformat(val)}
        elif cast_type in json_cast_types:
            return {key: json.loads(val)}
        else:
            return {key: cast_type(**val) if isinstance(val, dict) else cast_type(val)}
    else:
        # return {key: val}
        return {}


def remove_payload_key(d: dict) -> dict:
    """
    Remove 'payload' key from dict returned from Redis Querying

    :param d: dict returned from redis
    :type d: dict
    :return: Dict with 'payload' key removed
    """
    if 'payload' in d.keys():
        d.pop('payload')
    return d


def ignore_none(d):
    """
    Used as dict_factory function to ignore the keys in dict
    which have none values when converting class to dict

    :return: Dict with None key-val removed
    """
    return {k: v for (k, v) in d if v is not None}

