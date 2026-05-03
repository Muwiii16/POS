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

    dialog_state = {'open': None, 'close_fn': None, 'update_fn': None}
    cash_input_buffer = {'value': ''}
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

    def finalize(method, paid, partial_cash=0.0):
        import datetime
        total_snapshot = current_total
        change = paid - total_snapshot if method == 'Cash' and paid > total_snapshot else 0.0

        receipt_text = (
            "======= DAD'S STORE =======\n"
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Payment: {method}\n"
            "---------------------------\n"
        )
        for item in cart_state.values():
            p = item['product']
            qty = item['qty']
            sub = p.price * qty
            name_str = f'{p.name} ({p.get_variant_label()})'
            receipt_text += f'{name_str[:20]:<20} {qty} x ₱{sub:.2f}\n'

        if method == 'Credit':
            remaining = total_snapshot - partial_cash
            receipt_text += (
                "---------------------------\n"
                f"Total:      ₱{total_snapshot:.2f}\n"
                f"Cash Paid:  ₱{partial_cash:.2f}\n"
                f"On Credit:  ₱{remaining:.2f}\n"
                "===========================\n"
                "Thank you for shopping!"
            )
        else:
            receipt_text += (
                "---------------------------\n"
                f"Total:      ₱{total_snapshot:.2f}\n"
                f"Cash:       ₱{paid:.2f}\n"
                f"Change:     ₱{change:.2f}\n"
                "===========================\n"
                "Thank you for shopping!"
            )

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
        engine.log_sale(flat_cart, total_snapshot, paid, method)
        shared_state.write_checkout_done()

        cart_state.clear()
        status_lbl.value = '✅ Sale complete!'
        status_lbl.color = 'green'
        dialog_state['open'] = 'receipt'
        rebuild_cart()

        def close_receipt(e=None):
            dialog_state['open'] = None
            dialog_state['close_fn'] = None
            page.on_keyboard_event = None
            shared_state.clear_cart_file()
            page.pop_dialog()

        dialog_state['close_fn'] = close_receipt
        close_btn = ft.TextButton('Close & New Order', on_click=close_receipt)

        def on_receipt_keyboard(e: ft.KeyboardEvent):
            if e.key == 'Enter' or e.key == 'Numpad Enter':
                page.on_keyboard_event = None
                close_receipt()
        page.on_keyboard_event = on_receipt_keyboard

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Checkout Successful!',
                          weight='bold', color='green'),
            content=ft.Text(receipt_text, font_family='monospace'),
            actions=[close_btn],
            modal=True
        ))

    def show_cash_dialog():
        dialog_state['open'] = 'cash'
        cash_input_buffer['value'] = ''
        change_lbl = ft.Text('', size=14, color='grey')
        cash_field = ft.TextField(
            label='Cash Tendered (₱)',
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            autofocus=True,
        )

        def update_field():
            cash_field.value = cash_input_buffer['value']
            try:
                cash = float(cash_input_buffer['value'] or 0)
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
            try:
                cash_field.update()
                change_lbl.update()
            except Exception:
                pass

        def confirm(e=None):
            try:
                cash = float(cash_input_buffer['value'] or 0)
            except ValueError:
                return
            if cash < current_total:
                cash_field.error_text = 'Amount too low'
                cash_field.update()
                return
            dialog_state['open'] = None
            dialog_state['close_fn'] = None
            dialog_state['update_fn'] = None
            page.pop_dialog()
            finalize('Cash', cash)

        dialog_state['close_fn'] = confirm
        dialog_state['update_fn'] = update_field

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
            page.on_keyboard_event = None
            dialog_state['open'] = None
            page.pop_dialog()
            finalize('GCash', current_total)

        dialog_state['close_fn'] = confirm

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
        dialog_state['close_fn'] = None
        dialog_state['update_fn'] = None
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
            if shared_state.is_main_checkout_active():
                return
            try:
                print(
                    f'KEY: {key} | vk: {getattr(key, "vk", None)} | state: {dialog_state["open"]}')
                vk = getattr(key, 'vk', None)
                is_enter = key == pynput_kb.Key.enter or vk == 13 or str(
                    key) == 'Key.enter'
                is_esc = key == pynput_kb.Key.esc

                state = dialog_state['open']

                if state == 'receipt':
                    return

                elif state is None:
                    if is_enter and cart_state:
                        page.run_thread(show_payment_method_dialog)

                elif state == 'method':
                    if vk == 97 or (hasattr(key, 'char') and key.char == '1'):
                        page.run_thread(lambda: select_method('Cash'))
                    elif vk == 98 or (hasattr(key, 'char') and key.char == '2'):
                        page.run_thread(lambda: select_method('GCash'))
                    elif vk == 99 or (hasattr(key, 'char') and key.char == '3'):
                        page.run_thread(lambda: select_method('Credit'))
                    elif is_esc:
                        page.run_thread(close_method_dialog)

                elif state == 'cash':
                    if is_enter:
                        fn = dialog_state.get('close_fn')
                        if fn:
                            threading.Thread(target=fn, daemon=True).start()
                    elif is_esc:
                        page.run_thread(close_cash_dialog)
                    elif key == pynput_kb.Key.backspace:
                        cash_input_buffer['value'] = cash_input_buffer['value'][:-1]
                        fn = dialog_state.get('update_fn')
                        if fn:
                            page.run_thread(fn)
                    else:
                        char = None
                        if vk and 96 <= vk <= 105:
                            char = str(vk-96)
                        elif vk == 110 or (hasattr(key, 'char') and key.char == '.'):
                            if '.' not in cash_input_buffer['value']:
                                char = '.'
                        elif hasattr(key, 'char') and key.char and key.char.isdigit():
                            char = key.char
                        if char:
                            cash_input_buffer['value'] += char
                            fn = dialog_state.get('update_fn')
                            if fn:
                                page.run_thread(fn)

                elif state in ('gcash', 'credit'):
                    if is_enter:
                        fn = dialog_state.get('close_fn')
                        if fn:
                            page.run_thread(fn)
                    elif is_esc:
                        page.run_thread(
                            close_gcash_dialog if state == 'gcash'
                            else close_credit_dialog
                        )

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
                        if dialog_state['open'] == 'receipt':
                            dialog_state['open'] = None
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
                        dialog_state['open'] = 'receipt'
                        dialog_state['close_fn'] = None
                        page.run_thread(rebuild_cart)

                    elif msg['type'] == 'idle':
                        if dialog_state['open'] == 'receipt':
                            dialog_state['open'] = None

            except Exception:
                pass

            time.sleep(0.2)

    threading.Thread(target=poll_loop, daemon=True).start()

    def move_to_monitor2():
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            if len(monitors) < 2:
                page.show_dialog(ft.AlertDialog(
                    title=ft.Text('No second monitor found'),
                    content=ft.Text('Could not detect a second monitor.'),
                    actions=[ft.TextButton(
                        'OK', on_click=lambda e: page.pop_dialog())]
                ))
                return
            second = monitors[1]
            page.window.left = second.x
            page.window.top = second.y
            page.window.width = second.width
            page.window.height = second.height
            page.update()
        except Exception as ex:
            print(f'Monitor detection error: {ex}')

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
