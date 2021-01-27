from . import db


GUILD_QUERY = """CREATE TABLE IF NOT EXISTS guilds (
    GuildID integer PRIMARY KEY,
    prefix text DEFAULT "@."
);"""

PREFERENCES_QUERY = """CREATE TABLE IF NOT EXISTS preferences (
    GuildID integer PRIMARY KEY,
    everyone integer DEFAULT 1,
    roles integer DEFAULT 1,
    members integer DEFAULT 0,
    ChannelID integer
);"""

CONNECTION = db.DBConnection()
CONNECTION.execute_write_query(GUILD_QUERY)
CONNECTION.execute_write_query(PREFERENCES_QUERY)
