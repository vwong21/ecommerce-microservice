import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect("events.sqlite")

c = conn.cursor()
c.execute(
    """
        CREATE TABLE events
            (id INTEGER PRIMARY KEY ASC,
            message TEXT NOT NULL,
            code INTEGER NOT NULL,
            event_date TEXT NOT NULL
            )
"""
)

conn.commit()
conn.close()
