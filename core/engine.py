from thefuzz import process


def search_products(query, store_products):
    if not query.strip():
        return []

    product_names = list(set(item.name for item in store_products))

    matches = process.extract(query, product_names, limit=5)
    valid_names = [name for name, score in matches if score >= 60]

    results = [item for item in store_products if item.name in valid_names]
    return results


def calculate_totals(cart):
    return sum(item.price for item in cart)


def process_checkout(cart, amount_paid):
    if not cart:
        return False, 0, "Your cart is empty!"
    if not amount_paid.strip():
        return False, 0, "Please enter the payment amount."

    total = calculate_totals(cart)

    try:
        paid = float(amount_paid)
    except ValueError:
        return False, total, f"Invalid payment amount. Please enter a valid number."

    if paid < total:
        return False, total, f"Insufficient funds. Need ₱{total-paid:.2f} more."

    change = paid-total
    return True, total, change


def generate_receipt_text(cart, total, paid, change):
    receipt = '---RECEIPT---\n'
    for item in cart:
        receipt += f'{item.name} ({item.variant}) - ₱{item.price:.2f}\n'
    receipt += f'---------------------\n'
    receipt += f'TOTAL: ₱{total:.2f}\n'
    receipt += f'PAID: ₱{paid:.2f}\n'
    receipt += f'CHANGE: ₱{change:.2f}'
    return receipt
