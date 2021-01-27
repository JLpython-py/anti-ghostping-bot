import os
import sqlite3


class DBConnection:
    """ Connect to data/db/db.sqlite
"""
    def __init__(self):
        self.connection = sqlite3.connect(
            os.path.join('data', 'db', 'db.sqlite')
        )
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """ Close database connection
"""
        self.connection.close()

    def execute_write_query(self, query):
        """ Pass the given query to the cursor and commit the connection
"""
        self.cursor.execute(query)
        self.connection.commit()

    def execute_read_query(self, query):
        """ Pass the given query to the cursor to read the database
"""
        self.cursor.execute(query)
        return self.cursor.fetchall()