import json
from aiohttp import web, ClientSession, ContentTypeError
import asyncio
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

try:
    from sanic import response as sanic_response
except ModuleNotFoundError:
    sanic_response = None

from command import *
from payloads import *
from response import *
from utils import *


__all__ = (
    "InteractionProvider",
)


class InteractionProvider:
    def __init__(self, **kwargs):
        self.commands = []
        self.public_key = VerifyKey(bytes.fromhex(kwargs["public_key"]))
        self.token = kwargs["token"]
        self._loop = kwargs.get("loop")
        self.session = kwargs.get("session", ClientSession(loop=self.loop))
        self.app_id = None

    @property
    def loop(self):
        return self._loop or asyncio.get_event_loop()

    def find_command(self, data):
        base_command = iterable_get(self.commands, name=data.name)
        if base_command is None:
            return None  # Out of sync; ignore

        for option in data.options:
            sub_command = iterable_get(base_command.sub_commands, name=option.name)
            if isinstance(sub_command, SubCommandGroup):
                for sub_option in option.options:
                    sub_sub_command = iterable_get(sub_command.sub_commands, name=sub_option.name)
                    if sub_sub_command is None:
                        return None  # Out of sync; ignore

                    return sub_sub_command, sub_option.options

            elif isinstance(sub_command, SubCommand):
                return sub_command, option.options

        return base_command, data.options

    def command(self, _callable=None, **kwargs):
        if _callable is None:
            def _predicate(_callable):
                cmd = make_command(Command, _callable, **kwargs)
                self.commands.append(cmd)
                return cmd

            return _predicate

        cmd = Command(callable=_callable, **kwargs)
        self.commands.append(cmd)
        return cmd

    async def execute_command(self, command, payload, remaining_options):
        ctx = CommandContext(self, command, payload)

        # parse options
        # run converters
        # run checks

        async def _executor():
            try:
                result = await command.callable(ctx, *[o.value for o in remaining_options])
                if result is not None:
                    await ctx.respond_with(result)

            except Exception as e:
                ctx.future.set_exception(e)

        self.loop.create_task(_executor())

        try:
            return await ctx.future
        except Exception as e:
            return await self.on_error(ctx, e)

    async def interaction_received(self, payload):
        if payload.type == InteractionType.PING:
            return InteractionResponse.pong()

        elif payload.type == InteractionType.APPLICATION_COMMAND:
            command, remaining_options = self.find_command(payload.data)
            if command is None:
                return InteractionResponse.acknowledge()

            return await self.execute_command(command, payload, remaining_options)

    async def aiohttp_entry(self, request):
        raw_data = await request.text()
        signature = request.headers.get("x-signature-ed25519")
        timestamp = request.headers.get("x-signature-timestamp")
        if signature is None or timestamp is None:
            return web.HTTPUnauthorized()

        try:
            self.public_key.verify(f"{timestamp}{raw_data}".encode(), bytes.fromhex(signature))
        except BadSignatureError:
            return web.HTTPUnauthorized()

        data = InteractionPayload(json.loads(raw_data))
        resp = await self.interaction_received(data)
        return web.json_response(resp.to_dict())

    async def sanic_entry(self, request):
        if not sanic_response:
            raise ModuleNotFoundError("Sanic is not installed")

        raw_data = request.body.decode("utf-8")
        signature = request.headers.get("x-signature-ed25519")
        timestamp = request.headers.get("x-signature-timestamp")
        if signature is None or timestamp is None:
            return sanic_response.empty(status=401)

        try:
            self.public_key.verify(f"{timestamp}{raw_data}".encode(), bytes.fromhex(signature))
        except BadSignatureError:
            return sanic_response.empty(status=401)

        data = InteractionPayload(json.loads(raw_data))
        resp = await self.interaction_received(data)
        return sanic_response.json(resp.to_dict())

    async def make_request(self, method, path, data=None):
        # Should be replaced with an actual http client with proper ratelimiting
        async with self.session.request(
            method=method,
            url=f"https://discord.com/api/v8{path}",
            json=data,
            headers={
                "Authorization": f"Bot {self.token}"
            }
        ) as resp:
            resp.raise_for_status()
            try:
                return await resp.json()
            except ContentTypeError:
                return True

    async def prepare(self):
        app = await self.make_request("GET", "/oauth2/applications/@me")
        self.app_id = app["id"]

    async def push_commands(self):
        for command in self.commands:
            await self.make_request("POST", f"/applications/{self.app_id}/guilds/496683369665658880/commands", data=command.to_payload())

    async def flush_commands(self):
        commands = await self.make_request("GET", f"/applications/{self.app_id}/guilds/496683369665658880/commands")
        for command in commands:
            await self.make_request("DELETE", f"/applications/{self.app_id}/guilds/496683369665658880/commands/{command['id']}")
