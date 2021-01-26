import os
from sqlite3 import connect

DB_PATH = "./data/db/database.db"
BUILD_PATH = "./data/db/build.sql"

CONNECTION = connect(DB_PATH, check_same_thread=False)
CURSOR = CONNECTION.cursor()

def with_commit(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit()

    return inner


@with_commit
def build():
    if os.path.isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)

def commit():
    CONNECTION.commit()

def close():
    CONNECTION.close()

def field(command, *values):
    CURSOR.execute(command, tuple(values))

    if (fetch := CURSOR.fetchone()) is not None:
        return fetch[0]

def record(command, *values):
    CURSOR.execute(command, tuple(values))

    return CURSOR.fetchone()

def records(command, *values):
    CURSOR.execute(command, tuple(values))

    return CURSOR.fetchall()

def column(command, *values):
    CURSOR.execute(command, tuple(values))

    return [item[0] for item in CURSOR.fetchall()]

def execute(command, *values):
    CURSOR.execute(command, tuple(values))

def multiexec(command, valueset):
    CURSOR.executemany(command, valueset)

def scriptexec(path):
    with open(path, "r", encoding-'utf-8') as script:
        CURSOR.executescript(script.read()))
