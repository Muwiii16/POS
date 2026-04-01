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


def log_sale(cart, total, amount_paid, change):
    file_path = 'sales_log.csv'
    file_exists = os.path.isfile(file_path)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(file_path, mode='a', newline='')as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['Timestamp', 'Items Sold',
                            'Total', 'Amount Paid', 'Change'])

        item_summary = ' | '.join(
            f'{item.name}({item.variant})' for item in cart)

        writer.writerow(
            [now, item_summary, f'{total:.2f}', f'{amount_paid:.2f}', f'{change:.2f}'])


def load_inventory():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return [Product(**item) for item in data]


def save_inventory(products):
    data = [vars(p) for p in products]
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
