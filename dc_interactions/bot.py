import json
from aiohttp import web, ClientSession, ContentTypeError
import asyncio
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import traceback
import sys
import inspect
import weakref

from .command import *
from .payloads import *
from .response import *
from .utils import *
from .task import *

__all__ = (
    "InteractionBot",
)


class InteractionBot:
    def __init__(self, **kwargs):
        self.commands = []
        self.tasks = []
        self.public_key = VerifyKey(bytes.fromhex(kwargs["public_key"]))
        self.token = kwargs["token"]
        self._loop = kwargs.get("loop")
        self.session = kwargs.get("session", ClientSession(loop=self.loop))
        self.guild_id = kwargs.get("guild_id")  # Can be used during development to avoid the 1 hour cache
        self.app_id = None
        self.ctx_klass = kwargs.get("ctx_klass", CommandContext)

        self.listeners = {}

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

        return make_command(Command, _callable, **kwargs)

    def task(self, **td):
        def _predicate(_callable):
            t = Task(_callable, **td)
            self.tasks.append(t)
            return t

        return _predicate

    def dispatch(self, event, *args, **kwargs):
        listeners = self.listeners.get(event)
        if listeners is not None:
            for callable, check in listeners:
                try:
                    if check is not None and not check(*args, **kwargs):
                        continue
                except:
                    traceback.print_exc()
                    continue

                if isinstance(callable, asyncio.Future):
                    if not callable.done():
                        if len(args) == 1:
                            callable.set_result(args[0])

                        else:
                            callable.set_result(tuple([*args]))

                else:
                    try:
                        res = callable(*args, **kwargs)
                        if inspect.isawaitable(res):
                            self.loop.create_task(res)
                    except:
                        traceback.print_exc()

    def add_listener(self, event, callable, check=None):
        if event in self.listeners:
            self.listeners[event].add((callable, check))

        else:
            self.listeners[event] = {(callable, check)}

    def remove_listener(self, event, callable, check=None):
        self.listeners[event].remove((callable, check))

    def listener(self, _callable=None, name=None):
        if _callable is None:
            def _predicate(_callable):
                self.add_listener(name or _callable.__name__[3:], _callable)
                return _callable

            return _predicate

        self.add_listener(name or _callable.__name__[3:], _callable)
        return _callable

    async def wait_for(self, event, check=None, timeout=None):
        future = self.loop.create_future()
        try:
            self.add_listener(event, future, check=check)
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self.remove_listener(event, future, check=check)

    def load_module(self, module):
        for cmd in module.commands:
            self.commands.append(cmd)

        for t in module.tasks:
            self.tasks.append(t)

    async def on_command_error(self, ctx, e):
        if isinstance(e, asyncio.CancelledError):
            raise e

        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("Command Error:\n", tb, file=sys.stderr)
        await ctx.acknowledge()

    async def execute_command(self, command, payload, remaining_options):
        ctx = self.ctx_klass(self, command, payload)

        async def _executor():
            try:
                values = {}
                for option in remaining_options:
                    matching_option = iterable_get(command.options, name=option.name)
                    value = matching_option.converter(option.value)
                    values[option.name] = value

                for check in command.checks:
                    res = await check.run(ctx, **values)
                    if res is not True:
                        return

                result = command.callable(ctx, **values)
                if inspect.isawaitable(result):
                    result = await result

                if result is not None:
                    await ctx.respond_with(result)

            except Exception as e:
                await self.on_command_error(ctx, e)

        self.loop.create_task(_executor())

        try:
            return await asyncio.wait_for(ctx.future, timeout=5)
        except asyncio.TimeoutError:
            if not ctx.future.done():
                ctx.future.set_result(None)
            return InteractionResponse.acknowledge()
        except Exception as e:
            return await self.on_command_error(ctx, e)

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
        from sanic import response

        raw_data = request.body.decode("utf-8")
        signature = request.headers.get("x-signature-ed25519")
        timestamp = request.headers.get("x-signature-timestamp")
        if signature is None or timestamp is None:
            return response.empty(status=401)

        try:
            self.public_key.verify(f"{timestamp}{raw_data}".encode(), bytes.fromhex(signature))
        except BadSignatureError:
            return response.empty(status=401)

        data = InteractionPayload(json.loads(raw_data))
        resp = await self.interaction_received(data)
        return response.json(resp.to_dict())

    async def make_request(self, method, path, data=None, files=None, **params):
        # Should be overwritten with an actual http client with proper ratelimiting
        async with self.session.request(
                method=method,
                url=f"https://discord.com/api/v8{path.format(**params)}",
                json=data,
                headers={
                    "Authorization": f"Bot {self.token}"
                }
        ) as resp:
            if resp.status < 200 or resp.status > 299:
                print(await resp.text())
                resp.raise_for_status()

            try:
                return await resp.json()
            except ContentTypeError:
                return True

    async def prepare(self):
        app = await self.make_request("GET", "/oauth2/applications/@me")
        self.app_id = app["id"]
        for t in self.tasks:
            self.loop.create_task(t.run())

    def _commands_endpoint(self, guild_id=None):
        if guild_id is not None or self.guild_id is not None:
            return "/applications/{app_id}/guilds/{guild_id}/commands"
        else:
            return "/applications/{app_id}/commands"

    async def create_command(self, command, guild_id=None):
        guild_id = guild_id or command.guild_id or self.guild_id
        await self.make_request(
            "POST",
            self._commands_endpoint(guild_id=guild_id),
            data=command.to_payload(),
            app_id=self.app_id,
            guild_id=guild_id
        )

    async def create_commands(self, commands, guild_id=None):
        if len(commands) == 0:
            return

        guild_id = guild_id or commands[0].guild_id or self.guild_id
        await self.make_request(
            "PUT",
            self._commands_endpoint(guild_id=guild_id),
            data=[c.to_payload() for c in commands],
            app_id=self.app_id,
            guild_id=guild_id
        )

    async def push_commands(self):
        return await self.create_commands([c for c in self.commands if c.register])

    async def fetch_commands(self, guild_id=None):
        guild_id = guild_id or self.guild_id
        return await self.make_request("GET", self._commands_endpoint(guild_id=guild_id),
                                       guild_id=guild_id, app_id=self.app_id)

    async def delete_command(self, command_id, guild_id=None):
        guild_id = guild_id or self.guild_id
        await self.make_request("DELETE", "%s/{command_id}" % self._commands_endpoint(guild_id=guild_id),
                                guild_id=guild_id, app_id=self.app_id, command_id=command_id)

    async def flush_commands(self):
        commands = await self.fetch_commands()
        for command in commands:
            await self.delete_command(command["id"])
