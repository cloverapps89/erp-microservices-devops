from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nickname = Column(String, unique=False)
    email = Column(String, unique=False)

    orders = relationship("OrderItem", back_populates="customer")


class OrderItem(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(Integer, ForeignKey("customers.id"))

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderInventoryLink", back_populates="order")


class OrderInventoryLink(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True)
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Float, nullable=False)

    order_id = Column(Integer, ForeignKey("orders.id"))
    order = relationship("OrderItem", back_populates="items")
