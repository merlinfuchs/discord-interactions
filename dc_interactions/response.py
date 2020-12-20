from enum import IntEnum


__all__ = (
    "InteractionResponseType",
    "InteractionResponse"
)


class InteractionResponseType(IntEnum):
    PONG = 1
    ACKNOWLEDGE = 2
    CHANNEL_MESSAGE = 3
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    ACKNOWLEDGE_WITH_SOURCE = 5


class InteractionResponse:
    def __init__(self, type, content=None, **kwargs):
        self.type = type
        self.data = kwargs
        self.data["content"] = content

    @classmethod
    def pong(cls):
        return cls(InteractionResponseType.PONG)

    @classmethod
    def acknowledge(cls):
        return cls(InteractionResponseType.ACKNOWLEDGE)

    @classmethod
    def message(cls, content=None, **kwargs):
        return cls(InteractionResponseType.CHANNEL_MESSAGE, content=content, **kwargs)

    @classmethod
    def message_with_source(cls, content=None, **kwargs):
        return cls(InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE, content=content, **kwargs)

    @classmethod
    def acknowledge_with_source(cls):
        return cls(InteractionResponseType.ACKNOWLEDGE_WITH_SOURCE)

    def to_dict(self):
        return {
            "type": self.type.value,
            "data": self.data
        }
