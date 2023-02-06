from __future__ import annotations
import inspect
from typing import Union
from datetime import datetime
from dataclasses import dataclass, fields, field


def serialise_deserialise_date_in_profile(profile_json: dict, serialise: bool = False, deserialise: bool = False):
    if serialise:
        profile_json['dateOfBirth'] = profile_json['dateOfBirth'].isoformat()
    elif deserialise:
        profile_json['dateOfBirth'] = datetime.fromisoformat(profile_json['dateOfBirth'])
    return profile_json


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
    maxAgePreference: int = 19
    age_range: list = field(init=False)
    age: Union[str, int] = 0
    id: str = '*'

    def __post_init__(self):
        self.minAgePreference = 18 if int(self.minAgePreference) < 18 else int(self.minAgePreference)
        self.maxAgePreference = 19 if int(self.maxAgePreference) < 19 else int(self.maxAgePreference)
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
                # Gender Preference
                if field.name == 'genderPreference':
                    if str(instance_dict.get(field.name)) in {"Male", "Female", "Non Binary"}:
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

