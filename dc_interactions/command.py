from enum import IntEnum
import inspect
import re

from response import *


__all__ = (
    "make_command",
    "Command",
    "CommandOption",
    "CommandOptionType",
    "CommandOptionChoice",
    "SubCommand",
    "SubCommandGroup",
    "CommandContext"
)


def inspect_options(_callable, descriptions=None):
    descriptions = descriptions or {}
    skip = 1  # Skip ctx
    if inspect.ismethod(_callable):
        skip += 1  # Skip self

    options = []
    for p in list(inspect.signature(_callable).parameters.values())[skip:]:
        converter = p.annotation if p.annotation != inspect.Parameter.empty else str
        _type = CommandOptionType.STRING
        choices = []
        if isinstance(converter, CommandOptionType):
            _type = converter
            if converter in {CommandOptionType.ROLE, CommandOptionType.CHANNEL, CommandOptionType.USER}:
                converter = lambda v: re.match(r"[0-9]+", v)[0]

        elif converter == int:
            _type = CommandOptionType.INTEGER

        elif converter == bool:
            _type = CommandOptionType.BOOLEAN

        elif isinstance(converter, tuple) or isinstance(converter, list):
            for choice in converter:
                choices.append(CommandOptionChoice(name="placeholder", value=choice))

            converter = str

        # elif inspect.isclass(converter) and issubclass(converter, Converter):
        #     _type = converter.type

        options.append(CommandOption(
            type=_type,
            name=p.name,
            description=descriptions.get(p.name, "No description"),
            # default=False,
            required=p.default == inspect.Parameter.empty,
            choices=choices,
            converter=converter
        ))

    return options


def make_command(klass, cb, **kwargs):
    values = {
        "callable": cb,
        "name": cb.__name__,
        "description": inspect.getdoc(cb),
        "options": inspect_options(cb)
    }
    descriptions = kwargs.pop("descriptions", None)
    if descriptions:
        for option in values["options"]:
            description = descriptions.get(option.name)
            if description:
                option.description = description

    values.update(kwargs)
    return klass(**values)


class Command:
    def __init__(self, **kwargs):
        self.callable = kwargs.get("callable")
        self.name = kwargs["name"]
        self.description = kwargs["description"]
        self.options = kwargs.get("options", [])
        self.sub_commands = []

    def sub_command_group(self, _callable=None, **kwargs):
        if _callable is None:
            def _predicate(_callable):
                cmd = make_command(SubCommandGroup, _callable, **kwargs)
                self.sub_commands.append(cmd)
                return cmd

            return _predicate

        cmd = make_command(SubCommandGroup, _callable, **kwargs)
        self.sub_commands.append(cmd)
        return cmd

    def sub_command(self, _callable=None, **kwargs):
        if _callable is None:
            def _predicate(_callable):
                cmd = make_command(SubCommand, _callable, **kwargs)
                self.sub_commands.append(cmd)
                return cmd

            return _predicate

        cmd = make_command(SubCommand, _callable, **kwargs)
        self.sub_commands.append(cmd)
        return cmd

    def to_payload(self):
        return {
            "name": self.name,
            "description": self.description,
            "options": [o.to_payload() for o in self.options] + [s.to_payload() for s in self.sub_commands]
        }


class CommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8


class CommandOption:
    def __init__(self, **kwargs):
        self.type = kwargs["type"]
        self.name = kwargs["name"]
        self.description = kwargs["description"]
        self.default = kwargs.get("default", False)
        self.required = kwargs.get("required", True)
        self.choices = kwargs.get("choices", [])

        self.converter = kwargs.get("converter", str)

    def to_payload(self):
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "default": self.default,
            "required": self.required,
            "choices": [c.to_payload() for c in self.choices]
        }


class SubCommand:
    def __init__(self, **kwargs):
        self.callable = kwargs.get("callable")
        self.name = kwargs["name"]
        self.description = kwargs["description"]
        self.options = kwargs.get("options", [])

    def to_payload(self):
        return {
            "type": CommandOptionType.SUB_COMMAND,
            "name": self.name,
            "description": self.description,
            "options": [o.to_payload() for o in self.options]
        }


class SubCommandGroup:
    def __init__(self, **kwargs):
        self.callable = kwargs.get("callable")
        self.name = kwargs["name"]
        self.description = kwargs["description"]
        self.options = kwargs.get("options", [])
        self.sub_commands = []

    def sub_command(self, _callable=None, **kwargs):
        if _callable is None:
            def _predicate(_callable):
                cmd = make_command(SubCommand, _callable, **kwargs)
                self.sub_commands.append(cmd)
                return cmd

            return _predicate

        cmd = make_command(SubCommand, _callable, **kwargs)
        self.sub_commands.append(cmd)
        return cmd

    def to_payload(self):
        return {
            "type": CommandOptionType.SUB_COMMAND_GROUP,
            "name": self.name,
            "description": self.description,
            "options": [o.to_payload() for o in self.options] + [s.to_payload() for s in self.sub_commands]
        }


class CommandOptionChoice:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_payload(self):
        return {
            "name": self.name,
            "value": self.value
        }


class CommandContext:
    def __init__(self, provider, command, payload):
        self.provider = provider
        self.payload = payload
        self.command = command

        self.future = provider.loop.create_future()

    async def respond_with(self, response):
        if self.future.done():
            return await self.provider.make_request(
                "POST",
                f"/webhooks/{self.provider.app_id}/{self.token}",
                data=response.data
            )

        else:
            self.future.set_result(response)

    def respond(self, *args, **kwargs):
        return self.respond_with(InteractionResponse.message(*args, **kwargs))

    def respond_with_source(self, *args, **kwargs):
        return self.respond_with(InteractionResponse.message_with_source(*args, **kwargs))

    def acknowledge(self):
        return self.respond_with(InteractionResponse.acknowledge())

    def acknowledge_with_source(self):
        return self.respond_with(InteractionResponse.acknowledge_with_source())

    async def get_response(self):
        pass

    async def edit_response(self):
        pass

    async def delete_response(self):
        pass

    @property
    def token(self):
        return self.payload.token

    @property
    def guild_id(self):
        return self.payload.guild_id

    @property
    def channel_id(self):
        return self.payload.channel_id

    @property
    def data(self):
        return self.payload.data

    @property
    def author(self):
        return self.payload.member

    @property
    def member(self):
        return self.payload.member
