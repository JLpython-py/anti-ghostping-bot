#! python3
# bot.py

'''

'''

import asyncio
import logging
import os

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format=' %(asctime)s - %(levelname)s - %(message)s')

class Bot(commands.Bot):
    '''
'''
    def __init__(self, prefix="@."):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        commands.Bot.__init__(
            self, command_prefix=prefix, intents=intents)
        self.add_cog(GhostPing(self))

    async def on_ready(self):
        ''' Set bot activity
'''
        logging.info("Ready: %s", self.user.name)
        await self.change_presence(
            activity=discord.Game("Ghost Ping Hunting"))

class GhostPing(commands.Cog):
    '''
'''
    def __init__(self, bot):
        self.bot = bot

def main():
    token = os.environ.get("token", None)
    if token is None:
        with open("token.txt") as file:
            token = file.read()
    assert token is not None
    loop = asyncio.get_event_loop()
    bot = Bot()
    loop.create_task(bot.start(token))
    loop.run_forever()

if __name__ == '__main__':
    main()

        
