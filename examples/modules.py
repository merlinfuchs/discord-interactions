from aiohttp import web
from dc_interactions import InteractionBot, Module
from os import environ as env

bot = InteractionBot(
    public_key=env.get("PUBLIC_KEY"),
    token=env.get("TOKEN"),
    guild_id="496683369665658880"
)


class PingModule(Module):
    @Module.command()
    async def ping(self, ctx):
        """
        Ping Pong!
        """
        await ctx.respond_with_source("Pong!")


bot.load_module(PingModule(bot))
app = web.Application()


@app.on_startup.append
async def prepare_bot(_):
    await bot.prepare()
    await bot.push_commands()


app.add_routes([web.post("/entry", bot.aiohttp_entry)])
web.run_app(app)
