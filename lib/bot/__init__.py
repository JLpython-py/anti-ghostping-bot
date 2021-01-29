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
import logging

import discord
from discord.ext import commands

from lib.db import db

logging.basicConfig(
    level=logging.INFO,
    format=' %(asctime)s - %(levelname)s - %(message)s')


class BotRoot(commands.Bot):
    """ Create commands.Bot object and add appropriate cogs
"""
    def __init__(self, prefix="@."):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(
            command_prefix=prefix, intents=intents)
        self.connection = db.DBConnection()

    async def on_ready(self):
        """ Notify logging of event reference
            Change bot status message
"""
        logging.info("Ready: %s", self.user.name)
        await self.change_presence(
            activity=discord.Game("Ghost Ping Hunting | @."))
