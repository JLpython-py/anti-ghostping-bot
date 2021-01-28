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
        # Insert default values
        insert_new_guild_preferences = """
                INSERT INTO preferences (GuildID)
                VALUES (?)
                """
        self.bot.connection.execute_write_query(
            insert_new_guild_preferences, guild.id
        )
        await self.initial_message(guild)

    @commands.command(
        name="preferences", pass_context=True, aliases=["prefs", "p"])
    async def preferences(self, ctx):
        """ View bot preference settings
"""
        # Get data from db preferences table
        select_preferences_table = """
        SELECT *
        FROM preferences
        WHERE GuildID=?"""
        prefs = self.bot.connection.execute_read_query(
            select_preferences_table, ctx.guild.id
        )[0]
        columns = [d[0] for d in self.bot.connection.cursor.description]
        preferences = dict(zip(columns, prefs))
        # Send preferences data to channel
        embed = discord.Embed(
            title=f"Preferences for {ctx.guild.name}",
            color=0xff0000
        )
        for pref in preferences:
            if pref in ["everyone", "members", "roles"]:
                sett = "ON" if preferences[pref] == 1 else "OFF"
            elif pref == "channel":
                sett = discord.utils.get(
                    ctx.guild.channels, id=preferences[pref]
                )
            else:
                sett = preferences[pref]
            embed.add_field(name=pref, value=sett)
        await ctx.channel.send(embed=embed)

    @commands.command(
        name="configure", pass_context=True, aliases=["config", "c"])
    async def configure(self, ctx, setting="", set_to=""):
        """ Configure bot preference settings
"""
        if (
                setting.lower() in ["everyone", "members", "roles"]
                and set_to.upper() in ["ON", "OFF"]
        ):
            self.configure_mention(ctx, setting.lower(), set_to.upper())
            await ctx.send(
                f"`{setting.lower()}` configured to {set_to.upper()}"
            )
        elif (
                setting.lower() == "channel"
                and ctx.message.channel_mentions
        ):
            self.configure_channel(ctx, ctx.message.channel_mentions[0])
            await ctx.send(
                f"`channel` configured to {set_to.upper()}"
            )
        else:
            await self.configuration_prompt(ctx)

    async def configuration_prompt(self, ctx):
        """ Send prompt with instructions for configuring bot preferences
"""
        def check(mess):
            return mess.author.id == ctx.author.id

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
        message = await ctx.channel.send(embed=embed)
        while True:
            try:
                msg = await self.bot.wait_for(
                    "message",
                    timeout=30.0,
                    check=check)
            except asyncio.TimeoutError:
                break
            setting = msg.content.lower()
            if setting in ["everyone", "roles", "members"]:
                await self.process_mention_config(ctx, setting)
                await msg.delete()
            elif setting == "channel":
                await self.process_channel_config(ctx)
                await msg.delete()
            elif setting == "defaults":
                await self.process_default_config(ctx)
                await msg.delete()
                break
            else:
                await msg.delete()
                break
        await message.delete()

    async def process_mention_config(self, ctx, setting):
        """ Send specific prompt for user to manage mention preferences
"""
        messages = {"ON": True, "OFF": False}

        def check(mess):
            return (
                (mess.author.id == ctx.guild.owner.id)
                and (mess.content.upper() in messages)
            )

        # Get current preference setting
        current_settings_query = """
        SELECt *
        FROM preferences
        WHERE GuildID=?
        """
        prefs = self.bot.connection.execute_read_query(
            current_settings_query, ctx.guild.id
        )[0]
        columns = [d[0] for d in self.bot.connection.cursor.description]
        current = "ON" if dict(zip(columns, prefs))[setting] else "OFF"
        # Send an embed with reactions for guild owner to use
        embed = discord.Embed(
            gtitle=f"Confiure `{setting}`",
            color=0xff0000
        )
        fields = {
            "Current Configuration": f"`everyone`={current}",
            "Configure Setting": "ON/OFF"
        }
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        message = await ctx.channel.send(embed=embed)
        # Use guild owner input to configure setting in database
        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=30.0,
                check=check)
        except asyncio.TimeoutError:
            await message.delete()
            return
        set_to = "ON" if messages[msg.content.upper()] else "OFF"
        self.configure_mention(ctx, setting, set_to)
        await message.edit(
            content=f"`{setting}` configured to {set_to}",
            embed=None
        )
        await msg.delete()

    async def process_channel_config(self, ctx):
        """ Send specific prompt for user to manage channel preference
"""
        def check(mess):
            return (
                (mess.author.id == ctx.guild.owner.id)
                and (len(mess.channel_mentions) == 1)
            )

        # Get current preference setting
        current_settings = """
        SELECT channel
        FROM preferences
        WHERE GuildID=?
        """
        prefs = self.bot.connection.execute_read_query(
            current_settings, ctx.guild.id
        )[0]
        columns = [d[0] for d in self.bot.connection.cursor.description]
        logging.info(dict(zip(columns, prefs)))
        current = dict(zip(columns, prefs))["channel"]
        try:
            channel = discord.utils.get(
                ctx.guild.channels, id=current
            ).name
        except AttributeError:
            channel = "NOT SET"
        # Send an embed with configuratio instructions
        embed = discord.Embed(
            title="Configure `channel`",
            color=0xff0000
        )
        fields = {
            "Current Configuration": f"`channel`={channel}",
            "Configure Setting": "Mention a channel"
        }
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        message = await ctx.channel.send(embed=embed)
        # User guild owner input to configure setting in database
        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=30.0,
                check=check
            )
        except asyncio.TimeoutError:
            await message.delete()
            return
        set_to = msg.channel_mentions[0]
        self.configure_channel(ctx, set_to)
        await message.edit(
            content=f"`channel` configured to {set_to}",
            embed=None
        )
        await msg.delete()

    async def process_default_config(self, ctx):
        """ Confirm that user desires to revert bot preferences to defaults
"""
        def check(mess):
            return mess.author.id == ctx.author.id

        desc = "Are you sure you want to revert bot preferences to defaults?"
        embed = discord.Embed(
            title=":x: Set Guild Preferences to Default :x:",
            description=desc,
            footer_text="(y/n)",
            color=0xff0000
        )
        message = await ctx.channel.send(embed=embed)
        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=30.0,
                check=check
            )
        except asyncio.TimeoutError:
            await message.delete()
            return
        if msg.content.lower().startswith('y'):
            self.default_preferences(ctx)
            embed = discord.Embed(
                title="Bot Preferences Reverted to Default",
                color=0xff0000
            )
            await message.edit(
                embed=embed
            )
        await msg.delete()

    def configure_mention(self, ctx, setting, set_to):
        """ Update database to match new guild mention preferences
"""
        if setting == "everyone":
            new_setting_query = """
            UPDATE preferences
            SET everyone=?
            WHERE GuildID=?
            """
        elif setting == "roles":
            new_setting_query = """
            UPDATE preferences
            SET roles=?
            WHERE GuildID=?
            """
        elif setting == "members":
            new_setting_query = """
            UPDATE preferences
            SET members=?
            WHERE GuildID=?
            """
        else:
            return
        set_to = 1 if set_to == "ON" else 0
        self.bot.connection.execute_write_query(
            new_setting_query, set_to, ctx.guild.id
        )

    def configure_channel(self, ctx, channel):
        """ Update database to match new guild channel preference
"""
        new_setting_query = """
        UPDATE preferences
        SET channel=?
        WHERE GuildID=?
        """
        self.bot.connection.execute_write_query(
            new_setting_query, channel.id, ctx.guild.id
        )

    def default_preferences(self, ctx):
        """ Set guild bot preferences to default settings
"""
        delete_guild_query = """
        DELETE FROM preferences
        """
        self.bot.connection.execute_write_query(
            delete_guild_query
        )
        create_guild_query = """
        INSERT INTO preferences (GuildID)
        VALUES (?)
        """
        self.bot.connection.execute_write_query(
            create_guild_query, ctx.guild.id
        )

    async def initial_message(self, guild):
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
        select_preferences_table = """
        SELECT 
            roles,
            members,
            everyone
        FROM 
            preferences
        WHERE GuildID=?"""
        prefs = self.bot.connection.execute_read_query(
            select_preferences_table, message.guild.id
        )[0]
        headers = [d[0] for d in self.bot.connection.cursor.description]
        preferences = dict(zip(headers, prefs))
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
        select_preferences_table = """
        SELECT channel
        FROM preferences
        WHERE GuildID=?"""
        prefs = self.bot.connection.execute_read_query(
            select_preferences_table, message.guild.id
        )[0]
        columns = [d[0] for d in self.bot.connection.cursor.description]
        preferences = dict(zip(columns, prefs))
        # Get notification channel preferences from guild preferences
        if preferences is None:
            channel = message.channel
        else:
            channel = discord.utils.get(
                message.guild.channels,
                id=preferences["channel"]
            )
            if channel is None:
                channel = message.channel
        # Send notifying embed to specified channel
        embed = discord.Embed(
            title="Ghost Ping Detected :no_entry_sign: :ghost:",
            color=0x0000ff
        )
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
