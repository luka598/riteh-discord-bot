import sqlite3


class Database:
    def __init__(self, name: str) -> None:
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()
