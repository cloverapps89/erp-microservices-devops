from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    nickname = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())

    orders = relationship("OrderItem", back_populates="customer")


class OrderItem(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(Integer, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())

    customer_id = Column(Integer, ForeignKey("customers.id"))
    customer = relationship("Customer", back_populates="orders")

    items = relationship("OrderInventoryLink", back_populates="order", cascade="all, delete-orphan")


class OrderInventoryLink(Base):
    __tablename__ = "order_inventory_link"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    sku = Column(String, nullable=False)   # ✅ reference inventory by SKU, not foreign key
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Integer, nullable=False)

    order = relationship("OrderItem", back_populates="items")
