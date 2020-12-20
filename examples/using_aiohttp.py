from aiohttp import web
from dc_interactions import InteractionProvider
from os import environ as env

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


app = web.Application()


@app.on_startup.append
async def prepare_provider(_):
    await provider.prepare()
    await provider.push_commands()


app.add_routes([web.post("/entry", provider.aiohttp_entry)])
web.run_app(app)
