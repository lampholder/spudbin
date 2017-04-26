import sqlite3

_CONNECTION = None

def connect(filename='tokens.db'):
    global _CONNECTION

    _CONNECTION = sqlite3.connect(filename)
    _CONNECTION.row_factory = sqlite3.Row

def connection():
    global _CONNECTION
    if _CONNECTION is None:
        connect()
    return _CONNECTION
