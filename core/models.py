# Blueprint for each classes
class Product:
    def __init__(self, name, price, stock, category, barcode, **kwargs):
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
        self.category = category
        self.barcode = barcode

        self.metadata = kwargs

    def get_variant_label(self):
        priority_keys = ['size', 'color', 'type', 'weight']
        parts = []

        for key in priority_keys:
            val = self.metadata.get(key)
            if val and str(val).lower() not in ['none', 'null', '']:
                parts.append(str(val).strip().capitalize())

        other_keys = sorted([k for k in self.metadata.keys()
                            if k.lower() not in priority_keys])
        for key in other_keys:
            val = self.metadata.get(key)
            if val and str(val).lower() not in ['none', 'null', '']:
                parts.append(
                    str(val).strip().capitalize())
        return ' - '.join(parts) if parts else 'Standard'

    def __str__(self):
        return f"Product: {self.name} | Type: {self.get_variant_label()} | Price: {self.price}"


class CartItems:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def get_subtotal(self):
        return self.product.price * self.quantity
