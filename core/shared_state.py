import json
import os

CART_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'data', 'cart_state.json')


def write_cart(payload):
    with open(CART_FILE, 'w') as f:
        json.dump({'type': 'cart_update', 'payload': payload}, f)


def write_checkout_done():
    with open(CART_FILE, 'w') as f:
        json.dump({'type': 'checkout_done'}, f)


def read_cart():
    try:
        with open(CART_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def clear_cart_file():
    try:
        with open(CART_FILE, 'w') as f:
            json.dump({'type': 'idle'}, f)
    except Exception:
        pass


def write_checkout_done():
    with open(CART_FILE, 'w') as f:
        json.dump({'type': 'checkout_done'}, f)


def write_checkout_request(method, paid, total, partial_cash=0.0, cart_items=None):
    with open(CART_FILE, 'w') as f:
        json.dump({
            'type': 'checkout_request',
            'method': method,
            'paid': paid,
            'total': total,
            'partial_cash': partial_cash,
            'cart_items': cart_items or []
        }, f)


def write_main_checkout(active: bool):
    flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'data', 'main_checkout.json')
    with open(flag_file, 'w') as f:
        json.dump({'active': active}, f)


def is_main_checkout_active():
    flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'data', 'main_checkout.json')
    try:
        with open(flag_file, 'r') as f:
            return json.load(f).get('active', False)
    except Exception:
        return False
