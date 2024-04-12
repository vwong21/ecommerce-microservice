from sqlalchemy import Column, Integer, DateTime, String
from base import Base
from datetime import datetime, timezone


class Events(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    code = Column(Integer, nullable=False)
    event_datetime = Column(DateTime, nullable=False)

    def __init__(
        self,
        message,
        code,
        event_datetime=None,
    ):
        self.message = message
        self.code = code
        if datetime is None:
            self.event_datetime = datetime.now(timezone.utc)
        else:
            self.event_datetime = event_datetime

    def to_dict(self):
        dict = {}
        dict["message"] = self.message
        dict["code"] = self.code
        dict["event_datetime"] = self.event_datetime

        return dict
