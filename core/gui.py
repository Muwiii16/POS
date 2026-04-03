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

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=350)
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

        qty_frame = ctk.CTkFrame(modal, fg_color='transparent')
        qty_frame.pack(pady=20)

        ctk.CTkLabel(qty_frame, text='Quantity: ').grid(
            row=0, column=0, padx=10)

        qty_var = ctk.IntVar(value=1)

        def change_qty(amt):
            new_val = qty_var.get()+amt
            if 1 <= new_val <= 99:
                qty_var.set(new_val)
        ctk.CTkButton(qty_frame, text='-', width=30,
                      command=lambda: change_qty(-1)).grid(row=0, column=1)
        ctk.CTkEntry(qty_frame, textvariable=qty_var, width=50,
                     justify='center').grid(row=0, column=2, padx=5)
        ctk.CTkButton(qty_frame, text='+', width=30,
                      command=lambda: change_qty(+1)).grid(row=0, column=3)

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
                               command=update_ui_on_select).pack(pady=5)

        stock_label.pack(side='bottom', pady=(0, 10))

        def add_and_close():
            prod = next(p for p in variants if p.variant == choice_var.get())
            quantity = qty_var.get()

            self.add_to_cart(prod, quantity, parent_win=modal)
            if prod.stock >= quantity:
                modal.destroy()

        ctk.CTkButton(modal, text='🛒 Add to Cart', height=45, fg_color='#5c6370', hover_color='#4a4f59', font=('Inter', 14, 'bold'),
                      command=add_and_close).pack(side='bottom', pady=20, padx=40, fill='x')
        update_ui_on_select()

    def setup_cart_view(self):
        self.cart_frame = ctk.CTkFrame(
            self, width=450, fg_color='white', corner_radius=0)
        self.cart_frame.grid(row=0, column=2, sticky='nsew')
        self.cart_frame.grid_propagate(False)

        ctk.CTkLabel(self.cart_frame, text="🛒 Cart",
                     font=('Inter', 18, 'bold')).pack(pady=20)
        self.cart_items_frame = ctk.CTkScrollableFrame(
            self.cart_frame, fg_color='transparent', height=400)
        self.cart_items_frame.pack(fill='both', expand=True, padx=2)

        payment_frame = ctk.CTkFrame(self.cart_frame, fg_color='transparent')
        payment_frame.pack(pady=5)

        self.total_lbl = ctk.CTkLabel(
            self.cart_frame, text='Total: ₱0.00', font=('Inter', 20, 'bold'))
        self.total_lbl.pack(pady=10)

        ctk.CTkLabel(payment_frame, text='Payment Amount: ',
                     font=('Inter', 12)).pack()
        self.payment_entry = ctk.CTkEntry(
            payment_frame, placeholder_text='0.00', justify='center')
        self.payment_entry.pack(pady=5, fill='x')
        self.payment_entry.bind('<KeyRelease>', self.calculate_change)

        self.change_lbl = ctk.CTkLabel(
            payment_frame, text='Change: ₱0.00', font=('Inter', 16), text_color='green')
        self.change_lbl.pack(pady=5)

        self.checkout_btn = ctk.CTkButton(self.cart_frame, text='COMPLETE CHECKOUT', height=40, fg_color='#2ecc71', font=(
            'Inter', 14, 'bold'), command=self.process_checkout)
        self.checkout_btn.pack(pady=20, padx=20, fill='x')

    def process_checkout(self):
        payment_amount = self.payment_entry.get()
        success, total, result = engine.process_checkout(
            self.cart, payment_amount)
        if success:
            messagebox.showinfo(
                'Success', f'Transaction Complete!\nChange: ₱{result:.2f}')
            self.reset()

        else:
            messagebox.showerror('Checkout Error', result)

    def reset(self):
        self.cart = []
        for child in self.cart_items_frame.winfo_children():
            child.destroy()

        self.payment_entry.delete(0, 'end')
        self.total_lbl.configure(text='Total: ₱0.00')
        self.change_lbl.configure(text='Change: ₱0.00', text_color='green')

    def calculate_change(self, event=None):
        try:
            total = engine.calculate_totals(self.cart)
            payment_text = self.payment_entry.get()
            payment = float(payment_text) if payment_text else 0

            change = payment-total

            if change >= 0:
                self.change_lbl.configure(
                    text=f'Change: ₱{change:.2f}', text_color='green')
            else:
                self.change_lbl.configure(
                    text='Insufficient Amount', text_color='red')
        except ValueError:
            self.change_lbl.configure(text='Invalid Amount', text_color='red')

    def add_to_cart(self, product, quantity=1, parent_win=None):
        target_parent = parent_win if parent_win else self
        success, result = engine.add_bulk_cart(product, quantity, self.cart)

        if success:
            self.update_cart_display()
            self.total_lbl.configure(text=f'Total: ₱{result:.2f}')
            self.calculate_change()

        else:
            messagebox.showwarning(
                "Stock Error!", result, parent=target_parent)

    def update_cart_display(self):
        for child in self.cart_items_frame.winfo_children():
            child.destroy()

        grouped_items = {}
        for item in self.cart:
            key = (item.name, item.variant)
            if key not in grouped_items:
                grouped_items[key] = [item, 0]
            grouped_items[key][1] += 1

        for (name, variant), (prod, qty) in grouped_items.items():
            row = ctk.CTkFrame(self.cart_items_frame,
                               fg_color='#f0f0f0', corner_radius=8)
            row.pack(fill='x', pady=2, padx=5)

            lbl = ctk.CTkLabel(row, text=f'{name}\n({variant})', font=(
                'Inter', 16), anchor='w', justify='left')
            lbl.pack(side='left', padx=10, pady=5, fill='x', expand=True)

            btn_frame = ctk.CTkFrame(row, fg_color='transparent')
            btn_frame.pack(side='right', padx=5)

            ctk.CTkButton(btn_frame, text='-', width=25, height=25,
                          command=lambda p=prod: self.remove_one_from_cart(p)).pack(side='left', padx=2)
            ctk.CTkLabel(btn_frame, text=str(qty), font=(
                'Inter', 15, 'bold')).pack(side='left', padx=5)
            ctk.CTkButton(btn_frame, text='+', width=25, height=25,
                          command=lambda p=prod: self.add_to_cart(p, 1)).pack(side='left', padx=2)

            subtotal = prod.price*qty
            ctk.CTkLabel(btn_frame, text=f'₱{subtotal:.2f}', font=(
                'Inter', 16, 'bold'), text_color='#2980b9', width=70, anchor='e').pack(side='left', padx=(10, 5))

            current_total = engine.calculate_totals(self.cart)
            self.total_lbl.configure(text=f'Total: ₱{current_total:.2f}')

    def remove_one_from_cart(self, product):
        for i, item in enumerate(self.cart):
            if item.name == product.name and item.variant == product.variant:
                self.cart.pop(i)
                product.stock += 1
                break

        self.update_cart_display()
        total = engine.calculate_totals(self.cart)
        self.total_lbl.configure(text=f'Total: ₱{total:.2f}')
        self.calculate_change()


# Under Construction
# have to fix the checkout button
# palakihin cart side
# palakihin product font sa cart
# paliitin button ng bawat product
