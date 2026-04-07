import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core import engine

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class POSapp(ctk.CTk):
    def __init__(self,):
        super().__init__()
        self.title("Dad's Store POS")
        self.center_window(1200, 800)

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

        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.inv_search_entry.bind('<KeyRelease>', self.on_search_change)

    def on_search_change(self, event):
        query = self.inv_search_entry.get().strip().lower()
        if not query:
            self.refresh_inventory_table()
        else:
            results = [
                p for p in self.store_products if query in p.name.lower()]
            self.refresh_inventory_table(results)

    def center_window(self, width=1200, height=800):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2)-(width // 2)
        y = (screen_height // 2)-(height // 2)

        self.geometry(f'{width}x{height}+{x}+{y}')

    def center_popup(self, popup, width, height):
        popup.update_idletasks()

        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_w = self.winfo_width()
        main_h = self.winfo_height()

        x = int(main_x+(main_w // 2) - (width / 2))
        y = int(main_y+(main_h // 2) - (height / 2))

        popup.geometry(f'{width}x{height}+{x}+{y}')

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

        self.eod_button = ctk.CTkButton(self.sidebar, text='End of Day',
                                        fg_color='#e67e22', hover_color='#d35400', command=self.handle_eod_report)
        self.eod_button.pack(pady=10, padx=20, side='bottom')

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

        self.inventory_alert_frame = ctk.CTkFrame(
            self.inventory_page, fg_color='transparent', height=0)
        self.inventory_alert_frame.pack(fill='x', padx=20, pady=(10, 0))

        self.inv_search_entry = ctk.CTkEntry(
            self.inventory_page, placeholder_text='Search inventory by name...', height=40)
        self.inv_search_entry.pack(pady=(0, 10), padx=20, fill='x')
        self.inv_search_entry.bind(
            '<KeyRelease>', self.find_inventory_item)

        ctrl_frame = ctk.CTkFrame(
            self.inventory_page, fg_color='transparent')
        ctrl_frame.pack(pady=5, padx=20, fill='x')

        self.undo_btn = ctk.CTkButton(
            ctrl_frame, text='↩️ Undo', width=100, command=self.handle_undo)
        self.undo_btn.pack(side='left', padx=5)
        self.redo_btn = ctk.CTkButton(
            ctrl_frame, text='↪️ Redo', width=100, command=self.handle_redo)
        self.redo_btn.pack(side='left', padx=5)

        self.inventory_scroll = ctk.CTkScrollableFrame(
            self.inventory_page, fg_color='white')
        self.inventory_scroll.pack(
            fill='both', expand=True, padx=20, pady=10)
        # Inventory Management page
        # Add Products page
        self.add_page = ctk.CTkScrollableFrame(
            self, fg_color='transparent')
        ctk.CTkLabel(self.add_page, text="Add New Product",
                     font=('Inter', 24, 'bold')).pack(pady=20)

        form_frame = ctk.CTkFrame(
            self.add_page, fg_color='white', corner_radius=15)
        form_frame.pack(pady=10, padx=50, fill='x')

        self.new_name = self.create_input_row(form_frame, 'Product Name')
        self.new_price = self.create_input_row(form_frame, 'Price (₱)')
        self.new_stock = self.create_input_row(form_frame, 'Initial Stock')
        self.new_category = self.create_input_row(form_frame, 'Category')

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

    def refresh_inventory_table(self, products_to_show=None):
        if not hasattr(self, 'inventory_scroll') or not self.inventory_scroll.winfo_exists():
            return

        low_stock_list = [p for p in self.store_products if p.stock <= 5]
        out_of_stock_count = len(
            [p for p in low_stock_list if p.stock == 0])

        for child in self.inventory_alert_frame.winfo_children():
            child.destroy()

        if low_stock_list:
            msg = f'⚠️ ALERT: {len(low_stock_list)} items are low on stock'
            if out_of_stock_count > 0:
                msg += f' ({out_of_stock_count} completely empty!)'

            banner_color = '#e74c3c' if out_of_stock_count > 0 else '#e67e22'

            alert_banner = ctk.CTkButton(self.inventory_alert_frame, text=msg, fg_color=banner_color,
                                         hover_color='#d35400', font=('Inter', 13, 'bold'), command=self.show_only_low_stock)
            alert_banner.pack(fill='x', pady=5)

        if products_to_show is not None:
            back_btn = ctk.CTkButton(
                self.inventory_alert_frame,
                text='⬅ Back to Full Inventory',
                fg_color='#7f8c8d',
                command=self.clear_inventory_filter
            ).pack(pady=5)

        for child in self.inventory_scroll.winfo_children():
            child.destroy()

        display_list = products_to_show if products_to_show is not None else self.store_products

        grouped = {}
        for p in display_list:
            if p.name not in grouped:
                grouped[p.name] = []
            grouped[p.name].append(p)

        self.inventory_scroll.update_idletasks()
        current_width = self.inventory_scroll.winfo_width()-40
        w_name = int(current_width*0.20)
        w_vars = int(current_width * 0.40)
        w_price = int(current_width * 0.15)
        w_stock = int(current_width * 0.10)
        w_button = 100

        header_frame = ctk.CTkFrame(
            self.inventory_scroll, fg_color='#e0e0e0', height=40)
        header_frame.pack(fill='x', padx=10, pady=(0, 5))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(header_frame, text="Name", width=w_name, anchor='w', font=(
            'Inter', 12, 'bold')).pack(side='left', padx=10)
        ctk.CTkLabel(header_frame, text="Variants", width=w_vars, anchor='w', font=(
            'Inter', 12, 'bold')).pack(side='left', padx=10)
        ctk.CTkLabel(header_frame, text="Price", width=w_price, anchor='center', font=(
            'Inter', 12, 'bold')).pack(side='left', padx=10)
        ctk.CTkLabel(header_frame, text="Stock", width=w_stock, anchor='center', font=(
            'Inter', 12, 'bold')).pack(side='left', padx=10)

        for name, items in grouped.items():
            row = ctk.CTkFrame(self.inventory_scroll,
                               fg_color='transparent', height=45)
            row.pack(fill='x', pady=2, padx=10)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=name, width=w_name, anchor='w', font=(
                'Inter', 13, 'bold')).pack(side='left', padx=10)

            v_str = ', '.join([p.get_variant_label() for p in items])
            if len(v_str) > 40:
                v_str = v_str[:37] + "..."
            ctk.CTkLabel(row, text=v_str, width=w_vars, anchor='w', font=(
                'Inter', 11), text_color='grey').pack(side='left', padx=10)

            prices = [p.price for p in items]
            p_text = f'₱{min(prices):.2f}' if len(
                set(prices)) == 1 else f'₱{min(prices):.2f}-₱{max(prices):.2f}'
            ctk.CTkLabel(row, text=p_text, width=w_price,
                         anchor='center').pack(side='left', padx=10)

            total_stock = sum(p.stock for p in items)
            if total_stock == 0:
                stock_color = '#e74c3c'
                display_stock = 'OUT'
            elif total_stock <= 5:
                stock_color = '#e67e22'
                display_stock = str(total_stock)
            else:
                stock_color = '#2c3e50'
                display_stock = str(total_stock)

            ctk.CTkLabel(row, text=display_stock, width=w_stock, anchor='center', font=(
                'Inter', 12, 'bold'), text_color=stock_color).pack(side='left', padx=10)

            ctk.CTkButton(row, text='Manage', width=w_button, height=28, fg_color='#34495e',
                          command=lambda n=name: self.filter_inventory_by_name(n)).pack(side='right', padx=10)

    def show_only_low_stock(self):
        low_stock = [p for p in self.store_products if p.stock <= 5]
        self.refresh_inventory_table(low_stock)

    def filter_inventory_by_name(self, name):
        results = [p for p in self.store_products if p.name == name]
        self.refresh_inventory_table(results)

    def find_product(self, event=None):
        if not self.search_entry.winfo_exists():
            return

        query = self.search_entry.get().strip().lower()

        for child in self.catalog_scroll.winfo_children():
            try:
                child.destroy()
            except:
                pass

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
        if not hasattr(self, 'catalog_scroll') or not self.catalog_scroll.winfo_exists():
            return

        for child in self.catalog_scroll.winfo_children():
            if child.winfo_exists():
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

        modal_width = 485
        modal_height = 600

        self.center_popup(modal, modal_width, modal_height)

        modal.attributes('-topmost', True)
        modal.grab_set()

        variants = [p for p in self.store_products if p.name == category_name]

        scroll_container = ctk.CTkScrollableFrame(
            modal, fg_color="transparent", width=modal_width-20)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 15))

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
            row_frame.pack(fill='x', padx=40, pady=15)

            ctk.CTkLabel(row_frame, text=v_type.capitalize(),
                         font=('Inter', 14, 'bold')).pack(side='left', anchor='n', pady=5)

            unique_values = sorted(
                list(set(str(p.metadata.get(v_type)) for p in variants if p.metadata.get(v_type) and str(p.metadata.get(v_type)).lower() != 'none')))

            if not unique_values:
                continue

            v_var = ctk.StringVar(value=unique_values[0])
            selection_vars[v_type] = v_var

            options_frame = ctk.CTkFrame(row_frame, fg_color='transparent')
            options_frame.pack(side='left', fill='both',
                               expand=True, padx=(20, 0))

            max_columns = 3

            for index, val in enumerate(unique_values):
                row_num = index // max_columns
                col_num = index % max_columns

                ctk.CTkRadioButton(options_frame, text=val, variable=v_var, value=val, radiobutton_width=18, radiobutton_height=18,
                                   command=update_ui_on_select).grid(row=row_num, column=col_num, padx=10, pady=5, sticky='w')

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
            def safe_refresh():
                if self.winfo_exists():
                    self.update_cart_display()
                    self.refresh_catalog()

            paid = float(payment_amount)
            change = result

            final_cart = list(self.cart)
            self.cart = []
            self.after(100, safe_refresh)

            self.show_receipt_modal(final_cart, total, paid, change)

        else:
            messagebox.showerror('Checkout Error', result)

    def show_receipt_modal(self, cart, total, paid, change):
        receipt_win = ctk.CTkToplevel(self)
        receipt_win.title('Transaction Success')

        self.center_popup(receipt_win, 400, 700)
        receipt_win.attributes('-topmost', True)
        receipt_win.grab_set()

        paper = ctk.CTkFrame(receipt_win, fg_color='white', corner_radius=5)
        paper.pack(fill='both', expand=True, padx=30, pady=30)

        receipt_text = engine.generate_receipt_text(cart, total, paid, change)

        label = ctk.CTkLabel(paper, text=receipt_text, font=(
            'Consolas', 13), justify='left', text_color='black')
        label.pack(pady=20, padx=10)

        ctk.CTkButton(receipt_win, text='DONE', height=40, command=receipt_win.destroy, fg_color='#2ecc71',
                      hover_color='#27ae60', font=('Inter', 14, 'bold')).pack(pady=(0, 20), padx=30, fill='x')

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
        if not self.cart_items_frame.winfo_exists():
            return

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
                messagebox.showinfo('Success', 'Product updated!')
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
            messagebox.showinfo('Undo', 'No more actions to undo.')

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
        self.focus_set()
        self.metadata_rows = [
            r for r in self.metadata_rows if r[0] != row_frame]
        try:
            if row_frame.winfo_exists():
                row_frame.destroy()
        except:
            pass

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
            }

            for _, key_ent, val_ent in self.metadata_rows:
                key = key_ent.get().strip().lower()
                val = val_ent.get().strip()
                if key and val:
                    data[key] = val

            success, result = engine.add_new_product(data, self.store_products)

            if success:
                new_id = result

                def clear_and__show():
                    if not self.winfo_exists():
                        return

                    self.focus_set()

                    messagebox.showinfo(
                        'Success', f'Product Added! New Barcode: {new_id}')
                    barcode_path = engine.generate_product_barcode(new_id)
                    self.show_barcode_popup(barcode_path, new_id)

                    for entry in [self.new_name, self.new_price, self.new_stock, self.new_category]:
                        try:
                            if entry.winfo_exists():
                                entry.delete(0, 'end')
                        except Exception:
                            pass

                    temp_rows = list(self.metadata_rows)
                    self.metadata_rows = []

                    for row_item in temp_rows:
                        f_frame = row_item[0]
                        try:
                            if f_frame.winfo_exists():
                                f_frame.destroy()
                        except:
                            pass

                    self.refresh_catalog()
                self.after(100, clear_and__show)

            else:
                messagebox.showerror('Error', result)

        except ValueError:
            messagebox.showerror('Error', 'Price and Stock must be numbers!')
            return

    def show_barcode_popup(self, image_path, p_id):
        from PIL import Image
        pop = ctk.CTkToplevel(self)
        pop.title(f'Barcode Created: {p_id}')
        self.center_popup(pop, 450, 500)
        pop.attributes('-topmost', True)
        pop.grab_set()

        ctk.CTkLabel(pop, text='Barcode Generated Successfully!', font=(
            'Inter', 18, 'bold'), text_color='#27ae60').pack(pady=20)

        pil_img = Image.open(image_path)
        img = ctk.CTkImage(light_image=pil_img, size=(350, 150))

        ctk.CTkLabel(pop, image=img, text='').pack(pady=10)

        ctk.CTkLabel(pop, text=f'Manual Input Code: {p_id}', font=(
            'Consolas', 14), fg_color='#f0f0f0').pack(pady=10, padx=20, fill='x')

        def print_barcode():
            import os
            try:
                os.startfile(os.path.abspath(image_path), 'print')
            except Exception as e:
                messagebox.showerror(
                    'Print Error', f'Could not open print dialog {e}')

        ctk.CTkButton(pop, text='🖨️ PRINT BARCODE', command=print_barcode,
                      height=45, fg_color='#2980b9').pack(pady=20, padx=50, fill='x')
        ctk.CTkButton(pop, text='CLOSE', command=pop.destroy,
                      fg_color='transparent', text_color='grey').pack(pady=5)

    def filter_inventory_by_name(self, name):
        results = [p for p in self.store_products if p.name == name]

        results.sort(key=lambda p: p.get_variant_label())

        for child in self.inventory_scroll.winfo_children():
            child.destroy()

        w_var = 250
        w_price = 120
        w_stock = 80

        back_btn = ctk.CTkButton(self.inventory_scroll, text='← Back to All Products',
                                 fg_color='#3498db', text_color='white', command=self.refresh_inventory_table)
        back_btn.pack(anchor='w', padx=10, pady=10)
        for product in results:
            row = ctk.CTkFrame(self.inventory_scroll, fg_color='transparent')
            row.pack(fill='x', pady=2)

            ctk.CTkLabel(row, text=product.get_variant_label(),
                         width=w_var).pack(side='left', padx=10)
            ctk.CTkLabel(row, text=f'₱{product.price:.2f}', width=w_price).pack(
                side='left', padx=10)
            ctk.CTkLabel(row, text=str(product.stock),
                         width=w_stock).pack(side='left', padx=10)

            btn_frame = ctk.CTkFrame(row, fg_color='transparent')
            btn_frame.pack(side='right', padx=10)

            ctk.CTkButton(btn_frame, text='Edit', width=60, fg_color='#3498db',
                          command=lambda p=product: self.open_edit_modal(p)).pack(side='left', padx=5)
            ctk.CTkButton(btn_frame, text='Delete', width=60, fg_color='#e74c3c',
                          command=lambda p=product: self.confirm_delete(p)).pack(side='left', padx=5)

    def handle_eod_report(self):
        dialog = ctk.CTkInputDialog(
            text='Type "CONFIRM" to generate the End of Day report:',
            title='Confirm End of Day'
        )
        dialog.after(10, lambda: self.center_popup(dialog, 400, 200))
        user_input = dialog.get_input()

        if user_input is None:
            return
        if user_input.strip().upper() != 'CONFIRM':
            messagebox.showwarning('Cancelled', 'Incorrect confirmation')
            return

        report = engine.get_daily_summary()

        dash = ctk.CTkToplevel(self)
        dash.title(f'EOD Report - {report["date"]}')
        self.center_popup(dash, 900, 650)
        dash.attributes('-topmost', True)

        header = ctk.CTkFrame(dash, fg_color='#2c3e50',
                              height=80, corner_radius=0)
        header.pack(fill='x')
        ctk.CTkLabel(header, text=f'Daily Performance: {report["date"]}', font=(
            'Inter', 24, 'bold'), text_color='white').pack(pady=20)

        stats_frame = ctk.CTkFrame(dash, fg_color='transparent')
        stats_frame.pack(fill='x', padx=20, pady=20)

        def create_stat_card(parent, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, width=350, height=100)
            card.pack(side='left', expand=True, padx=10)
            ctk.CTkLabel(card, text=title, font=("Inter", 14),
                         text_color="white").pack(pady=(15, 0))
            ctk.CTkLabel(card, text=value, font=("Inter", 32, "bold"),
                         text_color="white").pack(pady=(0, 15))

        create_stat_card(stats_frame, 'Total Revenue',
                         f'₱{report["revenue"]:.2f}', '#27ae60')
        create_stat_card(stats_frame, 'Transctions',
                         str(report["transactions"]), '#2980b9')

        content_contianer = ctk.CTkFrame(dash, fg_color='transparent')
        content_contianer.pack(side='left', fill='both',
                               expand=False, padx=(0, 10))

        list_frame = ctk.CTkScrollableFrame(
            content_contianer, width=300, label_text="Top Selling Items", label_font=("Inter", 14, "bold"))
        list_frame.pack(side='left', fill='both', expand=False, padx=(0, 10))

        if report['category_sales']:
            sorted_sales = sorted(
                report['category_sales'].items(), key=lambda x: x[1], reverse=True)

            for index, (name, count) in enumerate(sorted_sales):
                item_row = ctk.CTkFrame(list_frame, fg_color='transparent')
                item_row.pack(fill='x', pady=2)

                rank_label = f'#{index+1}'
                ctk.CTkLabel(item_row, text=rank_label, font=(
                    "Inter", 12, "bold"), text_color="#2980b9", width=30).pack(side='left')
                ctk.CTkLabel(item_row, text=name, font=(
                    "Inter", 12)).pack(side='left', padx=5)
                ctk.CTkLabel(item_row, text=f"{count} sold", font=(
                    "Inter", 12, "italic"), text_color="grey").pack(side='right')

                ctk.CTkFrame(list_frame, height=1, fg_color="#dbdbdb").pack(
                    fill='x', padx=5, pady=2)
        else:
            ctk.CTkLabel(list_frame, text='No items sold today').pack(pady=20)

        chart_frame = ctk.CTkFrame(dash, fg_color='white', corner_radius=15)
        chart_frame.pack(side='left', fill='both',
                         expand=True, padx=20, pady=(0, 20))

        if report['category_sales']:
            fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
            labels = report['category_sales'].keys()
            sizes = report['category_sales'].values()

            cmap = plt.get_cmap('tab20')
            dynamic_colors = [cmap(i/len(labels)) for i in range(len(labels))]

            ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                   startangle=140, colors=dynamic_colors)
            ax.set_title('Sales Distribution by Item')

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        else:
            ctk.CTkLabel(chart_frame, text='No chart data available for today.',
                         text_color='grey').pack(expand=True)

    def on_closing(self):
        try:
            engine.save_inventory(self.store_products)
            import matplotlib.pyplot as plt
            plt.close('all')
            self.quit()
            self.destroy()

        except:
            pass

        finally:
            import os
            os._exit(0)

    def clear_inventory_filter(self):
        self.inv_search_entr.delete(0, 'end')
        self.refresh_inventory_table()
# Under Construction
#
