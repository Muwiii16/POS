# Blueprint for each classes
class Product:
    def __init__(self, name, variant, price, stock, barcode):
        self.name = name
        self.variant = variant
        self.price = price
        self.stock = stock
        self.barcode = barcode

    def __str__(self):
        return f"Product: {self.name} | Type: {self.variant} | Price: {self.price} | Stock: {self.stock} | Barcode: {self.barcode}"


class CartItems:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def get_subtotal(self):
        return self.product.price * self.quantity
