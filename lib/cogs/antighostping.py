#! python3
# anti-ghostping.py

"""
Anti-GhostPing discord.exts.commands.Cog Cog
- Parse delete messages for ghost pings
- Flags all mentions which are set to 1 in data/db/db.sqlite
    - Bot preferences can be modified with the configuration cog
- Sends notification to specified channel
    - Default channel is the channel where the message occurred
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

import discord
from discord.ext import commands


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
        columns, prefs = self.bot.connection.execute_query(
            select_preferences_table, "rr",
            message.guild.id
        )
        preferences = dict(zip(columns, prefs[0]))
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
        columns, prefs = self.bot.connection.execute_query(
            select_preferences_table, "rr",
            message.guild.id
        )
        preferences = dict(zip(columns, prefs[0]))
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


def setup(bot):
    """ Allow lib.bot.__init__.py to add AntiGhostPing cog as an extension
"""
    bot.add_cog(AntiGhostPing(bot))
