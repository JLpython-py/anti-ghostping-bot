#! python3
# configuration.py

"""
Configuration discord.exts.Cogs Cog
- Allow guild owners to customize bot preferences for their guild
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
import os

import discord
from discord.ext import commands


class Configuration(commands.Cog):
    """ Allow guild owners to configure bot preferences
"""
    def __init__(self, bot):
        self.directory = os.path.join("data", "Configuration")
        self.bot = bot
        with open(
                os.path.join(self.directory, "join_message.txt")
        ) as file:
            self.guild_join_fields = json.load(file)
        with open(
                os.path.join(self.directory, "remove_message.txt")
        ) as file:
            self.guild_remove_fields = json.load(file)
        with open(os.path.join(
                self.directory, "configure.txt"
        )) as file:
            self.configure_fields = json.load(file)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Send message to owner when the bot is added to a guild
"""
        # Insert default values
        query = """
        INSERT INTO preferences (GuildID)
        VALUES (?)
        """
        self.bot.connection.execute_query(
            query, "w",
            guild.id
        )
        await self.join_message(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Send message to owner when the bot is removed from a guild
"""
        # Delete guild table
        query = """
        DELETE
        FROM preferences
        WHERE GuildID=?
        """.format(guild.id)
        self.bot.connection.execute_query(
            query, "w",
            guild.id
        )
        await self.remove_message(guild)

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
        columns, prefs = self.bot.connection.execute_query(
            select_preferences_table, "rr",
            ctx.guild.id
        )
        preferences = dict(zip(columns, prefs[0]))
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
            return mess.author.guild_permissions.administrator

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
                (mess.content.upper() in messages)
                and mess.author.guild_permissions.administrator
            )

        # Get current preference setting
        current_settings_query = """
        SELECT *
        FROM preferences
        WHERE GuildID=?
        """
        columns, prefs = self.bot.connection.execute_query(
            current_settings_query, "rr",
            ctx.guild.id
        )
        current = "ON" if dict(zip(columns, prefs[0]))[setting] else "OFF"
        # Send an embed with reactions for guild owner to use
        embed = discord.Embed(
            gtitle=f"Confiure `{setting}`",
            color=0xff0000
        )
        fields = {
            "Current Configuration": f"`{setting}`={current}",
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
                (len(mess.channel_mentions) == 1)
                and mess.author.guild_permissions.administrator
            )

        # Get current preference setting
        current_settings = """
        SELECT channel
        FROM preferences
        WHERE GuildID=?
        """
        columns, prefs = self.bot.connection.execute_query(
            current_settings, "rr",
            ctx.guild.id
        )
        current = dict(zip(columns, prefs[0]))["channel"]
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
            return mess.author.guild_permissions.administrator

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
        self.bot.connection.execute_query(
            new_setting_query, "w",
            set_to, ctx.guild.id
        )

    def configure_channel(self, ctx, channel):
        """ Update database to match new guild channel preference
"""
        new_setting_query = """
        UPDATE preferences
        SET channel=?
        WHERE GuildID=?
        """
        self.bot.connection.execute_query(
            new_setting_query, "w",
            channel.id, ctx.guild.id
        )

    def default_preferences(self, ctx):
        """ Set guild bot preferences to default settings
"""
        delete_guild_query = """
        DELETE FROM preferences
        """
        self.bot.connection.execute_query(
            delete_guild_query, "w"
        )
        create_guild_query = """
        INSERT INTO preferences (GuildID)
        VALUES (?)
        """
        self.bot.connection.execute_query(
            create_guild_query, "w",
            ctx.guild.id
        )

    async def join_message(self, guild):
        """ Send embed in direct message channel to guild owner
"""
        direct_message = await guild.owner.create_dm()
        embed = discord.Embed(
            title="Thank you for choosing the Anti-GhostPing bot!",
            color=0xff0000
        )
        fields = self.guild_join_fields
        fields["Added to Guild"] = fields["Added to Guild"].format(
            guild.name, guild.id
        )
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        await direct_message.send(embed=embed)

    async def remove_message(self, guild):
        """ Send embed in direct message channel to guild owner
"""
        direct_message = await guild.owner.create_dm()
        embed = discord.Embed(
            title="We are sorry to see you go!",
            color=0xff0000
        )
        fields = self.guild_remove_fields
        fields["Removed from Guild"] = fields["Removed from Guild"].format(
            guild.name, guild.id
        )
        for field in fields:
            embed.add_field(name=field, value=fields[field])
        await direct_message.send(embed=embed)


def setup(bot):
    """ Allow lib.bot.__init__.py to add Configuration cog as an extension
"""
    bot.add_cog(Configuration(bot))
