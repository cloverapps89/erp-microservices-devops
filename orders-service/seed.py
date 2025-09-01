import asyncio
import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from db import engine
from models import Base, Customer, InventoryItem, OrderItem, OrderInventoryLink

# 🧸 Emoji map by category
emoji_map = {
    "tools":       ["🔧", "🪛", "🔨", "⚙️", "🛠️"],
    "electronics": ["💻", "📱", "🖥️", "🖨️", "🔋"],
    "furniture":   ["🪑", "🛏️", "🛋️", "🗄️", "🚪"],
    "toys":        ["🧸", "🎲", "🪀", "🎯", "🪁"],
    "kitchen":     ["🍴", "🥄", "🧂", "🍳", "🫙"],
    "sports":      ["⚽", "🏀", "🏈", "🎾", "🥏"],
    "garden":      ["🌻", "🪴", "🌿", "🧤", "🪓"],
    "clothing":    ["👕", "👖", "🧥", "👗", "🧢"],
    "books":       ["📚", "📖", "📘", "📙", "📕"],
    "pets":        ["🐶", "🐱", "🐹", "🐰", "🐦"],
}

# 🧑 Customer map
customer_data = [
    {"name": "Alice Johnson",     "nickname": "AJ",     "email": "alice.j@example.com"},
    {"name": "Robert Smith",      "nickname": "Bobby",  "email": "robert.smith@example.com"},
    {"name": "Cynthia Lee",       "nickname": "Cyn",    "email": "cynthia.lee@example.com"},
    {"name": "David Martinez",    "nickname": "Dave",   "email": "d.martinez@example.com"},
    {"name": "Emily Chen",        "nickname": "Em",     "email": "emily.chen@example.com"},
    {"name": "Franklin Wright",   "nickname": "Frank",  "email": "frank.w@example.com"},
    {"name": "Grace Thompson",    "nickname": "Gracie", "email": "grace.t@example.com"},
    {"name": "Henry Patel",       "nickname": "Hank",   "email": "henry.patel@example.com"},
    {"name": "Isabella Nguyen",   "nickname": "Izzy",   "email": "isabella.n@example.com"},
    {"name": "Jason Kim",         "nickname": "Jay",    "email": "jason.kim@example.com"},
]

# 🔢 Helpers
def generate_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def random_timestamp():
    now = datetime.now(timezone.utc)
    delta = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
    return now - delta

# 🏗️ Generate inventory
def generate_inventory(n=200):
    items = []
    categories = list(emoji_map.keys())
    for _ in range(n):
        category = random.choice(categories)
        emoji = random.choice(emoji_map[category])
        item = InventoryItem(
            name=f"{category.capitalize()} Item {random.randint(1, 999)}",
            sku=generate_sku(),
            quantity=random.randint(1, 500),
            price=random.randint(100, 9999),
            emoji=emoji
        )
        items.append(item)
    return items

# 👥 Generate customers
def generate_customers(n=100):
    customers = []
    for i in range(n):
        data = customer_data[i % len(customer_data)]
        customer = Customer(
            name=data["name"],
            nickname=f"{data['nickname']}{i}",
            email=f"{data['email'].split('@')[0]}{i}@{data['email'].split('@')[1]}"
        )
        customers.append(customer)
    return customers

# 🧾 Generate orders
def generate_orders(customers, inventory, n=100):
    orders = []
    for i in range(n):
        customer = random.choice(customers)
        order = OrderItem(
            order_number=1000 + i,
            customer=customer,
            created_at=random_timestamp()
        )
        selected_items = random.sample(
            inventory, 
            k=min(len(inventory), random.randint(1, 5))
        )
        for item in selected_items:
            link = OrderInventoryLink(
                inventory=item,
                quantity=random.randint(1, 3),
                price_at_order=item.price
            )
            order.items.append(link)
        orders.append(order)
    return orders

# 🚀 Async seed function
async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        inventory = generate_inventory()
        customers = generate_customers()
        orders = generate_orders(customers, inventory)

        session.add_all(inventory + customers + orders)
        await session.commit()

    print("✅ Seeded inventory, customers, and orders.")

if __name__ == "__main__":
    asyncio.run(seed())
