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

        def select_and_proceed(method):
            page.on_keyboard_event = on_keyboard
            page.pop_dialog()
            show_payment_dialog(method)

        def on_method_keyboard(e: ft.KeyboardEvent):
            key = e.key.replace('Numpad ', '')
            if key == '1':
                select_and_proceed('Cash')
            elif key == '2':
                select_and_proceed('GCash')
            elif key == '3':
                select_and_proceed('Credit')
            elif key == 'Escape':
                page.on_keyboard_event = on_keyboard
                page.pop_dialog()

        page.on_keyboard_event = on_method_keyboard

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'Select Payment — Total: ₱{total:.2f}',
                          weight='bold'),
            content=ft.Column([
                ft.Text('How is the customer paying?',
                        color='grey', size=13),
                ft.Container(height=8),
                ft.Row([
                    ft.ElevatedButton(
                        '[1] 💵 Cash', expand=True, height=60,
                        on_click=lambda e: select_and_proceed('Cash'),
                        style=ft.ButtonStyle(bgcolor='#27ae60', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.ElevatedButton(
                        '[2] 📱 GCash', expand=True, height=60,
                        on_click=lambda e: select_and_proceed('GCash'),
                        style=ft.ButtonStyle(bgcolor='#1565c0', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.ElevatedButton(
                        '[3] 📋 Credit', expand=True, height=60,
                        on_click=lambda e: select_and_proceed('Credit'),
                        style=ft.ButtonStyle(bgcolor='#e67e22', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                ], spacing=10),
            ], tight=True, spacing=8, width=380),
            actions=[
                ft.TextButton(
                    content=ft.Text('Cancel'),
                    on_click=lambda e: (
                        setattr(page, 'on_keyboard_event', on_keyboard),
                        page.pop_dialog()
                    )
                )
            ],
            modal=True
        ))

    def show_payment_dialog(method):
        import os
        import base64
        total = sum(item['product'].price * item['qty']
                    for item in cart_state.values())

        if method == 'Cash':
            change_lbl = ft.Text('', size=13, color='grey')
            cash_field = ft.TextField(
                label='Cash Amount Tendered (₱)',
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=8,
                autofocus=True,
            )

            def on_cash_change(e):
                try:
                    cash = float(cash_field.value or 0)
                except ValueError:
                    cash = 0.0
                if cash == 0:
                    change_lbl.value = ''
                elif cash < total:
                    change_lbl.value = f'Needed: ₱{total - cash:.2f}'
                    change_lbl.color = 'red'
                else:
                    change_lbl.value = f'Change: ₱{cash - total:.2f}'
                    change_lbl.color = 'green'
                change_lbl.update()

            cash_field.on_change = on_cash_change

            def confirm_cash(e):
                try:
                    cash = float(cash_field.value or 0)
                except ValueError:
                    cash = 0.0
                if cash < total:
                    cash_field.error_text = f'Need at least ₱{total:.2f}'
                    cash_field.update()
                    return
                page.on_keyboard_event = on_keyboard
                page.pop_dialog()
                complete_checkout('Cash', cash, cash - total)

            cash_field.on_submit = confirm_cash

            page.show_dialog(ft.AlertDialog(
                title=ft.Text(f'💵 Cash Payment — ₱{total:.2f}', weight='bold'),
                content=ft.Column([cash_field, change_lbl],
                                  tight=True, spacing=10, width=350),
                actions=[
                    ft.TextButton(
                        content=ft.Text('Back'),
                        on_click=lambda e: (
                            page.pop_dialog(), process_checkout(None))
                    ),
                    ft.ElevatedButton(
                        content=ft.Text('Confirm'),
                        on_click=confirm_cash,
                        style=ft.ButtonStyle(bgcolor='#27ae60', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], modal=True
            ))

        elif method == 'GCash':
            qr_path = None
            for ext in ['png', 'jpg', 'jpeg']:
                candidate = os.path.join('qr_codes', f'gcash.{ext}')
                if os.path.exists(candidate):
                    qr_path = candidate
                    break

            if qr_path:
                with open(qr_path, 'rb') as f:
                    qr_b64 = base64.b64encode(f.read()).decode()
                ext = qr_path.split('.')[-1]
                qr_widget = ft.Image(
                    src=f'data:image/{ext};base64,{qr_b64}',
                    width=350, height=350, fit='contain'
                )
            else:
                qr_widget = ft.Container(
                    width=350, height=350,
                    bgcolor='#f0f0f0',
                    border_radius=10,
                    content=ft.Column([
                        ft.Icon(ft.Icons.QR_CODE, size=60, color='grey'),
                        ft.Text('No QR code found.', color='grey'),
                        ft.Text('Place gcash.png inside the qr_codes folder.',
                                color='grey', size=11,
                                text_align=ft.TextAlign.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8),
                    alignment=ft.Alignment(0, 0)
                )

            def confirm_gcash(e):
                page.on_keyboard_event = on_keyboard
                page.pop_dialog()
                complete_checkout('GCash', total, 0.0)

            page.show_dialog(ft.AlertDialog(
                title=ft.Text(f'📱 GCash Payment — ₱{total:.2f}',
                              weight='bold', color='#1565c0'),
                content=ft.Column([
                    ft.Text('Ask customer to scan the GCash QR code',
                            color='grey', size=13),
                    ft.Text(f'Amount: ₱{total:.2f}',
                            size=20, weight='bold', color='#1565c0'),
                    ft.Container(height=8),
                    qr_widget,
                    ft.Container(height=8),
                    ft.Text('Confirm only after payment is received.',
                            color='grey', size=11, italic=True),
                ], tight=True, spacing=6, width=350,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                actions=[
                    ft.TextButton(
                        content=ft.Text('Back'),
                        on_click=lambda e: (
                            page.pop_dialog(), process_checkout(None))
                    ),
                    ft.ElevatedButton(
                        content=ft.Text('✅ Payment Received'),
                        on_click=confirm_gcash,
                        style=ft.ButtonStyle(bgcolor='#1565c0', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], modal=True
            ))

        elif method == 'Credit':
            customer_field = ft.TextField(label='Customer Name',
                                          border_radius=8, autofocus=True)
            due_field = ft.TextField(label='Due Date (e.g. 2026-05-31)',
                                     border_radius=8)
            partial_field = ft.TextField(
                label='Partial Cash (₱) — 0 if fully on credit',
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=8
            )
            credit_preview = ft.Text('', size=13, color='#e67e22')

            def on_partial_change(e):
                try:
                    p = float(partial_field.value or 0)
                except ValueError:
                    p = 0.0
                credit_preview.value = f'Amount on credit: ₱{total - p:.2f}'
                credit_preview.update()

            partial_field.on_change = on_partial_change

            def confirm_credit(e):
                customer = customer_field.value.strip()
                due = due_field.value.strip()
                if not customer:
                    customer_field.error_text = 'Required'
                    customer_field.update()
                    return
                if not due:
                    due_field.error_text = 'Required'
                    due_field.update()
                    return
                try:
                    p_cash = float(partial_field.value or 0)
                except ValueError:
                    p_cash = 0.0
                engine.save_credit_entry(
                    customer_name=customer,
                    amount_owed=total - p_cash,
                    due_date=due,
                    partial_cash=p_cash
                )
                page.on_keyboard_event = on_keyboard
                page.pop_dialog()
                complete_checkout('Credit', p_cash, 0.0, partial_cash=p_cash)

            page.show_dialog(ft.AlertDialog(
                title=ft.Text(f'📋 Credit — ₱{total:.2f}',
                              weight='bold', color='#e67e22'),
                content=ft.Column([
                    customer_field, due_field, partial_field, credit_preview
                ], tight=True, spacing=10, width=350),
                actions=[
                    ft.TextButton(
                        content=ft.Text('Back'),
                        on_click=lambda e: (
                            page.pop_dialog(), process_checkout(None))
                    ),
                    ft.ElevatedButton(
                        content=ft.Text('Confirm Credit'),
                        on_click=confirm_credit,
                        style=ft.ButtonStyle(bgcolor='#e67e22', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], modal=True
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
