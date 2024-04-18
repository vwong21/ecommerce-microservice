import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect("anomalies.sqlite")

c = conn.cursor()
c.execute(
    """
        CREATE TABLE events
            (id INTEGER PRIMARY KEY ASC,
            trace_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            anomaly_type TEXT NOT NULL,
            description TEXT NOT NULL,
            anomaly_datetime TEXT NOT NULL)
"""
)

conn.commit()
conn.close()
