# discord-interactions

An implementation of discord interactions (slash commands to be specific) using python and asyncio.  
Supports both aiohttp and sanic as a http server.  
  
Used in the most recent version of [Xenon](https://xenon.bot).

# Install

```
pip install git+git://github.com/merlinfuchs/discord-interactions
```

# Example

A simple example using aiohttp:

```py
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


# Providing option descriptions
@bot.command(
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
@bot.command()
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
async def prepare_bot(_):
    await bot.prepare()
    await bot.push_commands()


app.add_routes([web.post("/entry", bot.aiohttp_entry)])
web.run_app(app)
```

You can find more example in the `examples` folder.