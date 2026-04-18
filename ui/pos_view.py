
import datetime
import flet as ft
from core import engine
from core.models import Product


def pos_view_content(page: ft.Page):
    cart_state = {}
    cart_list = ft.ListView(expand=True, spacing=10)
    total_lbl = ft.Text('Total: ₱0.00', size=30, weight='bold')
    change_lbl = ft.Text('Change: ₱0.00', size=16, color='grey')

    all_products = engine.load_inventory()
    current_cart_total = [0.0]

    grouped_products = {}

    def update_cart_math(e=None):
        total = sum(item['product'].price * item['qty']
                    for item in cart_state.values())
        total_lbl.value = f'Total: ₱{total:.2f}'

        try:
            cash = float(cash_input.value) if cash_input.value else 0.0
        except ValueError:
            cash = 0.0

        if cash == 0:
            change_lbl.value = 'Change: ₱0.00'
            change_lbl.color = 'grey'
        elif cash < total:
            change_lbl.value = f'Needed: ₱{(total-cash):.2f}'
            change_lbl.color = 'red'
        else:
            change_lbl.value = f'Change: ₱{(cash-total):.2f}'
            change_lbl.color = 'green'

        page.update()

    cash_input = ft.TextField(
        label='Cash Amount Tendered (₱)',
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=update_cart_math,
        border_radius=10,
        height=50
    )

    def refresh_cart_ui():
        cart_list.controls.clear()

        for key, item in cart_state.items():
            p = item['product']
            qty = item['qty']

            def create_qty_handler(k, delta, prod_stock):
                def handler(e):
                    new_qty = cart_state[k]['qty']+delta
                    if new_qty <= 0:
                        del cart_state[k]
                    elif new_qty <= prod_stock:
                        cart_state[k]['qty'] = new_qty
                    refresh_cart_ui()
                return handler

            row = ft.Container(
                bgcolor='white',
                padding=10,
                border_radius=8,
                content=ft.Row([
                    ft.Column([
                        ft.Text(p.name, weight='bold', size=14),
                        ft.Text(p.get_variant_label(), size=11, color='grey'),
                        ft.Text(f'₱{p.price:.2f}', size=12),
                    ], expand=True),
                    ft.IconButton(icon=ft.icons.REMOVE, icon_color='red',
                                  on_click=create_qty_handler(key, -1, p.stock)),
                    ft.Text(str(qty), weight='bold', size=16),
                    ft.IconButton(icon=ft.icons.ADD, icon_color='green',
                                  on_click=create_qty_handler(key, 1, p.stock)),
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
        key = f'{p.name} - {p.get_variant_label}'
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

        try:
            cash = float(cash_input.value) if cash_input.value else 0.0
        except ValueError:
            return

        if cash < total:
            return

        change = cash-total

        receipt_text = (
            "======= DAD'S STORE =======\n"
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "---------------------------\n"
        )

        for key, item in cart_state.items():
            p = item['product']
            qty = item['qty']
            sub = p.price * qty

            p.stock -= qty

            name_str = f'{p.name} ({p.get_variant_label()})'
            receipt_text += f'{name_str[:20]:<20} {qty} x ₱{sub:.2f}\n'

        receipt_text += (
            "---------------------------\n"
            f"Total:      ₱{total:.2f}\n"
            f"Cash:       ₱{cash:.2f}\n"
            f"Change:     ₱{change:.2f}\n"
            "===========================\n"
            "Thank you for shopping!"
        )

        engine.save_inventory(all_products)

        def close_receipt(e):
            page.close(receipt_dialog)
            cart_state.clear()
            cash_input.value = ''
            refresh_cart_ui

        receipt_dialog = ft.AlertDialog(
            title=ft.Text('Checkout Successful!',
                          weight='bold', color='green'),
            content=ft.Text(receipt_text, font_family='monospace'),
            actions=[ft.TextButton('Close & New Order',
                                   on_click=close_receipt)],
            modal=True
        )

        page.open(receipt_dialog)

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
                dialog.open = False
                page.update()

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

        page.overlay.clear()

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def create_category_card(name, variants):
        # Bare minimum logic
        preview_price = [v.price for v in variants]
        min_p = min(preview_price)
        max_p = max(preview_price)

        if min_p == max_p:
            price_text = f'₱{min_p:.2f}'
        else:
            price_text = f'₱{min_p:.2f} - ₱{max_p:.2f}'

        return ft.Container(
            bgcolor='white',  # Making it red so we KNOW the new code ran
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

    return ft.Row([
        ft.Column([
            ft.TextField(
                hint_text='Search products...',
                prefix_icon='search',
                border_radius=15,
                bgcolor='white'
            ),
            product_grid
        ], expand=2),
        ft.Container(
            content=ft.Column([
                ft.Text('Current Order', size=25, weight='bold'),
                ft.Divider(),
                ft.Container(content=cart_list, expand=True),
                ft.Divider(),
                total_lbl,
                cash_input,
                change_lbl,
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
