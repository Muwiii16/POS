import tkinter as tk
from tkinter import messagebox


from core import engine


class POSapp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dad's Store POS")
        self.cart = []
        self.store_products = engine.load_inventory()

        self.setup_ui()
        self.bind_shortcuts()
        self.show_catalog()

    def setup_ui(self):
        self.create_search_area()
        self.create_variant_area()
        self.create_cart_area()
        self.create_checkout_area()

    def create_search_area(self):
        # Search Entry
        search_container = tk.Frame(self.root)
        search_container.pack(pady=5)

        self.search_label = tk.Label(search_container, text="Search Product: ")
        self.search_label.grid(row=0, column=0, padx=5)

        self.search_entry = tk.Entry(search_container)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.focus_set()

        self.search_btn = tk.Button(
            search_container, text='Search', command=self.find_product)
        self.search_btn.grid(row=0, column=2, padx=5)

    def create_variant_area(self):
        # Variants
        self.variant_frame = tk.Frame(self.root)
        self.variant_frame.pack(pady=10)

    def create_cart_area(self):
        # Cart Display
        self.cart_listbox = tk.Listbox(self.root, width=50)
        self.cart_listbox.pack()

    def create_checkout_area(self):
        # Checkout Display
        payment_container = tk.Frame(self.root)
        payment_container.pack(pady=10)

        self.total_label = tk.Label(
            payment_container, text="Total: P0.00", font=("Arial", 14, "bold"))
        self.total_label.grid(row=0, column=0, padx=5)

        tk.Label(payment_container, text="Amount Paid: ").grid(
            row=1, column=0, padx=5)
        self.payment_entry = tk.Entry(payment_container)
        self.payment_entry.grid(row=1, column=1, padx=5)

        self.checkout_btn = tk.Button(
            payment_container, text='CHECKOUT', bg='green', fg='white', command=self.checkout)
        self.checkout_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def bind_shortcuts(self):
        self.search_entry.bind('<Return>', lambda event: self.find_product())
        self.payment_entry.bind('<Return>', lambda event: self.checkout())

    def clear_search_results(self):
        for widget in self.variant_frame.winfo_children():
            widget.destroy()

    def create_product_button(self, product):
        button_text = f'{product.name} ({product.variant}) - ₱{product.price:.2f} | Stock: {product.stock}'
        btn = tk.Button(self.variant_frame, text=button_text,
                        command=lambda i=product: self.add_to_cart(i))
        btn.pack(fill='x', pady=2)

    def show_catalog(self):
        self.clear_search_results()
        unique_names = []
        for product in self.store_products:
            if product.name not in unique_names:
                unique_names.append(product.name)

                btn = tk.Button(self.variant_frame, text=product.name.capitalize(
                ), width=25, height=2, bg='lightblue', command=lambda name=product.name: self.show_variants(name))
                btn.pack(pady=5)

    def show_variants(self, product_name):
        self.clear_search_results()
        variants = [p for p in self.store_products if p.name == product_name]

        for variant in variants:
            btn_text = f'{variant.variant} - ₱{variant.price:.2f} | Stock: {variant.stock}'
            btn = tk.Button(self.variant_frame, text=btn_text, width=40,
                            command=lambda prod=variant: self.add_to_cart(prod))
            btn.pack(pady=2)

        tk.Button(self.variant_frame, text="Back to Catalog",
                  command=self.show_catalog).pack(pady=10)

    def find_product(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.show_catalog()
            return

        self.clear_search_results()
        results = engine.search_products(query, self.store_products)

        for product in results:
            self.create_product_button(product)

    def add_to_cart(self, product):
        if product.stock > 0:
            product.stock -= 1
            self.cart.append(product)
            self.cart_listbox.insert(tk.END, str(product))

            current_total = sum(item.price for item in self.cart)
            self.total_label.config(text=f'Total: P{current_total:.2f}')
            query = self.search_entry.get().strip().lower()
            if query:
                self.find_product()
            else:
                self.show_variants(product.name)

        else:
            messagebox.showwarning('Out of Stock', 'Item is out of stock!')

    def checkout(self):
        raw_payment = self.payment_entry.get()
        success, total, result = engine.process_checkout(
            self.cart, raw_payment)

        if not success:
            messagebox.showwarning("Checkout Error", result)
        else:
            engine.save_inventory(self.store_products)
            engine.log_sale(self.cart, total, float(raw_payment), result)
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
        self.show_catalog()
