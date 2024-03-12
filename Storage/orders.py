from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql.functions import now
from base import Base


class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(250), nullable=False)
    order_date = Column(DateTime, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)

    def __init__(
        self, customer_id, order_date, quantity, total_price, date_created, trace_id
    ):
        self.customer_id = customer_id
        self.order_date = order_date
        self.quantity = quantity
        self.total_price = total_price
        self.date_created = date_created
        self.trace_id = trace_id

    def to_dict(self):
        dict = {}
        dict["id"] = self.id
        dict["customer_id"] = self.customer_id
        dict["order_date"] = self.order_date
        dict["quantity"] = self.quantity
        dict["total_price"] = self.total_price
        dict["date_created"] = self.date_created
        dict["trace_id"] = self.trace_id

        return dict
