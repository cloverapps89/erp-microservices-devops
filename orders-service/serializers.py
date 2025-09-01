def serialize_order(order):
    return {
        "order_number": order.order_number,
        "customer": order.customer.nickname if order.customer else None,
        "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else None,
        "items": [
            {
                "name": link.inventory.name if link.inventory else None,
                "emoji": link.inventory.emoji if link.inventory else None,
                "quantity": link.quantity,
                "price": link.price_at_order
            }
            for link in order.items or []
        ]
    }
