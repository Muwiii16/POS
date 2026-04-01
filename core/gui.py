import tkinter as tk
from tkinter import messagebox

from core import inventory
from core import models
from core import engine


class POSapp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dad's Store POS")
        self.cart = []

        # Search Entry
        self.search_label = tk.Label(root, text="Search Product: ")
        self.search_label.pack()
        self.search_entry = tk.Entry(root)
        self.search_entry.pack()

        self.search_btn = tk.Button(
            root, text='Search', command=self.find_product)
        self.search_btn.pack()

        # Variants
        self.variant_frame = tk.Frame(root)
        self.variant_frame.pack(pady=10)

        # Cart Display
        self.cart_listbox = tk.Listbox(root, width=50)
        self.cart_listbox.pack()

        # Checkout Display
        self.total_label = tk.Label(
            root, text="Total: P0.00", font=("Arial", 14, "bold"))
        self.total_label.pack(pady=10)

        tk.Label(root, text="Amount Paid: ").pack()
        self.payment_entry = tk.Entry(root)
        self.payment_entry.pack()

        self.checkout_btn = tk.Button(
            root, text='CHECKOUT', bg='green', fg='white', command=self.checkout)
        self.checkout_btn.pack(pady=10)

    def clear_search_results(self):
        for widget in self.variant_frame.winfo_children():
            widget.destroy()

    def create_product_button(self, product):
        button_text = f'{product.name} ({product.variant}) - ₱{product.price:.2f} | Stock: {product.stock}'
        btn = tk.Button(self.variant_frame, text=button_text,
                        command=lambda i=product: self.add_to_cart(i))
        btn.pack(fill='x', pady=2)

    def find_product(self):
        query = self.search_entry.get()
        results = engine.search_products(query, inventory.Store_Products)
        self.clear_search_results()

        for product in results:
            self.create_product_button(product)

    def add_to_cart(self, product):
        if product.stock > 0:
            product.stock -= 1
            self.cart.append(product)
            self.cart_listbox.insert(tk.END, str(product))

            current_total = sum(item.price for item in self.cart)
            self.total_label.config(text=f'Total: P{current_total:.2f}')
            self.find_product()

        else:
            messagebox.showwarning('Out of Stock', 'Item is out of stock!')

    def checkout(self):
        raw_payment = self.payment_entry.get()
        success, total, result = engine.process_checkout(
            self.cart, raw_payment)

        if not success:
            messagebox.showwarning("Checkout Error", result)
        else:
            receipt_msg = engine.generate_receipt_text(
                self.cart, total, float(raw_payment), result)
            messagebox.showinfo("Successful Checkout", receipt_msg)

            self.reset_ui()

    def reset_ui(self):
        # Reset for next customer
        self.cart = []
        self.cart_listbox.delete(0, 'end')
        self.total_label.config(text="Total: P0.00")
        self.payment_entry.delete(0, 'end')
        self.search_entry.delete(0, 'end')
