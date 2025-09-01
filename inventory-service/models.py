from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    emoji = Column(String)
    price = Column(Integer)
    sku = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, nullable=False)
