import json
import csv
from datetime import datetime
import os

from thefuzz import process
from . models import Product
CURRENT_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(CURRENT_DIR, 'inventory.json')


def search_products(query, store_products):
    if not query.strip():
        return []

    product_names = list(set(item.name for item in store_products))

    matches = process.extract(query, product_names, limit=5)
    valid_names = [name for name, score in matches if score >= 60]

    results = [item for item in store_products if item.name in valid_names]
    return results


def add_bulk_cart(product, quantity, cart):
    if product.stock >= quantity:
        product.stock -= quantity
        for _ in range(quantity):
            cart.append(product)

        total = sum(p.price for p in cart)
        return True, total
    else:
        return False, f'Only {product.stock} items available!'


def get_grouped_cart(cart):
    grouped = {}
    for item in cart:
        key = (item.name, item.get_variant_label())
        if key not in grouped:
            grouped[key] = [item, 0]
        grouped[key][1] += 1
    return grouped


def remove_item_from_cart(product, cart):
    for i, item in enumerate(cart):
        if item.name == product.name and item.get_variant_label() == product.get_variant_label():
            cart.pop(i)
            product.stock += 1
            return True
    return False


def get_change_info(payment_text, total):
    try:
        payment = float(payment_text)if payment_text else 0
        change = payment-total
        if change >= 0:
            return f'Change: ₱{change:.2f}', 'green'
        else:
            return 'Insufficient Amout', 'red'
    except ValueError:
        return 'Invalid Amount', 'red'


def calculate_totals(cart):
    return sum(item.price for item in cart)


def process_checkout(cart, amount_paid, store_products):
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

    log_sale(cart, total, paid, change)
    save_inventory(store_products)

    return True, total, change


def generate_receipt_text(cart, total, paid, change):
    receipt = '------------RECEIPT------------\n'
    grouped = get_grouped_cart(cart)
    for (name, variant_label), (prod, qty) in grouped.items():
        receipt += f'{qty}x {name} ({variant_label}) - ₱{prod.price*qty:.2f}\n'
    receipt += f'-------------------------------\n'
    receipt += f'TOTAL: ₱{total:.2f}\n'
    receipt += f'PAID: ₱{paid:.2f}\n'
    receipt += f'CHANGE: ₱{change:.2f}'
    return receipt


def log_sale(cart, total, paid, change):
    file_path = 'sales_log.csv'
    file_exists = os.path.isfile(file_path)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(file_path, mode='a', newline='')as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['Timestamp', 'Items Sold',
                            'Total', 'Amount Paid'])

        item_summary = ' | '.join(
            f'{item.name}({item.get_variant_label()})' for item in cart)

        writer.writerow(
            [now, item_summary, f'{total:.2f}', f'{paid:.2f}'])


def load_inventory():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return [Product(**item) for item in data]


def save_inventory(products):
    data = []
    for p in products:
        item_dict = {
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "category": p.category,
            "barcode": p.barcode
        }
        item_dict.update(p.metadata)
        data.append(item_dict)

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
