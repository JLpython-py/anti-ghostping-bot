#! python3
# bot.py

"""
Anti-GhostPing Discord bot
    - Listens for the on_message_delete event reference to be called
    - Checks deleted message for the following:
        - raw_mentions
        - raw_role_mentions
        - mentions_everyone
    - Sends notifying message to configured channel in Discord guild
===============================================================================
Authorization Flow:
    - Public Bot
Privileged Gateway Intents:
    - Presence Intent
    - Server Members Intent
Permission Integer: 125952
===============================================================================
Copyright (c) 2021 Jacob Lee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
===============================================================================
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from lib.db import db

logging.basicConfig(
    level=logging.INFO,
    format=' %(asctime)s - %(levelname)s - %(message)s')


class CreateBot(commands.Bot):
    """ Create commands.Bot object and add appropriate cogs
"""
    def __init__(self, prefix="@."):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(
            command_prefix=prefix, intents=intents)
        self.connection = db.DBConnection()
        self.add_cog(AntiGhostPing(self))

    async def on_ready(self):
        """ Notify logging of event reference
            Change bot status message
"""
        logging.info("Ready: %s", self.user.name)
        await self.change_presence(
            activity=discord.Game("Ghost Ping Hunting | @."))


class AntiGhostPing(commands.Cog):
    """ Listen for and handle ghost pings
"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """ Notify logging of event reference
            Check for and handle host ping
"""
        if message.author.bot:
            return
        flags = await self.parse(message)
        if flags:
            await self.detected(message, flags)

    async def parse(self, message):
        """ Parse message for all specified mentions
"""
        flags = {}
        if message.raw_role_mentions:
            role_mentions = [
                discord.utils.get(message.guild.roles, id=i).name
                for i in message.raw_role_mentions
            ]
            flags.setdefault(
                "Roles Mentioned",
                ", ".join(role_mentions)
            )
        if message.raw_mentions:
            raw_mentions = [
                discord.utils.get(message.guild.members, id=i).name
                for i in message.raw_mentions
            ]
            flags.setdefault(
                "Members Mentioned",
                ", ".join(raw_mentions))
        if message.mention_everyone:
            flags.setdefault(
                "Other Groups Mentioned", "everyone")
        return flags

    async def detected(self, message, flags):
        """ Alert guild by sending message to specified channel
"""
        channel = message.channel
        embed = discord.Embed(title="Ghost Ping Detected", color=0x0000ff)
        fields = {
            "Member": message.author.name, "Message": message.content,
            "Channel": message.channel.name
        }
        fields = {**fields, **flags}
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        embed.set_footer(
            text=f"Detect At: {message.created_at.strftime('%D %T')}")
        await channel.send(embed=embed)


def main():
    """ Create bot object and add to asyncio event loop to run forever
"""
    token = os.environ.get("token", None)
    if token is None:
        with open("../../token.txt") as file:
            token = file.read()
    assert token is not None
    loop = asyncio.get_event_loop()
    bot = CreateBot()
    loop.create_task(bot.start(token))
    loop.run_forever()


if __name__ == '__main__':
    main()