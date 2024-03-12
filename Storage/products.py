from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql.functions import now
from base import Base


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    product_id = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)

    def __init__(self, product_id, name, price, quantity, date_created, trace_id):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.date_created = date_created
        self.trace_id = trace_id

    def to_dict(self):
        dict = {}
        dict["id"] = self.id
        dict["product_id"] = self.product_id
        dict["name"] = self.name
        dict["price"] = self.price
        dict["quantity"] = self.quantity
        dict["date_created"] = self.date_created
        dict["trace_id"] = self.trace_id

        return dict
