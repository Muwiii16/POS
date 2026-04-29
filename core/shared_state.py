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
    write_cart([])
