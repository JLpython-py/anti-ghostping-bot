#! python3
# db.py

"""
Manages the SQLite database in data/db
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

    def execute_query(self, query, mode, *args):
        """ Pass the given query to the cursor under the determined mode
"""
        mode = mode.lower()
        if mode not in ["r", "rr", "w"]:
            return
        if "w" in mode:
            self.cursor.execute(query, tuple(args))
            self.connection.commit()
        elif "r" in mode:
            self.cursor.execute(query, tuple(args))
            if mode == "rr":
                return [
                    [d[0] for d in self.cursor.description],
                    self.cursor.fetchall()
                ]
            else:
                return self.cursor.fetchall()
