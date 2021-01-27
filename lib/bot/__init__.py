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

import json
import logging
import os

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
        self.add_cog(AntiGhostPing(self))
        self.add_cog(Configuration(self))

    async def on_ready(self):
        """ Notify logging of event reference
            Change bot status message
"""
        logging.info("Ready: %s", self.user.name)
        await self.change_presence(
            activity=discord.Game("Ghost Ping Hunting | @."))


class Configuration(commands.Cog):
    """ Allow guild owners to configure bot preferences
"""
    def __init__(self, bot):
        self.directory = os.path.join("data", "BotConfiguration")
        self.bot = bot
        with open(os.path.join(
                self.directory, "prompt.txt"
        )) as file:
            self.prompt_fields = json.load(file)
        with open(os.path.join(
                self.directory, "configure.txt"
        )) as file:
            self.configure_fields = json.load(file)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Send configuration prompt when the bot is added to a guild
"""
        await self.prompt_configuration(guild)

    @commands.command(
        name="configure", pass_context=True, aliases=["config", "c"])
    async def configure(self, ctx):
        """ Configure bot preference settings
"""
        def check(message):
            return message.author.id == ctx.author.id

        # Display current bot preference settings
        # List the possible settings guild owner can configure
        embed = discord.Embed(
            title="Bot Preference Configuration",
            color=0xff0000
        )
        for field in self.configure_fields:
            embed.add_field(
                name=field,
                value=self.configure_fields[field])
        embed.set_footer(text="Type 'quit' to quit")
        config_message = await ctx.channel.send(embed=embed)
        while True:
            option = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=check(message)
            ).lower()
            config_funcs = {
                "everyone": self.c_everyone, "roles": self.c_roles,
                "members": self.c_members, "channel": self.c_channel
            }
            if option == "quit":
                break
            elif option in config_funcs:
                await config_funcs[option](ctx)
        await config_message.delete()

    @commands.command(
        name="preferences", pass_context=True, aliases=["prefs", "p"])
    async def preferences(self, ctx):
        """ View bot preference settings
"""
        # Get data from db preferences table
        select_preferences_table = """
        SELECT *
        FROM preferences
        WHERE preferences.GuildID=?"""
        prefs = self.bot.connection.execute_read_query(
            select_preferences_table, ctx.guild.id
        )
        prefs = [p for p in prefs if p is not None]
        columns = [d[0] for d in self.bot.connection.cursor.description]
        preferences = dict(zip(columns, prefs))
        # Send preferences data to channel
        embed = discord.Embed(
            title=f"Preferences for {ctx.guild.name}",
            color=0xff0000
        )
        for pref in preferences:
            embed.add_field(name=pref, value=preferences[pref])
        await ctx.channel.send(embed=embed)

    async def c_everyone(self, ctx):
        pass

    async def c_roles(self, ctx):
        pass

    async def c_members(self, ctx):
        pass

    async def c_channel(self, ctx):
        pass

    async def prompt_configuration(self, guild):
        """ Send embed in direct message channel to guild owner
"""
        direct_message = await guild.owner.create_dm()
        embed = discord.Embed(
            title="Thank you for choosing the Anti-GhostPing bot!",
            color=0xff0000
        )
        fields = self.prompt_fields
        fields["Added to Guild"] = fields["Added to Guild"].format(
            guild.name, guild.id
        )
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        await direct_message.send(embed=embed)


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
        # Get guild preferences from db.sqlite
        prefs = self.bot.connection.execute_read_query(
            "SELECT * FROM preferences"
        )
        columns = [d[0] for d in self.bot.connection.cursor.description]
        list_preferences = [dict(zip(columns, r)) for r in prefs]
        preferences = {d["GuildID"]: d for d in list_preferences}.get(
            message.guild.id, None
        )
        # Get ping detection preferences from guild preferences
        if preferences is None:
            preferences = {
                "roles": True, "members": False, "everyone": True
            }
        # Parse message for raw mentions and flags for specified preferences
        flags = {}
        # Check for role mentions
        if preferences["roles"] and message.raw_role_mentions:
            role_mentions = [
                discord.utils.get(message.guild.roles, id=i).name
                for i in message.raw_role_mentions
            ]
            flags.setdefault("Roles Mentioned", ", ".join(role_mentions))
        # Check for member mentions
        if preferences["members"] and message.raw_mentions:
            raw_mentions = [
                discord.utils.get(message.guild.members, id=i).name
                for i in message.raw_mentions
            ]
            flags.setdefault("Members Mentioned", ", ".join(raw_mentions))
        # Check for everyone mentions
        if preferences["everyone"] and message.mention_everyone:
            flags.setdefault("Other Groups Mentioned", "everyone")
        return flags

    async def detected(self, message, flags):
        """ Alert guild by sending message to specified channel
"""
        # Get guild preferences from db.sqlite
        prefs = self.bot.connection.execute_read_query(
            "SELECT * from preferences"
        )
        columns = [d[0] for d in self.bot.connection.cursor.description]
        list_preferences = [dict(zip(columns, r)) for r in prefs]
        preferences = {d["GuildID"]: d for d in list_preferences}.get(
            message.guild.id, None
        )
        # Get notification channel preferences from guild preferences
        if preferences is None:
            channel = message.channel
        else:
            channel = discord.utils.get(
                message.guild.channels,
                id=preferences["ChannelID"]
            )
            if channel is None:
                channel = message.channel
        # Send notifying embed to specified channel
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
