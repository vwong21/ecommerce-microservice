from sqlalchemy import Column, Integer, String, DateTime, Float
from base import Base


class Stats(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    number_products = Column(Integer, nullable=False)
    number_orders = Column(Integer, nullable=False)
    highest_product_price = Column(Float, nullable=False)
    highest_order_price = Column(Float, nullable=False)
    highest_product_quantity = Column(Integer, nullable=False)
    highest_order_quantity = Column(Integer, nullable=False)

    def __init__(
        self,
        number_products,
        number_orders,
        highest_product_price,
        highest_order_price,
        highest_product_quantity,
        highest_order_quantity,
    ):
        self.number_products = number_products
        self.number_orders = number_orders
        self.highest_product_price = highest_product_price
        self.highest_order_price = highest_order_price
        self.highest_product_quantity = highest_product_quantity
        self.highest_order_quantity = highest_order_quantity

    def to_dict(self):
        dict = {}
        dict["number_products"] = self.number_products
        dict["number_orders"] = self.number_orders
        dict["highest_product_price"] = self.highest_product_price
        dict["highest_order_price"] = self.highest_order_price
        dict["highest_product_quantity"] = self.highest_product_quantity
        dict["highest_order_quantity"] = self.highest_order_quantity

        return dict
