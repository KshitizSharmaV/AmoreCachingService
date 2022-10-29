import inspect
from datetime import datetime
from dataclasses import asdict, dataclass

@dataclass
class ProfileImage():
    imageURL: str
    firebaseImagePath: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )

@dataclass
class ChatUser():
    firstName: str
    lastName: str
    image1: ProfileImage
    id: str = ""

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )

@dataclass
class ChatText():
    fromId: str
    toId: str
    text: str
    timestamp: datetime
    otherUserUpdated: bool

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )

@dataclass
class ChatConversation():
    fromId: str
    toId: str
    user: ChatUser
    lastText: str
    timestamp: datetime
    msgRead: bool
    otherUserUpdated: bool
    directMessageApproved: bool = True

    @classmethod
    def from_dict(cls, data):
        return cls(
            **{
                key: (data[key] if val.default == val.empty else data.get(key, val.default))
                for key, val in inspect.signature(cls).parameters.items()
            }
        )