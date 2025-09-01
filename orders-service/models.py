from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# 🧑 Customer Model
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    nickname = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())

    # 👇 Always eager load orders
    orders = relationship(
        "OrderItem",
        back_populates="customer",
        lazy="selectin"
    )

# 📦 Inventory Model
class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    emoji = Column(String)
    price = Column(Integer)
    sku = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, nullable=False)

    # 👇 Always eager load order links
    orders = relationship(
        "OrderInventoryLink",
        back_populates="inventory",
        lazy="selectin"
    )

# 🧾 Order Model
class OrderItem(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(Integer, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())

    customer_id = Column(Integer, ForeignKey("customers.id"))

    # 👇 Always eager load customer + items
    customer = relationship(
        "Customer",
        back_populates="orders",
        lazy="selectin"
    )

    items = relationship(
        "OrderInventoryLink",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

# 🔗 Association Table
class OrderInventoryLink(Base):
    __tablename__ = "order_inventory_link"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Integer, nullable=False)

    # 👇 Always eager load order + inventory
    order = relationship(
        "OrderItem",
        back_populates="items",
        lazy="selectin"
    )
    inventory = relationship(
        "InventoryItem",
        back_populates="orders",
        lazy="selectin"
    )
