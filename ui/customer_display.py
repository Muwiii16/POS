import queue
import os
import base64
import threading
import time
import flet as ft
from core import engine, shared_state
from pynput import keyboard as pynput_kb


def customer_display_main(page: ft.Page):
    page.title = 'Customer Display'
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = '#F8F4F1'
    page.padding = 0
    page.window_width = 900
    page.window_height = 700
    page.window_always_on_top = True

    dialog_state = {'open': None, 'close_fn': None}
    cart_state = {}
    current_total = 0.0

    cart_list = ft.ListView(expand=True, spacing=8)
    total_lbl = ft.Text('Total: ₱0.00', size=32,
                        weight='bold', color='#4A4440')
    status_lbl = ft.Text('Waiting for items...', size=13, color='grey',
                         text_align=ft.TextAlign.CENTER)

    checkout_btn = ft.ElevatedButton(
        'CHECKOUT  [Enter]',
        height=60,
        width=float('inf'),
        bgcolor='#4A4440',
        color='white',
        disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    def rebuild_cart():
        nonlocal current_total
        cart_list.controls.clear()
        current_total = sum(v['product'].price*v['qty']
                            for v in cart_state.values())

        if not cart_state:
            checkout_btn.disabled = True
            cart_list.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text('Cart is empty', color='grey',
                                    size=16, text_align=ft.TextAlign.CENTER)
                )
            )
        else:
            checkout_btn.disabled = False
            for key, item in cart_state.items():
                p = item['product']
                qty = item['qty']
                subtotal = p.price*qty
                cart_list.controls.append(
                    ft.Container(
                        bgcolor='white',
                        border_radius=10,
                        padding=ft.padding.symmetric(
                            horizontal=16, vertical=10),
                        shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                        content=ft.Row([
                            ft.Column([
                                ft.Text(p.name, weight='bold', size=15,
                                        no_wrap=False, max_lines=2),
                                ft.Text(p.get_variant_label(),
                                        size=11, color='grey'),
                                ft.Text(f'₱{p.price:.2f} × {qty}', size=12,
                                        color='#7f8c8d'),
                            ], expand=True, spacing=2),
                            ft.Text(f'₱{subtotal:.2f}', size=15,
                                    weight='bold', color='#4A4440')
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )

        total_lbl.value = f'Total: ₱{current_total:,.2f}'
        try:
            page.update()
        except Exception:
            pass

    def finalize(method, paid):
        flat_cart = []
        for item in cart_state.values():
            flat_cart.extend([item['product']] * item['qty'])

        all_products = engine.load_inventory()
        inv_by_barcode = {str(p.barcode): p for p in all_products}
        for item in cart_state.values():
            bc = str(item['product'].barcode)
            if bc in inv_by_barcode:
                inv_by_barcode[bc].stock = max(
                    0, inv_by_barcode[bc].stock - item['qty']
                )
        engine.save_inventory(all_products)

        engine.log_sale(flat_cart, current_total, paid, method)
        shared_state.write_checkout_done()

        total_snapshot = current_total
        cart_state.clear()
        status_lbl.value = '✅ Sale complete!'
        status_lbl.color = 'green'
        rebuild_cart()

        dialog_state['open'] = 'receipt'

        def close_receipt(e=None):
            dialog_state['open'] = None
            dialog_state['close_fn'] = None
            page.pop_dialog()

        dialog_state['close_fn'] = close_receipt

        change = paid - total_snapshot if method == 'Cash' and paid > total_snapshot else 0

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('✅ Sale Complete!', weight='bold', color='#27ae60'),
            content=ft.Column([
                ft.Text(f'Method: {method}', size=14),
                ft.Text(f'Total: ₱{total_snapshot:.2f}', size=14),
                ft.Text(f'Cash: ₱{paid:.2f}' if method ==
                        'Cash' else '', size=14),
                ft.Text(f'Change: ₱{change:.2f}' if method ==
                        'Cash' else '', size=14, color='green'),
            ], tight=True, spacing=6, width=300),
            actions=[
                ft.ElevatedButton(
                    'Done [Enter]',
                    on_click=close_receipt,
                    style=ft.ButtonStyle(bgcolor='#4A4440', color='white')
                )
            ],
            modal=True
        ))

    def show_cash_dialog():
        dialog_state['open'] = 'cash'
        change_lbl = ft.Text('', size=14, color='grey')
        cash_field = ft.TextField(
            label='Cash Tendered (₱)',
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
            elif cash < current_total:
                change_lbl.value = f'Short by ₱{current_total - cash:.2f}'
                change_lbl.color = 'red'
            else:
                change_lbl.value = f'Change: ₱{cash - current_total:.2f}'
                change_lbl.color = 'green'
            change_lbl.update()

        cash_field.on_change = on_cash_change

        def confirm(e=None):
            try:
                cash = float(cash_field.value or 0)
            except ValueError:
                return
            if cash < current_total:
                cash_field.error_text = 'Amount too low'
                cash_field.update()
                return
            dialog_state['open'] = None
            page.pop_dialog()
            finalize('Cash', cash)

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(
                f'Cash Payment — ₱{current_total:.2f}', weight='bold'),
            content=ft.Column([cash_field, change_lbl],
                              tight=True, spacing=10, width=340),
            actions=[
                ft.TextButton('Cancel [Esc]',
                              on_click=lambda e: close_cash_dialog()),
                ft.ElevatedButton(
                    'Confirm [Enter]',
                    on_click=confirm,
                    style=ft.ButtonStyle(bgcolor='#27ae60', color='white')
                )
            ],
            modal=True
        ))

    def show_gcash_dialog():
        import os
        import base64
        dialog_state['open'] = 'gcash'

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
                width=300, height=300, fit='contain'
            )
        else:
            qr_widget = ft.Container(
                width=300, height=300,
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
                    spacing=8)
            )

        def confirm(e=None):
            dialog_state['open'] = None
            page.pop_dialog()
            finalize('GCash', current_total)

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'📱 GCash Payment — ₱{current_total:.2f}',
                          weight='bold', color='#1565c0'),
            content=ft.Column([
                ft.Text('Ask customer to scan the GCash QR code',
                        color='grey', size=13),
                ft.Text(f'Amount: ₱{current_total:.2f}',
                        size=20, weight='bold', color='#1565c0'),
                ft.Container(height=8),
                qr_widget,
                ft.Container(height=8),
                ft.Text('Confirm only after payment is received.',
                        color='grey', size=11, italic=True),
            ], tight=True, spacing=6, width=350,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton('Back', on_click=lambda e: (
                    close_gcash_dialog(),
                    show_payment_method_dialog()
                )),
                ft.ElevatedButton(
                    '✅ Payment Received',
                    on_click=confirm,
                    style=ft.ButtonStyle(bgcolor='#1565c0', color='white',
                                         shape=ft.RoundedRectangleBorder(radius=8))
                )
            ], modal=True
        ))

    def close_gcash_dialog():
        dialog_state['open'] = None
        page.pop_dialog()

    def show_credit_dialog():
        dialog_state['open'] = 'credit'
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
            credit_preview.value = f'Amount on credit: ₱{current_total - p:.2f}'
            credit_preview.update()

        partial_field.on_change = on_partial_change

        def confirm(e=None):
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
                amount_owed=current_total - p_cash,
                due_date=due,
                partial_cash=p_cash
            )
            dialog_state['open'] = 'None'
            page.pop_dialog()
            finalize('Credit', p_cash)

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'📋 Credit — ₱{current_total:.2f}',
                          weight='bold', color='#e67e22'),
            content=ft.Column([
                customer_field, due_field, partial_field, credit_preview
            ], tight=True, spacing=10, width=350),
            actions=[
                ft.TextButton('Back', on_click=lambda e: (
                    close_credit_dialog(),
                    show_payment_method_dialog()
                )),
                ft.ElevatedButton(
                    'Confirm Credit',
                    on_click=confirm,
                    style=ft.ButtonStyle(bgcolor='#e67e22', color='white',
                                         shape=ft.RoundedRectangleBorder(radius=8))
                )
            ], modal=True
        ))

    def close_credit_dialog():
        dialog_state['open'] = None
        page.pop_dialog()

    def close_cash_dialog():
        dialog_state['open'] = None
        page.pop_dialog()

    def close_method_dialog():
        dialog_state['open'] = None
        page.pop_dialog()

    def select_method(method):
        dialog_state['open'] = None
        page.pop_dialog()
        if method == 'Cash':
            show_cash_dialog()
        elif method == 'GCash':
            show_gcash_dialog()
        elif method == 'Credit':
            show_credit_dialog()

    def start_numpad_listener():
        def on_press(key):
            try:
                vk = getattr(key, 'vk', None)
                is_enter = key in (pynput_kb.Key.enter,) or vk == 13
                is_esc = key == pynput_kb.Key.esc

                if dialog_state['open'] is None:
                    if is_enter and cart_state:
                        page.run_thread(show_payment_method_dialog)

                elif dialog_state['open'] == 'method':
                    if vk == 97 or (hasattr(key, 'char') and key.char == '1'):
                        page.run_thread(lambda: select_method('Cash'))
                    elif vk == 98 or (hasattr(key, 'char') and key.char == '2'):
                        page.run_thread(lambda: select_method('GCash'))
                    elif vk == 99 or (hasattr(key, 'char') and key.char == '3'):
                        page.run_thread(lambda: select_method('Credit'))
                    elif is_esc:
                        page.run_thread(close_method_dialog)

                elif dialog_state['open'] in ('cash', 'gcash', 'credit'):
                    if is_esc:
                        page.run_thread(lambda: (
                            close_gcash_dialog() if dialog_state['open'] == 'gcash'
                            else close_credit_dialog()
                        ))

                elif dialog_state['open'] == 'receipt':
                    if is_enter:
                        fn = dialog_state.get('close_fn')
                        if fn:
                            page.run_thread(fn)

            except Exception:
                pass

        listener = pynput_kb.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()

    threading.Thread(target=start_numpad_listener, daemon=True).start()

    def show_payment_method_dialog():
        dialog_state['open'] = 'method'
        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'Payment — ₱{current_total:.2f}', weight='bold'),
            content=ft.Column([
                ft.Text('Select payment method:', color='grey', size=13),
                ft.Container(height=8),
                ft.Row([
                    ft.ElevatedButton(
                        '[1] 💵 Cash', expand=True, height=65,
                        on_click=lambda e: select_method('Cash'),
                        style=ft.ButtonStyle(bgcolor='#27ae60', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.ElevatedButton(
                        '[2] 📱 GCash', expand=True, height=65,
                        on_click=lambda e: select_method('GCash'),
                        style=ft.ButtonStyle(bgcolor='#1565c0', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.ElevatedButton(
                        '[3] 📋 Credit', expand=True, height=65,
                        on_click=lambda e: select_method('Credit'),
                        style=ft.ButtonStyle(bgcolor='#e67e22', color='white',
                                             shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                ], spacing=10),
            ], tight=True, spacing=8, width=400),
            actions=[
                ft.TextButton('Cancel [Esc]',
                              on_click=lambda e: close_method_dialog())
            ],
            modal=True
        ))

    def poll_loop():
        last_seen = None
        while True:
            try:
                msg = shared_state.read_cart()
                if msg and msg != last_seen:
                    last_seen = msg

                    if msg['type'] == 'cart_update':
                        cart_state.clear()
                        all_inv = engine.load_inventory()
                        inv_by_barcode = {str(p.barcode): p for p in all_inv}
                        for entry in msg['payload']:
                            key = entry['key']
                            bc = str(entry['barcode'])
                            qty = entry['qty']
                            if bc in inv_by_barcode:
                                cart_state[key] = {
                                    'product': inv_by_barcode[bc],
                                    'qty': qty
                                }
                        page.run_thread(rebuild_cart)

                    elif msg['type'] == 'checkout_done':
                        cart_state.clear()
                        status_lbl.value = '✅ Sale complete!'
                        status_lbl.color = 'green'
                        page.run_thread(rebuild_cart)

            except Exception:
                pass

            time.sleep(0.2)

    threading.Thread(target=poll_loop, daemon=True).start()

    def move_to_monitor2():
        page.window_left = 1920
        page.window_top = 0
        page.update()

    page.add(
        ft.Column([
            ft.Container(
                bgcolor='#4A4440',
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                content=ft.Row([
                    ft.Text('🛒  Customer Cart', size=20, weight='bold',
                            color='white'),
                    ft.Container(expand=True),
                    ft.TextButton(
                        '📺 Move to Monitor 2',
                        on_click=lambda e: move_to_monitor2(),
                        style=ft.ButtonStyle(color='white')
                    )
                ])
            ),
            ft.Container(
                content=cart_list,
                expand=True,
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            ),
            ft.Divider(height=1, color='#D1C7BD'),
            ft.Container(
                bgcolor='#E8E2DE',
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                content=ft.Column([
                    status_lbl,
                    total_lbl,
                    ft.Container(height=8),
                    checkout_btn,
                    ft.Text(
                        'Enter = Checkout  │  1 = Cash  │  2 = GCash  │  3 = Credit  │  Esc = Cancel',
                        size=11, color='grey',
                        text_align=ft.TextAlign.CENTER
                    )
                ], spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ], expand=True, spacing=0)
    )

    rebuild_cart()
