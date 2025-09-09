import asyncio
import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from db import engine
from models import Base, InventoryItem


# 🧸 Emoji map by category
emoji_map = {
  "tools":       ["🔧", "🪛", "🔨", "⚙️", "🛠️", "🗜️", "🪚", "🪓", "🔩", "🧰", "🧱", "🧪", "🧲"],
  "electronics": ["💻", "📱", "🖥️", "🖨️", "🔋", "📷", "🎧", "📺", "🕹️", "🖱️", "⌨️", "📡", "🔌"],
  "furniture":   ["🪑", "🛏️", "🛋️", "🗄️", "🚪", "🪟", "🪞", "🛁", "🚽", "🪜", "🧴", "🧻"],
  "toys":        ["🧸", "🎲", "🪀", "🎯", "🪁", "🧩", "🎮", "🪆", "🪅", "🛼", "🛹", "🧃"],
  "kitchen":     ["🍴", "🥄", "🧂", "🍳", "🫙", "🥣", "🥡", "🧊", "🧇", "🍽️", "🫕", "🧁"],
  "sports":      ["⚽", "🏀", "🏈", "🎾", "🥏", "🏐", "🏓", "🥊", "⛳", "🏸", "🎳", "🛷", "⛷️"],
  "garden":      ["🌻", "🪴", "🌿", "🧤", "🪓", "🌱", "🧹", "🧺", "🪠", "🧼", "🪵", "🧽"],
  "clothing":    ["👕", "👖", "🧥", "👗", "🧢", "👚", "👘", "🥼", "🧦", "👒", "👟", "🥾", "🥿"],
  "books":       ["📚", "📖", "📘", "📙", "📕", "📗", "📓", "📒", "📔", "📑", "📰", "📎"],
  "pets":        ["🐶", "🐱", "🐹", "🐰", "🐦", "🐢", "🐠", "🦜", "🐕", "🐈", "🦎", "🐇"],
  "household":   ["🧼", "🧽", "🧺", "🧻", "🪣", "🧊", "🧴", "🧹", "🪠", "🧯", "🧪"],
  "travel":      ["🧳", "🎒", "⛺", "🗺️", "🧭", "🚲", "🛶", "🛴", "🛵", "🚐", "🏕️", "🌄"]
}



# 🔢 Helpers
def generate_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def random_timestamp():
    now = datetime.now(timezone.utc)
    delta = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
    return now - delta

# 🏗️ Generate inventory
def generate_inventory(n=500):
    items = []
    categories = list(emoji_map.keys())
    for _ in range(n):
        category = random.choice(categories)
        emoji = random.choice(emoji_map[category])
        item = InventoryItem(
            name=f"{category.capitalize()} Item {random.randint(1, 999)}",
            sku=generate_sku(),
            quantity=random.randint(5000, 50000),
            price=random.randint(100, 9999),
            emoji=emoji
        )
        items.append(item)
    return items


# 🚀 Async seed function
async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        inventory = generate_inventory()

        session.add_all(inventory )
        await session.commit()
        print(f"🧪 Number of itmes restocked - {len(inventory)}", flush=True)

    print("✅ Seeded inventory.", flush=True)

if __name__ == "__main__":
    asyncio.run(seed())
