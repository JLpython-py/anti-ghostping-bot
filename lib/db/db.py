import os
import sqlite3

class DBConnection:
    """ Connect to data/db/db.sqlite
"""
    def __init__(self, path):
        self.connection = sqlite3.connect(
            os.path.join(path, 'db.sqlite')
        )
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """ Close database connection
"""
        self.connection.close()

    def execute_query(self, query):
        """ Pass the given query to the cursor and commit the connection
"""
        self.cursor.execute(query)
        self.connection.commit()
