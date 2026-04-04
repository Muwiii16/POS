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

        if page == 'POS':
            self.cart_frame.grid(row=0, column=2, sticky='nsew')
            self.grid_columnconfigure(2, weight=0, minsize=350)
        else:
            self.cart_frame.grid_forget()
            self.grid_columnconfigure(2, weight=0, minsize=0)

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
                self.refresh_inventory_table()
            case 'Add':
                self.add_page.grid(
                    row=0, column=1, sticky="nsew", padx=20, pady=5)
                self.add_btn.configure(
                    fg_color=active_color, text_color='white')

    def setup_main_pages(self):
        # POS page
        self.pos_page = ctk.CTkFrame(self, fg_color='transparent')
        self.search_entry = ctk.CTkEntry(
            self.pos_page, placeholder_text="Search Product...", height=40)
        self.search_entry.pack(pady=(0, 20), fill='x')
        self.search_entry.bind('<KeyRelease>', self.find_product)

        self.catalog_scroll = ctk.CTkScrollableFrame(
            self.pos_page, fg_color='transparent')
        self.catalog_scroll.pack(fill='both', expand=True)
        # POS page
        # Inventory Management page
        self.inventory_page = ctk.CTkFrame(self, fg_color='transparent')
        ctk.CTkLabel(self.inventory_page,
                     text='Inventory Management', font=('Inter', 24, 'bold')).pack(pady=20)

        self.inv_search_entry = ctk.CTkEntry(
            self.inventory_page, placeholder_text='Search inventory by name...', height=40)
        self.inv_search_entry.pack(pady=(0, 10), padx=20, fill='x')
        self.inv_search_entry.bind('<KeyRelease>', self.find_inventory_item)

        ctrl_frame = ctk.CTkFrame(self.inventory_page, fg_color='transparent')
        ctrl_frame.pack(pady=5, padx=20, fill='x')

        self.undo_btn = ctk.CTkButton(
            ctrl_frame, text='↩️ Undo', width=100, command=self.handle_undo)
        self.undo_btn.pack(side='left', padx=5)
        self.redo_btn = ctk.CTkButton(
            ctrl_frame, text='↪️ Redo', width=100, command=self.handle_redo)
        self.redo_btn.pack(side='left', padx=5)

        self.inventory_scroll = ctk.CTkScrollableFrame(
            self.inventory_page, fg_color='white')
        self.inventory_scroll.pack(fill='both', expand=True, padx=20, pady=10)
        # Inventory Management page
        # Add Products page
        self.add_page = ctk.CTkScrollableFrame(self, fg_color='transparent')
        ctk.CTkLabel(self.add_page, text="Add New Product",
                     font=('Inter', 24, 'bold')).pack(pady=20)

        form_frame = ctk.CTkFrame(
            self.add_page, fg_color='white', corner_radius=15)
        form_frame.pack(pady=10, padx=50, fill='x')

        self.new_name = self.create_input_row(form_frame, 'Product Name')
        self.new_price = self.create_input_row(form_frame, 'Price (₱)')
        self.new_stock = self.create_input_row(form_frame, 'Initial Stock')
        self.new_category = self.create_input_row(form_frame, 'Category')
        self.new_barcode = self.create_input_row(form_frame, 'Barcode')

        ctk.CTkLabel(form_frame, text='Extra Details (Variants)',
                     font=('Inter', 14, 'bold')).pack(pady=(20, 10))

        self.metadata_container = ctk.CTkFrame(
            form_frame, fg_color='transparent')
        self.metadata_container.pack(fill='x', padx=20)
        self.metadata_rows = []

        ctk.CTkButton(form_frame, text='+ Add Detail (e.g. Color: Blue)',
                      fg_color='#34495e', command=self.add_metadata_row).pack(pady=10)
        ctk.CTkButton(self.add_page, text='📥 Save Product to Inventory', height=50, fg_color='#2ecc71', font=(
            'Inter', 16, 'bold'), command=self.submit_new_product).pack(pady=30, padx=50, fill='x')

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
        modal_width = 700
        modal_height = 600

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

        scroll_container = ctk.CTkScrollableFrame(
            modal, fg_color="transparent", width=modal_width-20)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 80))

        all_keys = []
        for p in variants:
            for k in p.metadata.keys():
                if k not in all_keys:
                    all_keys.append(k)

        variant_types = all_keys

        ctk.CTkLabel(scroll_container, text=category_name.capitalize(),
                     font=('Inter', 22, 'bold')).pack(pady=(20, 5))

        ctk.CTkLabel(scroll_container, text='Select Options', font=(
            'Inter', 12), text_color='grey').pack(pady=(0, 20))

        price_label = ctk.CTkLabel(
            scroll_container, text=f'₱{variants[0].price:.2f}', font=('Inter', 28, 'bold'))
        price_label.pack(pady=10)

        selection_vars = {}

        def get_selected_product():
            for p in variants:
                match = True
                for v_type, v_var in selection_vars.items():
                    if str(p.metadata.get(v_type)) != v_var.get():
                        match = False
                        break
                if match:
                    return p
            return None

        def update_ui_on_select():
            selected = get_selected_product()
            if selected:
                price_label.configure(text=f'₱{selected.price:.2f}')
                stock_label.configure(text=f'Stock: {selected.stock}')
                stock_label.configure(
                    text_color='red' if selected.stock <= 5 else 'black')
                add_btn.configure(state='normal')
            else:
                price_label.configure(text='---')
                stock_label.configure(
                    text='Out of Stock / Unavailable', text_color='grey')
                add_btn.configure(state='disabled')

        for v_type in variant_types:
            row_frame = ctk.CTkFrame(scroll_container, fg_color='transparent')
            row_frame.pack(fill='x', padx=40, pady=10)

            ctk.CTkLabel(row_frame, text=v_type.capitalize(),
                         font=('Inter', 14, 'bold')).pack(side='left')

            unique_values = sorted(
                list(set(str(p.metadata.get(v_type)) for p in variants if p.metadata.get(v_type) and str(p.metadata.get(v_type)).lower() != 'none')))

            if not unique_values:
                ConnectionRefusedError

            v_var = ctk.StringVar(value=unique_values[0])
            selection_vars[v_type] = v_var

            options_frame = ctk.CTkFrame(row_frame, fg_color='transparent')
            options_frame.pack(side='right')

            for val in unique_values:
                ctk.CTkRadioButton(options_frame, text=val, variable=v_var, value=val,
                                   command=update_ui_on_select).pack(side='left', padx=5)

        qty_section = ctk.CTkFrame(
            scroll_container, fg_color='#f2f2f2', corner_radius=10)
        qty_section.pack(pady=20, padx=40, fill='x')

        qty_var = ctk.IntVar(value=1)

        def change_qty(amt):
            new_val = qty_var.get()+amt
            if 1 <= new_val <= 99:
                qty_var.set(new_val)

        qty_control = ctk.CTkFrame(qty_section, fg_color='transparent')
        qty_control.pack(pady=10)

        ctk.CTkButton(qty_control, text='-', width=35,
                      command=lambda: change_qty(-1)).pack(side='left', padx=5)
        ctk.CTkEntry(qty_control, textvariable=qty_var, width=50,
                     justify='center').pack(side='left', padx=5)
        ctk.CTkButton(qty_control, text='+', width=35,
                      command=lambda: change_qty(1)).pack(side='left', padx=5)

        stock_label = ctk.CTkLabel(
            scroll_container, text='', font=('Inter', 13, 'italic'))
        stock_label.pack()

        def add_and_close():
            prod = get_selected_product()

            if prod:
                self.add_to_cart(prod, qty_var.get(), parent_win=modal)
                modal.destroy()

        add_btn = ctk.CTkButton(modal, text='🛒 Add to Cart', height=50, fg_color='#5c6370',
                                hover_color='#4a4f59', font=('Inter', 16, 'bold'), command=add_and_close)
        add_btn.pack(side='bottom', pady=30, padx=40, fill='x')

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
        self.payment_entry.bind(
            '<Return>', lambda event: self.process_checkout())

        self.change_lbl = ctk.CTkLabel(
            payment_frame, text='Change: ₱0.00', font=('Inter', 16), text_color='green')
        self.change_lbl.pack(pady=5)

        self.checkout_btn = ctk.CTkButton(self.cart_frame, text='COMPLETE CHECKOUT', height=40, fg_color='#2ecc71', font=(
            'Inter', 14, 'bold'), command=self.process_checkout)
        self.checkout_btn.pack(pady=20, padx=20, fill='x')

    def process_checkout(self, event=None):
        payment_amount = self.payment_entry.get()
        success, total, result = engine.process_checkout(
            self.cart, payment_amount, self.store_products)
        if success:
            paid = float(payment_amount)
            change = result
            receipt = engine.generate_receipt_text(
                self.cart, total, paid, change)
            messagebox.showinfo(
                'Success', f'Transaction Complete!\n\n{receipt}')
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
        total = engine.calculate_totals(self.cart)
        payment_text = self.payment_entry.get()

        display_text, color = engine.get_change_info(payment_text, total)
        self.change_lbl.configure(text=display_text, text_color=color)

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

        grouped_items = engine.get_grouped_cart(self.cart)

        for (name, variant_label), (prod, qty) in grouped_items.items():
            row = ctk.CTkFrame(self.cart_items_frame,
                               fg_color='#f0f0f0', corner_radius=8)
            row.pack(fill='x', pady=2, padx=5)

            lbl = ctk.CTkLabel(row, text=f'{name}\n({variant_label})', font=(
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
        if engine.remove_item_from_cart(product, self.cart):
            self.update_cart_display()
            self.calculate_change

    def refresh_inventory_table(self, products_to_show=None):
        display_list = products_to_show if products_to_show is not None else self.store_products

        for child in self.inventory_scroll.winfo_children():
            child.destroy()

        header_frame = ctk.CTkFrame(self.inventory_scroll, fg_color='#e0e0e0')
        header_frame.pack(fill='x', pady=5)
        headers = ['Name', 'Variant', 'Price', 'Stock', 'Actions']
        widths = [200, 200, 100, 100, 200]

        for text, width in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=text, width=width, font=(
                'Inter', 12, 'bold')).pack(side='left', padx=10)

        for product in display_list:
            row = ctk.CTkFrame(self.inventory_scroll, fg_color='transparent')
            row.pack(fill='x', pady=2)

            ctk.CTkLabel(row, text=product.name, width=200,
                         anchor='w').pack(side='left', padx=10)
            ctk.CTkLabel(row, text=product.get_variant_label(),
                         width=200, anchor='w').pack(side='left', padx=10)
            ctk.CTkLabel(row, text=f'₱{product.price:.2f}', width=100).pack(
                side='left', padx=10)
            ctk.CTkLabel(row, text=str(product.stock),
                         width=100).pack(side='left', padx=10)

            btn_frame = ctk.CTkFrame(row, fg_color='transparent')
            btn_frame.pack(side='left', padx=10)

            ctk.CTkButton(btn_frame, text='Edit', width=60, fg_color='#3498db',
                          command=lambda p=product: self.open_edit_modal(p)).pack(side='left', padx=5)
            ctk.CTkButton(btn_frame, text='Delete', width=60, fg_color='#e74c3c',
                          command=lambda p=product: self.confirm_delete(p)).pack(side='left', padx=5)

    def confirm_delete(self, product):
        if messagebox.askyesno('Delete', f'Are you sure you want to delete {product.name} ({product.get_variant_label()})?'):
            engine.history.save_state(self.store_products)
            if engine.delete_product(product, self.store_products):
                self.refresh_inventory_table()

    def open_edit_modal(self, product):
        modal = ctk.CTkToplevel(self)
        modal.geometry('400x500')
        modal.title(f'Editing {product.name}')
        modal.attributes('-topmost', True)

        ctk.CTkLabel(modal, text='Edit Product', font=(
            'Inter', 20, 'bold')).pack(pady=20)

        name_entry = self.create_edit_field(modal, 'Name', product.name)
        price_entry = self.create_edit_field(
            modal, 'Price', str(product.price))
        stock_entry = self.create_edit_field(
            modal, 'Stock', str(product.stock))

        def save_changes():

            try:
                engine.history.save_state(self.store_products)
                product.name = name_entry.get()
                product.price = float(price_entry.get())
                product.stock = int(stock_entry.get())

                engine.save_inventory(self.store_products)
                self.refresh_inventory_table()
                modal.destroy()
                messagebox.showinfo('Succes', 'Produve updated!')
            except ValueError:
                messagebox.showerror('Error', 'Invalid price or stock value.')

        ctk.CTkButton(modal, text='Save Changes', fg_color='#2ecc71',
                      command=save_changes).pack(pady=30, padx=40, fill='x')

    def create_edit_field(self, parent, label_text, initial_val):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(fill='x', padx=40, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=80,
                     anchor='w').pack(side='left')
        entry = ctk.CTkEntry(frame)
        entry.insert(0, initial_val)
        entry.pack(side='right', fill='x', expand=True)
        return entry

    def find_inventory_item(self, event=None):
        query = self.inv_search_entry.get().strip().lower()
        if not query:
            self.refresh_inventory_table()
            return

        results = engine.search_products(query, self.store_products)
        self.refresh_inventory_table(results)

    def handle_undo(self):
        prev_state = engine.history.undo(self.store_products)
        if prev_state is not None:
            self.store_products = prev_state
            engine.save_inventory(self.store_products)
            self.refresh_inventory_table()
        else:
            messagebox.showinfo('Unfo', 'No more actios to undo.')

    def handle_redo(self):
        next_state = engine.history.redo(self.store_products)
        if next_state is not None:
            self.store_products = next_state
            engine.save_inventory(self.store_products)
            self.refresh_inventory_table()
        else:
            messagebox.showinfo('Redo', 'No more action to redo.')

    def create_input_row(self, parent, label_text):
        row = ctk.CTkFrame(parent, fg_color='transparent')
        row.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(row, text=label_text, width=120,
                     anchor='w').pack(side='left')
        entry = ctk.CTkEntry(
            row, placeholder_text=f'Enter {label_text.lower()}...')
        entry.pack(side='right', fill='x', expand=True)
        return entry

    def add_metadata_row(self):
        row = ctk.CTkFrame(self.metadata_container, fg_color='transparent')
        row.pack(fill='x', pady=5)

        key_entry = ctk.CTkEntry(
            row, placeholder_text='Field (e.g. Size)', width=120)
        key_entry.pack(side='left', padx=5)

        val_entry = ctk.CTkEntry(
            row, placeholder_text='Value (e.g. Large)')
        val_entry.pack(side='left', padx=5, fill='x', expand=True)

        remove_btn = ctk.CTkButton(row, text='X', width=30, fg_color='#e74c3c',
                                   command=lambda r=row: self.remove_metadata_row(r))
        remove_btn.pack(side='right', padx=5)

        self.metadata_rows.append((row, key_entry, val_entry))

    def remove_metadata_row(self, row_frame):
        self.metadata_rows = [
            r for r in self.metadata_rows if r[0] != row_frame]
        row_frame.destroy()

    def submit_new_product(self):
        try:
            name = self.new_name.get().strip()
            if not name:
                messagebox.showerror('Error', 'Product Name cannot be empty!')
                return
            data = {
                'name': self.new_name.get(),
                'price': float(self.new_price.get()),
                'stock': int(self.new_stock.get()),
                'category': self.new_category.get(),
                'barcode': self.new_barcode.get()
            }

            for _, key_ent, val_ent in self.metadata_rows:
                key = key_ent.get().strip().lower()
                val = val_ent.get().strip()
                if key and val:
                    data[key] = val

            success, msg = engine.add_new_product(data, self.store_products)

            if success:
                messagebox.showinfo('Success', msg)

                for entry in [self.new_name, self.new_price, self.new_stock, self.new_category, self.new_barcode]:
                    entry.delete(0, 'end')
                for row_frame, _, _ in self.metadata_rows:
                    row_frame.destroy()
                self.metadata_rows = []
            else:
                messagebox.showerror('Error', msg)

        except ValueError:
            messagebox.showerror('Error', 'Price and Stock must be numbers!')
            return


# Under Construction
# still no inventory
# still no Add product
