from sanic import Sanic
from dc_interactions import InteractionBot
from os import environ as env
import asyncio


bot = InteractionBot(
    public_key=env.get("PUBLIC_KEY"),
    token=env.get("TOKEN")
)


# The most simple command
@bot.command()
async def ping(ctx):
    """
    Ping! Pong!
    """
    await ctx.respond("Pong!")


async def prepare():
    await bot.prepare()
    await bot.push_commands()


loop = asyncio.get_event_loop()
loop.run_until_complete(prepare())

app = Sanic(__name__)
app.add_route(bot.sanic_entry, "/entry", methods={"POST"})
app.run(host="127.0.0.1", port=8080)