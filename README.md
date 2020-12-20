# discord-interactions

An implementation of discord interactions (slash commands to be specific) using python and asyncio.  
Supports both aiohttp and sanic as a http server.

# Install

```
pip install git+git://github.com/merlinfuchs/discord-interactions
```

# Example

A simple example using aiohttp:

```py
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


# Providing option descriptions
@provider.command(
    descriptions=dict(
        to_echo="The text to echo"
    )
)
async def echo(ctx, to_echo):
    """
    Echo? Echo!
    """
    await ctx.respond(to_echo)


# Sub commands
@provider.command()
async def repeat(ctx):
    """
    Repeat some text
    """


@repeat.sub_command()
async def twice(ctx, text):
    """
    Repeat some text twice
    """
    await ctx.respond(f"1: {text}")
    await ctx.respond(f"2: {text}")


app = web.Application()


@app.on_startup.append
async def prepare_provider(_):
    await provider.prepare()
    await provider.push_commands()


app.add_routes([web.post("/entry", provider.aiohttp_entry)])
web.run_app(app)
```

You can find more example in the `examples` folder.