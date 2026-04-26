import datetime
import time
import flet as ft
import threading
from core import engine
from core.models import Product
from core.scanner import BarcodeScanner


def pos_view_content(page: ft.Page):
    cart_state = {}

    all_products = engine.load_inventory()

    grouped_products = {}

    scanner_lbl = ft.Text('📷 Scanner: starting...', size=12, color='orange')

    def on_barcode_scanned(barcode_val):
        def update():
            match = next((p for p in all_products if str(
                p.barcode) == str(barcode_val)), None)

            if match:
                if match.stock > 0:
                    add_item(match, 1)
                    scanner_lbl.value = f'✅ Added: {match.name} ({match.get_variant_label()})'
                    scanner_lbl.color = 'green'
                else:
                    scanner_lbl.value = f'⚠️ Out of stock: {match.name}'
                    scanner_lbl.color = 'orange'
            else:
                scanner_lbl.value = f'❌ Not found: {barcode_val}'
                scanner_lbl.color = 'red'

            page.update()
        page.run_thread(update)

    camera_index = (page.data or {}).get('camera_index', 0)
    scanner = BarcodeScanner(
        on_scan_callback=on_barcode_scanned, camera_index=camera_index)

    def delayed_start():
        time.sleep(1.5)
        scanner.start()

        def update_label():
            scanner_lbl.value = '📷 Scanner ready'
            scanner_lbl.color = 'grey'
            page.update()
        page.run_thread(update_label)

    threading.Thread(target=delayed_start, daemon=True).start()

    page.on_close = lambda e: scanner.stop()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == 'Enter' and not e.shift and not e.ctrl:
            if cart_state:
                process_checkout(None)
    page.on_keyboard_event = on_keyboard

    def update_cart_math(e=None):
        total = sum(item['product'].price * item['qty']
                    for item in cart_state.values())
        total_lbl.value = f'Total: ₱{total:.2f}'

        page.update()

    def refresh_cart_ui():
        cart_list.controls.clear()

        for key, item in cart_state.items():
            p = item['product']
            qty = item['qty']

            def create_qty_handler(k, delta, prod):
                def handler(e):
                    new_qty = cart_state[k]['qty']+delta
                    if new_qty <= 0:
                        del cart_state[k]
                    elif new_qty <= prod.stock:
                        cart_state[k]['qty'] = new_qty
                    refresh_cart_ui()
                return handler

            row = ft.Container(
                bgcolor='white',
                padding=10,
                border_radius=8,
                content=ft.Row([
                    ft.Column([
                        ft.Text(p.name, weight='bold', size=14, no_wrap=False,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(p.get_variant_label(), size=11, color='grey'),
                        ft.Text(f'₱{p.price:.2f}', size=12),
                    ], expand=True),
                    ft.IconButton(icon=ft.Icons.REMOVE, icon_color='red',
                                  on_click=create_qty_handler(key, -1, p)),
                    ft.Text(str(qty), weight='bold', size=16),
                    ft.IconButton(icon=ft.Icons.ADD, icon_color='green',
                                  on_click=create_qty_handler(key, 1, p)),
                ])
            )
            cart_list.controls.append(row)

        update_cart_math()
        page.update()

    for p in all_products:
        if p.name not in grouped_products:
            grouped_products[p.name] = []
        grouped_products[p.name].append(p)

    product_grid = ft.GridView(
        expand=True,
        max_extent=250,
        child_aspect_ratio=1.0,
        spacing=20,
        run_spacing=20,
        padding=10,
    )

    cart_list = ft.ListView(expand=True, spacing=10)
    total_lbl = ft.Text('Total: ₱0.00', size=30, weight='bold')

    def add_item(p: Product, qty: int):
        key = f'{p.name} - {p.get_variant_label()}'
        if key in cart_state:
            if cart_state[key]['qty']+qty <= p.stock:
                cart_state[key]['qty'] += qty
        else:
            if qty <= p.stock:
                cart_state[key] = {'product': p, 'qty': qty}
        refresh_cart_ui()

    def process_checkout(e):
        total = sum(item['product'].price * item['qty']
                    for item in cart_state.values())

        if total == 0:
            return

        payment_method = {'value': 'Cash'}
        cash_tendered = {'value': 0.0}
        partial_cash = {'value': 0.0}

        method_lbl = ft.Text('Cash', weight='bold', size=16, color='#27ae60')
        change_preview = ft.Text('', size=13, color='grey')
        credit_fields = ft.Column([], visible=False, spacing=8)

        customer_field = ft.TextField(label='Customer Name', border_radius=8)
        due_date_field = ft.TextField(
            label='Due Date (e.g. 2026-05-01)', border_radius=8)
        partial_field = ft.TextField(
            label='Partial Cash Payment (₱)',
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            hint_text='0 if fully on credit'
        )

        def update_preview(e=None):
            method = payment_method['value']

            if method == 'Credit':
                try:
                    p = float(partial_field.value or 0)
                except ValueError:
                    p = 0.0
                partial_cash['value'] = p
                remaining = total-p
                change_preview.value = f'Amount on credit: ₱{remaining:.2f}'
                change_preview.color = '#e67e22'
            else:
                try:
                    cash = float(cash_field.value or 0)
                except ValueError:
                    cash = 0.0
                cash_tendered['value'] = cash
                if cash == 0:
                    change_preview.value = ''
                elif cash < total:
                    change_preview.value = f'Needed: ₱{total - cash:.2f}'
                    change_preview.color = 'red'
                else:
                    change_preview.value = f'Change: ₱{cash-total:.2f}'
                    change_preview.color = 'green'

            change_preview.update()

        def confirm_payment(e):
            method = payment_method['value']

            if method == 'Credit':
                customer = customer_field.value.strip()
                due = due_date_field.value.strip()
                if not customer:
                    customer_field.error_text = 'Required'
                    customer_field.update()
                    return
                if not due:
                    due_date_field.error_text = 'Required'
                    due_date_field.update()
                    return

                try:
                    p_cash = float(partial_field.value or 0)
                except ValueError:
                    p_cash = 0.0

                amount_on_credit = total - p_cash
                paid_amount = p_cash
                change = 0.0

                # Save credit entry
                engine.save_credit_entry(
                    customer_name=customer,
                    amount_owed=amount_on_credit,
                    due_date=due,
                    partial_cash=p_cash
                )

            else:
                try:
                    cash = float(cash_field.value or 0)
                except ValueError:
                    cash = 0.0

                if cash < total:
                    cash_field.error_text = f'Need at least ₱{total:.2f}'
                    cash_field.update()
                    return

                paid_amount = cash
                change = cash - total
                p_cash = cash

            page.pop_dialog()
            complete_checkout(method, paid_amount, change,
                              partial_cash=p_cash if method == 'Credit' else paid_amount)

        cash_field = ft.TextField(
            label='Cash Amount Tendered (₱)',
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            autofocus=False,
            on_change=update_preview,
            on_submit=confirm_payment,
        )

        def select_method(method):
            payment_method['value'] = method
            method_lbl.value = method
            method_lbl.color = {
                'Cash': '#27ae60',
                'GCash': '#1565c0',
                'Maya': '#00897b',
                'Credit': '#e67e22'
            }.get(method, 'grey')
            credit_fields.visible = (method == 'Credit')
            cash_field.visible = (method != 'Credit')
            update_preview()
            method_lbl.update()
            credit_fields.update()
            cash_field.update()

            if method == 'Credit':
                customer_field.focus()
            else:
                cash_field.focus()

        credit_fields.controls = [
            customer_field, due_date_field, partial_field]

        def on_payment_keyboard(e: ft.KeyboardEvent):
            key = e.key.replace('Numpad ', '')
            if e.key == '1':
                select_method('Cash')
            elif e.key == '2':
                select_method('GCash')
            elif e.key == '3':
                select_method('Maya')
            elif e.key == '4':
                select_method('Credit')
            elif e.key == 'Enter':
                confirm_payment(e)
        page.on_keyboard_event = on_payment_keyboard

        method_buttons = ft.Row([
            ft.ElevatedButton('[1]💵 Cash', on_click=lambda e: select_method('Cash'),
                              style=ft.ButtonStyle(bgcolor='#27ae60', color='white',
                                                   shape=ft.RoundedRectangleBorder(radius=8))),
            ft.ElevatedButton('[2]📱 GCash', on_click=lambda e: select_method('GCash'),
                              style=ft.ButtonStyle(bgcolor='#1565c0', color='white',
                                                   shape=ft.RoundedRectangleBorder(radius=8))),
            ft.ElevatedButton('[3]🟢 Maya', on_click=lambda e: select_method('Maya'),
                              style=ft.ButtonStyle(bgcolor='#00897b', color='white',
                                                   shape=ft.RoundedRectangleBorder(radius=8))),
            ft.ElevatedButton('[4]📋 Credit', on_click=lambda e: select_method('Credit'),
                              style=ft.ButtonStyle(bgcolor='#e67e22', color='white',
                                                   shape=ft.RoundedRectangleBorder(radius=8))),
        ], spacing=8, wrap=True)

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'Payment — Total: ₱{total:.2f}', weight='bold'),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text('Select Payment Method', size=13, color='grey'),
                    method_buttons,
                    ft.Divider(),
                    ft.Row([ft.Text('Method:', size=13), method_lbl], spacing=8),
                    cash_field,
                    credit_fields,
                    change_preview,
                ], spacing=10, tight=True)
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text('Cancel'),
                    on_click=lambda e: (
                        setattr(page, 'on_keyboard_event', on_keyboard),
                        page.pop_dialog()
                    )
                ),
                ft.ElevatedButton(
                    content=ft.Text('Confirm Payment'),
                    on_click=confirm_payment,
                    style=ft.ButtonStyle(bgcolor='#4A4440', color='white',
                                         shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            modal=True
        ))

    def complete_checkout(method, paid_amount, change, partial_cash=0.0):
        total = sum(item['product'].price * item['qty']
                    for item in cart_state.values())

        receipt_text = (
            "======= DAD'S STORE =======\n"
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Payment: {method}\n"
            "---------------------------\n"
        )

        flat_cart = []
        for item in cart_state.values():
            p = item['product']
            qty = item['qty']
            sub = p.price * qty
            p.stock -= qty
            name_str = f'{p.name} ({p.get_variant_label()})'
            receipt_text += f'{name_str[:20]:<20} {qty} x ₱{sub:.2f}\n'
            for _ in range(qty):
                flat_cart.append(p)

        if method == 'Credit':
            remaining = total - partial_cash
            receipt_text += (
                "---------------------------\n"
                f"Total:      ₱{total:.2f}\n"
                f"Cash Paid:  ₱{partial_cash:.2f}\n"
                f"On Credit:  ₱{remaining:.2f}\n"
                "===========================\n"
                "Thank you for shopping!"
            )
        else:
            receipt_text += (
                "---------------------------\n"
                f"Total:      ₱{total:.2f}\n"
                f"Cash:       ₱{paid_amount:.2f}\n"
                f"Change:     ₱{change:.2f}\n"
                "===========================\n"
                "Thank you for shopping!"
            )

        engine.log_sale(flat_cart, total, paid_amount,
                        change, payment_method=method)
        engine.save_inventory(all_products)

        def close_receipt(e):
            page.pop_dialog()
            cart_state.clear()
            refresh_cart_ui()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Checkout Successful!',
                          weight='bold', color='green'),
            content=ft.Text(receipt_text, font_family='monospace'),
            actions=[ft.TextButton('Close & New Order',
                                   on_click=close_receipt)],
            modal=True
        ))

    def open_variant_selector(product_name):
        variants = grouped_products[product_name]

        variant_types = []
        for p in variants:
            if hasattr(p, 'metadata') and p.metadata:
                for k in p.metadata.keys():
                    if k not in variant_types:
                        variant_types.append(k)

        state = {
            'selections': {},
            'qty': 1
        }
        price_label = ft.Text(
            f'₱{variants[0].price:.2f}', size=28, weight='bold')
        stock_label = ft.Text('', italic=True, size=13)
        qty_var = ft.TextField(
            value='1', text_align='center', width=50, height=40, content_padding=0)

        add_btn = ft.ElevatedButton(
            '🛒 Add to Cart',
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor='#5c6370',
                color='white',
            )
        )

        def get_selected_product():
            for p in variants:
                match = True
                for v_type, selected_val in state['selections'].items():
                    if not hasattr(p, 'metadata') or str(p.metadata.get(v_type)) != selected_val:
                        match = False
                        break

                if match:
                    return p

            return None

        def update_ui_on_select(e=None, is_init=False):
            selected = get_selected_product()

            if selected:
                price_label.value = f'₱{selected.price:.2f}'
                stock_label.value = f'Stock: {selected.stock}'
                stock_label.color = 'red' if selected.stock <= 5 else 'green'
                add_btn.disabled = False
            else:
                price_label.value = '---'
                stock_label.value = 'Out of Stock / Unavailable'
                stock_label.color = 'grey'
                add_btn.disabled = True

            qty_var.value = str(state['qty'])

            if not is_init:
                price_label.update()
                stock_label.update()
                qty_var.update()
                add_btn.update()

        dynamic_rows = []

        def create_radio_handler(v_type_key):
            def on_change(e):
                state['selections'][v_type_key] = e.control.value
                update_ui_on_select()
            return on_change

        for v_type in variant_types:
            unique_values = sorted(list(set(str(p.metadata.get(v_type)) for p in variants if hasattr(
                p, 'metadata') and p.metadata and p.metadata.get(v_type) and str(p.metadata.get(v_type)).lower() != 'none')))

            if not unique_values:
                continue

            state['selections'][v_type] = unique_values[0]

            max_columns = 3
            radio_rows = []

            for i in range(0, len(unique_values), max_columns):
                chunk = unique_values[i:i + max_columns]
                radio_rows.append(
                    ft.Row([ft.Radio(value=val, label=val)for val in chunk])
                )

            radio_group = ft.RadioGroup(
                content=ft.Column(radio_rows),
                value=unique_values[0],
                on_change=create_radio_handler(v_type)
            )

            row_frame = ft.Row([
                ft.Text(v_type.capitalize(), weight='bold', size=14, width=80),
                radio_group
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)

            dynamic_rows.append(row_frame)
            dynamic_rows.append(ft.Container(height=10))

        def change_qty(amount):
            new_val = state['qty']+amount
            if 1 <= new_val <= 99:
                state['qty'] = new_val
                update_ui_on_select()

        qty_section = ft.Container(
            bgcolor='#f2f2f2',
            border_radius=10,
            padding=10,
            content=ft.Row([
                ft.ElevatedButton(
                    '-', width=40, on_click=lambda _: change_qty(-1)),
                qty_var,
                ft.ElevatedButton(
                    '+', width=40, on_click=lambda _: change_qty(1)),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        def add_and_close(e):
            prod = get_selected_product()
            if prod:
                add_item(prod, state['qty'])
                page.pop_dialog()

        add_btn.on_click = add_and_close

        dialog_content = ft.Column(controls=[
            ft.Text(product_name.capitalize(), size=22,
                    weight='bold', color='black'),
            ft.Text('Select Options', color='grey', size=12),
            ft.Container(height=10),

            price_label,
            ft.Container(height=20),

            *dynamic_rows,

            ft.Container(height=10),
            qty_section,
            ft.Container(height=10),

            stock_label,
            ft.Container(height=20),


            add_btn
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, width=400, scroll=ft.ScrollMode.AUTO,
            spacing=15,)

        dialog = ft.AlertDialog(
            content=ft.Container(content=dialog_content,
                                 padding=20, bgcolor='white',)
        )
        update_ui_on_select(is_init=True)

        page.show_dialog(dialog)

    def create_category_card(name, variants):

        preview_price = [v.price for v in variants]
        min_p = min(preview_price)
        max_p = max(preview_price)

        if min_p == max_p:
            price_text = f'₱{min_p:.2f}'
        else:
            price_text = f'₱{min_p:.2f} - ₱{max_p:.2f}'

        return ft.Container(
            bgcolor='white',
            border_radius=20,
            padding=20,
            shadow=ft.BoxShadow(blur_radius=15, color='black12'),
            on_click=lambda _: open_variant_selector(name),
            content=ft.Column(
                controls=[
                    ft.Text(name, weight='bold', size=18,
                            color='black'),
                    ft.Text(f'{len(variants)} Variants',
                            color='grey', size=12),
                    ft.Text(price_text, size=14,
                            color='#A4907C', weight='bold')
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            )
        )

    for name, variants in grouped_products.items():
        product_grid.controls.append(create_category_card(name, variants))

    def on_pos_search(e):
        query = e.control.value.strip()
        if not query:
            product_grid.controls.clear()
            for name, variants in grouped_products.items():
                product_grid.controls.append(
                    create_category_card(name, variants))

        else:
            results = engine.search_products(query, all_products)
            matched_names = set(p.name for p in results)
            product_grid.controls.clear()
            for name, variants in grouped_products.items():
                if name in matched_names:
                    product_grid.controls.append(
                        create_category_card(name, variants))

        page.update()

    return ft.Row([
        ft.Column([
            ft.TextField(
                hint_text='Search products...',
                prefix_icon='search',
                border_radius=15,
                bgcolor='white',
                on_change=on_pos_search
            ),
            product_grid
        ], expand=2),
        ft.Container(
            content=ft.Column([
                ft.Text('Current Order', size=25, weight='bold'),
                ft.Divider(),
                scanner_lbl,
                ft.Container(content=cart_list, expand=True),
                ft.Divider(),
                total_lbl,
                ft.Container(height=10),

                ft.ElevatedButton(
                    'COMPLETE CHECKOUT',
                    height=55,
                    width=float('inf'),
                    bgcolor='#4A4440',
                    color='white',
                    on_click=process_checkout,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10))
                )
            ]),
            expand=1,
            bgcolor='#E8E2DE',
            padding=20,
            border_radius=20
        )
    ], expand=True)
