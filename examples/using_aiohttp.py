from aiohttp import web
from dc_interactions import InteractionBot
from os import environ as env

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


app = web.Application()


@app.on_startup.append
async def prepare_bot(_):
    await bot.prepare()
    await bot.push_commands()


app.add_routes([web.post("/entry", bot.aiohttp_entry)])
web.run_app(app)
