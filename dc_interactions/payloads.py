from enum import IntEnum


__all__ = (
    "InteractionType",
    "InteractionPayload",
    "CommandInteractionData",
    "CommandInteractionDataOption",
)


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2


class ResolvedEntities:
    def __init__(self, data):
        self.users = data.get("users", {})
        self.members = data.get("members", {})
        self.roles = data.get("roles", {})
        self.channels = data.get("channels", {})


class InteractionPayload:
    def __init__(self, data):
        print(data.get("resolved"))
        self.id = data["id"]
        self.type = InteractionType(data["type"])
        self.guild_id = data.get("guild_id")
        self.channel_id = data.get("channel_id")
        self.token = data.get("token")
        self.version = data.get("version")
        self.resolved = ResolvedEntities(data.get("resolved", {}))

        if self.type == InteractionType.APPLICATION_COMMAND:
            self.data = CommandInteractionData(data["data"])
            self.member = data["member"]


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
