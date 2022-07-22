from __future__ import annotations
import inspect
import json
import traceback
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


profile_type_hints = {
    'id': str, 'firstName': str, 'lastName': str, 'email': str, 'dateOfBirth': datetime, 'interests': list,
    'genderIdentity': str, 'sexualOrientation': list, 'sexualOrientationVisible': bool, 'showMePreference': str,
    'work': str, 'school': str, 'age': int, 'headline': str, 'profileDistanceFromUser': float, 'jobTitle': str,
    'careerField': str, 'height': float, 'education': str, 'religion': str, 'community': str, 'politics': str,
    'location': Location, 'geohash': str, 'geohash1': str, 'geohash2': str, 'geohash3': str, 'geohash4': str,
    'geohash5': str, 'description': str, 'country': str, 'discoveryStatus': bool, 'notificationsStatus': bool,
    'image1': ProfileImage, 'image2': ProfileImage, 'image3': ProfileImage, 'image4': ProfileImage,
    'image5': ProfileImage, 'image6': ProfileImage, 'doYouWorkOut': str, 'doYouDrink': str, 'doYouSmoke': str,
    'doYouWantBabies': str, 'profileCompletion': float, 'countryRaisedIn': str, 'wasProfileUpdated': bool,
    'isProfileActive': bool, 'userCreationDate': datetime
}


@dataclass
class Profile():
    __slots__ = ['id', 'firstName', 'lastName', 'email', 'dateOfBirth', 'interests', 'genderIdentity',
                 'sexualOrientation', 'sexualOrientationVisible', 'showMePreference', 'work', 'school', 'age',
                 'headline', 'profileDistanceFromUser', 'jobTitle', 'careerField', 'height', 'education', 'religion',
                 'community', 'politics', 'location', 'geohash', 'geohash1', 'geohash2', 'geohash3', 'geohash4',
                 'geohash5', 'description', 'country', 'discoveryStatus', 'notificationsStatus', 'image1', 'image2',
                 'image3', 'image4', 'image5', 'image6', 'doYouWorkOut', 'doYouDrink', 'doYouSmoke', 'doYouWantBabies',
                 'profileCompletion', 'countryRaisedIn', 'wasProfileUpdated', 'isProfileActive', 'userCreationDate']
    id: str
    firstName: str
    lastName: str
    email: str
    dateOfBirth: datetime
    interests: list
    genderIdentity: str
    sexualOrientation: list
    sexualOrientationVisible: bool
    showMePreference: str
    work: str
    school: str
    age: int
    headline: str
    profileDistanceFromUser: float
    jobTitle: str
    careerField: str
    height: float
    education: str
    religion: str
    community: str
    politics: str
    location: Location
    geohash: str
    geohash1: str
    geohash2: str
    geohash3: str
    geohash4: str
    geohash5: str
    description: str
    country: str
    discoveryStatus: bool
    notificationsStatus: bool
    image1: ProfileImage
    image2: ProfileImage
    image3: ProfileImage
    image4: ProfileImage
    image5: ProfileImage
    image6: ProfileImage
    doYouWorkOut: str
    doYouDrink: str
    doYouSmoke: str
    doYouWantBabies: str
    profileCompletion: float
    countryRaisedIn: str
    wasProfileUpdated: bool
    isProfileActive: bool
    userCreationDate: datetime

    def to_dict(self):
        ignore_elements = ['location', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6']
        instance_dict = {}
        for _field in fields(self):
            if _field not in ignore_elements:
                cast_type = profile_type_hints[_field.name]
                instance_dict.update(decode_with_type_casting(_field.name, getattr(self, _field.name), cast_type))
        instance_dict['location'] = self.location
        instance_dict['image1'] = self.image1
        instance_dict['image2'] = self.image2
        instance_dict['image3'] = self.image3
        instance_dict['image4'] = self.image4
        instance_dict['image5'] = self.image5
        instance_dict['image6'] = self.image6
        return instance_dict

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data.get(key) if val.default == val.empty else data.get(key, val.default))
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
                    key: (data.get(key) if val.default == val.empty else data.get(key, val.default))
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
        try:
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
        except Exception as e:
            print(traceback.format_exc())


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
        self.minAgePreference = 18 if int(self.minAgePreference) < 18 else int(self.minAgePreference)
        self.maxAgePreference = 18 if int(self.maxAgePreference) < 18 else int(self.maxAgePreference)
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
                if field.name == 'genderPreference':
                    query_list.append(f"(@genderIdentity:{str(instance_dict.get(field.name))})")
                else:
                    query_list.append(f"(@{field.name}:{str(instance_dict.get(field.name))})")
        if self.age:
            query_list.append(f"(@age:{str(instance_dict.get('age'))})")
        elif self.maxAgePreference != self.minAgePreference:
            query_list.append(
                f"(@age:[{str(instance_dict.get('minAgePreference'))} {str(instance_dict.get('maxAgePreference'))}])")
        query = " ".join(query_list)
        return query


def test_query_builder(**kwargs):
    print(QueryBuilder.from_dict(kwargs).query_builder())


if __name__ == "__main__":
    """
    Test Query Builder
    """
    test_query_builder(id="SaMpLePrOfIlEiD", geohash1="7", geohash2="75", religionPreference="abc")
