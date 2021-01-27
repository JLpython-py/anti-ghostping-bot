#! python3
# functional_tests.py

"""
Run bot script then delete any tables created in the database
"""

import asyncio
import os
import unittest

from lib.bot import BotRoot
from lib.db import db


class TestRunBot(unittest.TestCase):

    def setUp(self):
        self.connection = db.DBConnection()

    def tearDown(self):
        self.connection.execute_write_query("DELETE FROM guilds")
        self.connection.execute_write_query("DELETE FROM preferences")
        self.connection.close_connection()

    def test_run_bot(self):
        token = os.environ.get("token", None)
        if token is None:
            with open(os.path.join("lib", "bot", "token.txt")) as file:
                token = file.read()
        self.assertIsNotNone(token)
        loop = asyncio.get_event_loop()
        bot = BotRoot()
        loop.create_task(bot.start(token))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            bot.connection.close_connection()


if __name__ == '__main__':
    unittest.main()
