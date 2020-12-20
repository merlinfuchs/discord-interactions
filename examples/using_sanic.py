from sanic import Sanic
from dc_interactions import InteractionProvider
from os import environ as env
import asyncio


provider = InteractionProvider(
    public_key=env.get("PUBLIC_KEY"),
    token=env.get("TOKEN")
)


# The most simple command
@provider.command()
async def ping(ctx):
    """
    Ping! Pong!
    """
    await ctx.respond("Pong!")


async def prepare():
    await provider.prepare()
    await provider.push_commands()


loop = asyncio.get_event_loop()
loop.run_until_complete(prepare())

app = Sanic(__name__)
app.add_route(provider.sanic_entry, "/entry", methods={"POST"})
app.run(host="127.0.0.1", port=8080)