import customtkinter as ctk
from tkinter import messagebox

from core import engine

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class POSapp(ctk.CTk):
    def __init__(self,):
        super().__init__()
        self.title("Dad's Store POS")
        self.geometry("1200x800")

        self.cart = []
        self.store_products = engine.load_inventory()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_pages()
        self.setup_cart_view()
        self.show_page("POS")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="🏪 POS", font=(
            'Inter', 20, 'bold')).pack(pady=20)

        self.pos_btn = ctk.CTkButton(
            self.sidebar, text="POS", fg_color='transparent', text_color='black', command=lambda: self.show_page("POS"))
        self.pos_btn.pack(pady=10, padx=10)

        self.inventory_btn = ctk.CTkButton(self.sidebar, text='Inventory', fg_color='transparent',
                                           text_color='black', command=lambda: self.show_page("Inventory"))
        self.inventory_btn.pack(pady=10, padx=10)

        self.add_btn = ctk.CTkButton(self.sidebar, text="Add Product", fg_color="transparent",
                                     text_color='black', command=lambda: self.show_page('Add'))
        self.add_btn.pack(pady=10, padx=10)

    def show_page(self, page):
        self.pos_page.grid_forget()
        self.add_page.grid_forget()
        self.inventory_page.grid_forget()

        active_color = 'blue'
        inactive_color = 'grey'

        for btn in [self.pos_btn, self.add_btn, self.inventory_btn]:
            btn.configure(fg_color=inactive_color, text_color='black')

        match page:
            case 'POS':
                self.pos_page.grid(
                    row=0, column=1, sticky="nsew", padx=20, pady=5)
                self.pos_btn.configure(
                    fg_color=active_color, text_color='white')
                self.refresh_catalog()
            case 'Inventory':
                self.inventory_page.grid(
                    row=0, column=1, sticky="nsew", padx=20, pady=5)
                self.inventory_btn.configure(
                    fg_color=active_color, text_color='white')
                # self.refresh_inventory_table()
            case 'Add':
                self.add_page.grid(
                    row=0, column=1, sticky="nsew", padx=20, pady=5)
                self.add_btn.configure(
                    fg_color=active_color, text_color='white')

    def setup_main_pages(self):
        self.pos_page = ctk.CTkFrame(self, fg_color='transparent')
        self.search_entry = ctk.CTkEntry(
            self.pos_page, placeholder_text="Search Product...", height=40)
        self.search_entry.pack(pady=(0, 20), fill='x')
        self.search_entry.bind('<KeyRelease>', self.find_product)

        self.catalog_scroll = ctk.CTkScrollableFrame(
            self.pos_page, fg_color='transparent')
        self.catalog_scroll.pack(fill='both', expand=True)

        self.inventory_page = ctk.CTkFrame(self, fg_color='transparent')
        ctk.CTkLabel(self.inventory_page,
                     text='Inventory Management').pack(pady=20)

        self.add_page = ctk.CTkFrame(self, fg_color='transparent')
        ctk.CTkLabel(self.add_page, text="Add New Product").pack(pady=20)

    def find_product(self, event=None):
        query = self.search_entry.get().strip().lower()

        for child in self.catalog_scroll.winfo_children():
            child.destroy()

        if not query:
            self.refresh_catalog()
            return

        results = engine.search_products(query, self.store_products)

        unique_names = sorted(list(set(p.name for p in results)))

        row, col = 0, 0

        for name in unique_names:
            self.create_card(name, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

    def create_card(self, name, row, col):
        card = ctk.CTkFrame(self.catalog_scroll,
                            fg_color='white', corner_radius=15)
        card.grid(row=row, column=col, padx=10, pady=10)

        ctk.CTkLabel(card, text=name.capitalize(), font=(
            'Inter', 16, 'bold')).pack(pady=20, padx=20)
        ctk.CTkButton(card, text='Select Options',
                      command=lambda n=name: self.open_variant_modal(n)).pack(pady=10)

    def refresh_catalog(self):
        for child in self.catalog_scroll.winfo_children():
            child.destroy()

        unique_names = sorted(list(set(p.name for p in self.store_products)))

        row, col = 0, 0
        for name in unique_names:
            self.create_card(name, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

    def open_variant_modal(self, category_name):
        modal = ctk.CTkToplevel(self)
        modal_width = 400
        modal_height = 500

        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()

        center_x = int(main_x+(main_width/2)-(modal_width/2))
        center_y = int(main_y+(main_height/2)-(modal_height/2))

        modal.geometry(f'{modal_width}x{modal_height}+{center_x}+{center_y}')
        modal.attributes('-topmost', True)
        modal.grab_set()

        variants = [p for p in self.store_products if p.name == category_name]

        ctk.CTkLabel(modal, text=category_name.capitalize(),
                     font=('Inter', 22, 'bold')).pack(pady=(20, 5))
        ctk.CTkLabel(modal, text='Select Variant', font=(
            'Inter', 12), text_color='grey').pack(pady=(0, 20))

        price_label = ctk.CTkLabel(
            modal, text=f'₱{variants[0].price:.2f}', font=('Inter', 28, 'bold'))
        price_label.pack(pady=10)

        choice_var = ctk.StringVar(value=variants[0].variant)

        stock_label = ctk.CTkLabel(
            modal, text=f'Stock: {variants[0].stock}', font=('Inter', 13, 'italic'))

        def update_ui_on_select():
            selected = next(p for p in variants if p.variant ==
                            choice_var.get())
            price_label.configure(text=f'₱{selected.price:.2f}')
            stock_label.configure(text=f'Stock: {selected.stock}')

            if selected.stock <= 5:
                stock_label.configure(text_color='red')
            else:
                stock_label.configure(text_color='black')

        for v in variants:
            ctk.CTkRadioButton(modal, text=v.variant, variable=choice_var, value=v.variant,
                               command=update_ui_on_select).pack(pady=8, padx=50, anchor='w')

        stock_label.pack(side='bottom', pady=(0, 10))

        def add_and_close():
            prod = next(p for p in variants if p.variant == choice_var.get())
            self.add_to_cart(prod)
            modal.destroy()

        ctk.CTkButton(modal, text='🛒 Add to Cart', height=45, fg_color='#5c6370', hover_color='#4a4f59', font=('Inter', 14, 'bold'),
                      command=add_and_close).pack(side='bottom', pady=20, padx=40, fill='x')
        update_ui_on_select()

    def setup_cart_view(self):
        self.cart_frame = ctk.CTkFrame(
            self, width=300, fg_color='white', corner_radius=0)
        self.cart_frame.grid(row=0, column=2, sticky='nsew')

        ctk.CTkLabel(self.cart_frame, text="🛒 Cart",
                     font=('Inter', 18, 'bold')).pack(pady=20)
        self.cart_box = ctk.CTkTextbox(
            self.cart_frame, fg_color='transparent', font=('Inter', 12))
        self.cart_box.pack(fill='both', expand=True, padx=10)

        self.total_lbl = ctk.CTkLabel(
            self.cart_frame, text='Total: ₱0.00', font=('Inter', 20, 'bold'))
        self.total_lbl.pack(pady=10)

    def add_to_cart(self, product):
        if product.stock > 0:
            product.stock -= 1
            self.cart.append(product)
            self.cart_box.insert(
                'end', f'{product.name} ({product.variant}) - ₱{product.price:.2f}\n')
            total = sum(p.price for p in self.cart)
            self.total_lbl.configure(text=f'Total: ₱{total:.2f}')
        else:
            messagebox.showwarning('Stock', 'Out of Stock!')


'''
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
'''
