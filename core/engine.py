import json
import csv
from datetime import datetime
import os
import copy
import barcode

from thefuzz import process
from barcode.writer import ImageWriter
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
    receipt = []
    receipt.append("      DAD'S STORE POS      ")
    receipt.append("   123 Business St, City   ")
    receipt.append("---------------------------")
    receipt.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    receipt.append("---------------------------")

    grouped_items = get_grouped_cart(cart)
    for (name, variant_label), (prod, qty) in grouped_items.items():
        display_name = f'{qty}x {name[:15]}'
        price_each = f'{prod.price * qty:.2f}'

        receipt.append(f'{display_name:<20}{price_each:7}')
        if variant_label:
            receipt.append(f"  ({variant_label})")

    receipt.append("---------------------------")
    receipt.append(f"TOTAL:           ₱{total:>9.2f}")
    receipt.append(f"CASH:            ₱{paid:>9.2f}")
    receipt.append(f"CHANGE:          ₱{change:>9.2f}")
    receipt.append("---------------------------")
    receipt.append("   THANK YOU FOR SHOPPING! ")

    return '\n'.join(receipt)


def log_sale(cart, total, paid, change):
    file_path = 'sales_log.csv'
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    today_date = now.strftime('%Y-%m-%d')

    item_summary = ' | '.join(
        f'{item.name}({item.get_variant_label()})' for item in cart)

    file_exists = os.path.isfile(file_path)
    is_new_day = False

    if file_exists:
        try:
            with open(file_path, 'r', encoding='utf-8')as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1]
                    if today_date not in last_line:
                        is_new_day = True
        except:
            pass

    with open(file_path, mode='a', newline='', encoding='utf-8')as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Items Sold',
                            'Total', 'Amount Paid'])

        if is_new_day:
            writer.writerow([])
            writer.writerow(
                [f'--- SESSION START: {today_date} ---', '-', '-', '-'])
            writer.writerow([])

        writer.writerow(
            [timestamp, item_summary, f'{total:.2f}', f'{paid:.2f}'])


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


def delete_product(product_to_remove, store_products):
    if product_to_remove in store_products:
        store_products.remove(product_to_remove)
        save_inventory(store_products)
        return True
    return False


class InventoryHistory:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def save_state(self, products):
        self.undo_stack.append(copy.deepcopy(products))
        self.redo_stack.clear()

    def undo(self, current_products):
        if not self.undo_stack:
            return None
        self.redo_stack.append(copy.deepcopy(current_products))
        return self.undo_stack.pop()

    def redo(self, current_products):
        if not self.redo_stack:
            return None
        self.undo_stack.append(copy.deepcopy(current_products))
        return self.redo_stack.pop()


history = InventoryHistory()


def add_new_product(product_data, store_products):
    from .models import Product

    core_fields = ['name', 'price', 'stock', 'category', 'barcode']
    name = product_data.get('name', '').strip().lower()
    barcode = product_data.get('barcode', '').strip()

    metadata = {k.lower(): str(v).strip().lower()
                for k, v in product_data.items() if k not in core_fields}

    for existing_prod in store_products:
        if barcode and existing_prod.barcode == barcode:
            return False, f'Error: Barcode "{barcode}" is already assigned to {existing_prod.name}.'

        existing_meta_check = {k.lower(): str(v).strip().lower()
                               for k, v in existing_prod.metadata.items()}
        if existing_prod.name.lower() == name and existing_meta_check == metadata:
            return False, f'Error: "{product_data['name']}" with these variants already exists!'

    display_metadata = {}
    for k, v in product_data.items():
        if k not in core_fields:
            key_str = str(k).strip().lower()
            val_str = str(v).strip()
            if key_str and val_str and val_str.lower() != 'none':
                display_metadata[key_str] = val_str.capitalize()

    product_data['name'] = product_data['name'].strip().title()
    product_data['category'] = product_data['category'].strip().capitalize()

    try:
        constructor_data = {k: product_data[k]
                            for k in core_fields if k in product_data}
        new_prod = Product(**constructor_data, **display_metadata)
        store_products.append(new_prod)
        save_inventory(store_products)
        return True, 'Product added successfully!'
    except Exception as e:
        return False, f'Failed to add: {str(e)}'


def get_daily_summary():
    file_path = 'sales_log.csv'
    today_str = datetime.now().strftime('%Y-%m-%d')

    summary = {
        "revenue": 0.0,
        "transactions": 0,
        "date": today_str,
        "category_sales": {}
    }

    if not os.path.exists(file_path):
        return summary

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8')as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp = row.get('Timestamp', '')
                if today_str in timestamp:
                    raw_total = float(row.get('Total', 0))
                    summary['revenue'] += raw_total
                    summary['transactions'] += 1

                    items_sold = row.get('Items Sold', '').split(' | ')
                    for item in items_sold:
                        cat = item.split('(')[0].strip()
                        summary['category_sales'][cat] = summary['category_sales'].get(
                            cat, 0)+1

        return summary
    except Exception as e:
        print(f'Error reading sales log: {e}')
        return summary


def generate_product_barcode(product_id):
    os.makedirs('barcodes', exist_ok=True)

    CODE = barcode.get_barcode_class('code128')

    writer_options = {
        'write_text': True,
        'module_height': 15.0,
        'font_size': 10,
        'text_disctance': 5.0,
        'quiet_zone': 6.0
    }

    my_barcode = CODE(str(product_id), writer=ImageWriter())
    file_path = os.path.join('barcodes', f'barcode_{product_id}')

    full_path = my_barcode.save(file_path, options=writer_options)
    return full_path
