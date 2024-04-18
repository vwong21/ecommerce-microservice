from sqlalchemy import Column, Integer, DateTime, Float, String
from base import Base
from datetime import datetime, timezone


class Anomalies(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    anomaly_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    anomaly_datetime = Column(DateTime, nullable=False)

    def __init__(
        self, trace_id, event_type, anomaly_type, description, anomaly_datetime=None
    ):
        self.trace_id = trace_id
        self.event_type = event_type
        self.anomaly_type = anomaly_type
        self.description = description
        if anomaly_datetime is None:
            self.anomaly_datetime = datetime.now(timezone.utc)
        else:
            self.anomaly_datetime = anomaly_datetime

    def to_dict(self):
        dict = {}
        dict["trace_id"] = self.trace_id
        dict["event_type"] = self.event_type
        dict["anomaly_type"] = self.anomaly_type
        dict["description"] = self.description
        dict["anomaly_datetime"] = self.anomaly_datetime

        return dict
