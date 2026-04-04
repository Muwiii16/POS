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
        if not self.metadata:
            return 'Standard'
        return ' - '.join(str(v) for v in self.metadata.values())

    def __str__(self):
        return f"Product: {self.name} | Type: {self.get_variant_label()} | Price: {self.price}"


class CartItems:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def get_subtotal(self):
        return self.product.price * self.quantity
