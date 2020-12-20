from enum import IntEnum


__all__ = (
    "InteractionType",
    "InteractionPayload",
    "CommandInteractionData",
    "CommandInteractionDataOption",
    "Member"
)


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2


class InteractionPayload:
    def __init__(self, data):
        self.id = data["id"]
        self.type = InteractionType(data["type"])
        self.guild_id = data.get("guild_id")
        self.channel_id = data.get("channel_id")
        self.token = data.get("token")
        self.version = data.get("version")

        if self.type == InteractionType.APPLICATION_COMMAND:
            self.data = CommandInteractionData(data["data"])
            self.member = Member(data["member"])


class CommandInteractionData:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.options = [CommandInteractionDataOption(o) for o in data.get("options", [])]


class CommandInteractionDataOption:
    def __init__(self, data):
        self.name = data["name"]
        self.value = data.get("value")
        self.options = [CommandInteractionDataOption(o) for o in data.get("options", [])]


class Member:
    def __init__(self, data):
        user = data["user"]
        self.id = user["id"]
        self.name = user["username"]
