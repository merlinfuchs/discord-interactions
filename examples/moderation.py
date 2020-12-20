from aiohttp import web
from dc_interactions import InteractionProvider, CommandOptionType, has_permissions
from os import environ as env

provider = InteractionProvider(
    public_key=env.get("PUBLIC_KEY"),
    token=env.get("TOKEN"),
)


@provider.command()
@has_permissions(1 << 1)
async def kick(ctx, user: CommandOptionType.USER, reason: str = "No reason provided"):
    """
    Kick a member from this server
    """
    # actually ban the user (http client required)
    await ctx.respond_with_source(f"Kicked <@{user}>: `{reason}`")


@provider.command()
@has_permissions(1 << 2)
async def ban(ctx, user: CommandOptionType.USER, reason: str = "No reason provided"):
    """
    Ban a member from this server
    """
    # actually ban the user (http client required)
    await ctx.respond_with_source(f"Banned <@{user}>: `{reason}`")


app = web.Application()


@app.on_startup.append
async def prepare_provider(_):
    await provider.prepare()
    await provider.push_commands()


app.add_routes([web.post("/entry", provider.aiohttp_entry)])
web.run_app(app)
