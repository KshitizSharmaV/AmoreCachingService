from __future__ import annotations
import inspect
import json
from pickle import decode_long
from typing import Any, Union
from datetime import datetime
from dataclasses import asdict, dataclass, fields, field
from typing import get_type_hints
from pprint import pprint
from Utilities.DictOps import flatten_dict_str, decode_with_type_casting, remove_payload_key


@dataclass
class ProfileImage():
    imageURL: str = None
    firebaseImagePath: str = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )


@dataclass
class Location():
    longitude: float = None
    latitude: float = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )


@dataclass
class Profile():
    id: str = None
    firstName: str = None
    lastName: str = None
    email: str = None
    dateOfBirth: datetime = None
    interests: list = None
    genderIdentity: str = None
    sexualOrientation: list = None
    sexualOrientationVisible: bool = None
    showMePreference: str = None
    work: str = None
    school: str = None
    age: int = None
    headline: str = None
    profileDistanceFromUser: float = None
    jobTitle: str = None
    careerField: str = None
    height: float = None
    education: str = None
    religion: str = None
    community: str = None
    politics: str = None
    location: Location = None
    geohash: str = None
    geohash1: str = None
    geohash2: str = None
    geohash3: str = None
    geohash4: str = None
    geohash5: str = None
    description: str = None
    country: str = None
    discoveryStatus: bool = None
    notificationsStatus: bool = None
    image1: ProfileImage = ProfileImage()
    image2: ProfileImage = ProfileImage()
    image3: ProfileImage = ProfileImage()
    image4: ProfileImage = ProfileImage()
    image5: ProfileImage = ProfileImage()
    image6: ProfileImage = ProfileImage()
    doYouWorkOut: str = None
    doYouDrink: str = None
    doYouSmoke: str = None
    doYouWantBabies: str = None
    profileCompletion: float = None
    countryRaisedIn: str = None
    wasProfileUpdated: bool = None
    isProfileActive: bool = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )

    @classmethod
    def encode_data_for_redis(cls, data: dict):
        """
        Encode Profiles data to Dict for Redis.
        :param data: Dict of profile data to be encoded into Profile Class
        :type data: dict
        :return: Encoded, type converted dict acceptable by Redis Hash
        """
        return flatten_dict_str(
            asdict(cls(
                **{
                    key: (data[key] if val.default == val.empty else data.get(key, val.default))
                    for key, val in inspect.signature(cls).parameters.items()
                }
            ))
        )

    @classmethod
    def decode_data_from_redis(cls, data: dict):
        """
        Decode incoming Profiles data from Redis.
        :param data: Dict fetched from Redis
        :type data: dict
        :return: Profile class instance
        """
        data = remove_payload_key(data)
        user_defined_types = [Location.__name__, ProfileImage.__name__]
        decoded_dict = {}
        for key, val in inspect.signature(cls).parameters.items():
            if cls.__annotations__[key] in user_defined_types and not isinstance(data.get(key), dict):
                data[key] = json.loads(data.get(key)) if data.get(key) else val.default
            if val.default == val.empty:
                decoded_dict.update({key: data.get(key)})
            else:
                cast_type = get_type_hints(cls)[key]
                # decoded_dict.update({key: cast_type(data.get(key, val.default)) if data.get(key) else val.default})
                decoded_dict.update(decode_with_type_casting(key, data.get(key, val.default), cast_type))
        return cls(**decoded_dict)


"""
Query Builder Class for Profiles Data from Redis.
"""
@dataclass
class QueryBuilder():
    geohash1: str = '*'
    geohash2: str = '*'
    geohash3: str = '*'
    geohash4: str = '*'
    geohash5: str = '*'
    geohash: str = '*'
    genderPreference: str = '*'
    # religionPreference: str = '*'
    minAgePreference: int = 18
    maxAgePreference: int = 18
    age_range: list = field(init=False)
    age: Union[str, int] = 0
    id: str = '*'

    def __post_init__(self):
        self.minAgePreference = 18 if self.minAgePreference < 18 else self.minAgePreference
        self.maxAgePreference = 18 if self.maxAgePreference < 18 else self.maxAgePreference
        self.age_range = list(range(self.minAgePreference, self.maxAgePreference + 1))

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )

    def query_builder(self):
        """
        Builds keys based on the values of member fields

        :return: Query String for Redisearch
        """
        query, ignore_elems = [], ['minAgePreference', 'maxAgePreference', 'age_range', 'age']
        instance_dict = self.__dict__
        query_list = []
        for field in fields(self):
            if field.name not in ignore_elems and instance_dict.get(field.name) != '*':
                query_list.append(f"@{field.name}:{str(instance_dict.get(field.name))}")
        if self.age:
            query_list.append(f"@age:{str(instance_dict.get('age'))}")
        elif self.maxAgePreference != self.minAgePreference:
            query_list.append(
                f"@age:[{str(instance_dict.get('minAgePreference'))} {str(instance_dict.get('maxAgePreference'))}]")
        query = " ".join(query_list)
        return query


def test_query_builder(**kwargs):
    print(QueryBuilder.from_dict(kwargs).query_builder())


if __name__ == "__main__":
    """
    Test Query Builder
    """
    test_query_builder(id="SaMpLePrOfIlEiD", geohash1="7", geohash2="75", religionPreference="abc")
