import asyncio
import random
import string
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from db import engine
from models import InventoryItem

SessionLocal = sessionmaker(bind=engine)

# 🧸 Emoji map by category
emoji_map = {
    "tools": ["🔧", "🪛", "🔨", "⚙️", "🛠️"],
    "electronics": ["💻", "📱", "🖥️", "🖨️", "🔋"],
    "furniture": ["🪑", "🛏️", "🛋️", "🗄️", "🚪"],
    "toys": ["🧸", "🎲", "🪀", "🎯", "🪁"],
    "kitchen": ["🍴", "🥄", "🧂", "🍳", "🫙"],
    "sports": ["⚽", "🏀", "🏈", "🎾", "🥏"],
}

# 🧠 Generate random SKU
def generate_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# 🏗️ Generate random items
def generate_items(n=100):
    items = []
    categories = list(emoji_map.keys())
    for _ in range(n):
        category = random.choice(categories)
        emoji = random.choice(emoji_map[category])
        name = f"{category.capitalize()} Item {random.randint(1, 999)}"
        sku = generate_sku()
        quantity = random.randint(1, 500)
        item = InventoryItem(name=name, sku=sku, quantity=quantity)
        item.emoji = emoji  # If you want to store emoji, add a column to your model
        items.append(item)
    return items

async def seed():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        items = generate_items(200)
        session.add_all(items)
        await session.commit()
    print("✅ Seeded 200 inventory items.")

if __name__ == "__main__":
    asyncio.run(seed())
