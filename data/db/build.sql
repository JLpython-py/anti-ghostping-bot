CREATE TABLE IF NOT EXISTS preferences (
	GuildID integer PRIMARY KEY,
	detectEVERYONE boolean DEFAULT 1,
	detectROLES boolean DEFAULT 1,
	detectMEMBERS boolean DEFAULT 0
);