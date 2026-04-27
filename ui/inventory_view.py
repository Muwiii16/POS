import flet as ft
import base64
import os
from core import engine


def inventory_view_content(page: ft.Page):
    all_products = engine.load_inventory()

    current_view = {'mode': 'all', 'filter_name': None}

    alert_banner = ft.Container(visible=False)
    product_list = ft.ListView(expand=True, spacing=6, padding=10)

    def compute_total(items):
        return sum(item['product'].price*item['qty'] for item in items.values()) if isinstance(items, dict) else 0

    def build_alert_banner():
        low = [p for p in all_products if p.stock <= 5]
        out = [p for p in low if p.stock == 0]

        if not low:
            alert_banner.visible = False
            alert_banner.content = None

        else:
            msg = f'⚠️ {len(low)} items low on stock'
            if out:
                msg += f' ({len(out)} completely out!)'
            color = '#c0392b' if out else '#e67e22'

            alert_banner.visible = True
            alert_banner.bgcolor = color
            alert_banner.border_radius = 10
            alert_banner.padding = 12
            alert_banner.content = ft.Row([
                ft.Text(msg, color='white', weight='bold', expand=True),
                ft.TextButton(
                    content=ft.Text('Show only low stock', color='white'),
                    on_click=lambda e: show_low_stock()
                )
            ])

    def refresh_table(products_override=None):
        product_list.controls.clear()

        source = products_override if products_override is not None else all_products

        grouped = {}
        for p in source:
            grouped.setdefault(p.name, []).append(p)

        product_list.controls.append(
            ft.Container(
                bgcolor='#e0e0e0',
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                content=ft.Row([
                    ft.Text('Name', weight='bold', expand=3),
                    ft.Text('Variants', weight='bold', expand=3, color='grey'),
                    ft.Text('Price', weight='bold',
                            expand=2, text_align='center'),
                    ft.Text('Stock', weight='bold',
                            expand=1, text_align='center'),
                    ft.Container(width=90),
                ])
            )
        )

        if not grouped:
            product_list.controls.append(
                ft.Container(
                    padding=30,
                    content=ft.Text('No products found.',
                                    color='grey', text_align='center'),
                    alignment=ft.Alignment.CENTER
                )
            )

        for name, items in grouped.items():
            prices = [p.price for p in items]
            price_text = f'₱{min(prices):.2f}' if len(
                set(prices)) == 1 else f'₱{min(prices):.2f} - ₱{max(prices):.2f}'

            total_stock = sum(p.stock for p in items)
            if total_stock == 0:
                stock_color = '#e74c3c'
                stock_text = 'OUT'
            elif total_stock <= 5:
                stock_color = '#e67e22'
                stock_text = str(total_stock)
            else:
                stock_color = '#27ae60'
                stock_text = str(total_stock)

            variant_str = ', '.join([p.get_variant_label() for p in items])
            if len(variant_str) > 45:
                variant_str = variant_str[:42]+'...'

            row = ft.Container(
                bgcolor='white',
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                content=ft.Row([
                    ft.Text(name, weight='bold', expand=3),
                    ft.Text(variant_str, expand=3, color='grey', size=12),
                    ft.Text(price_text, expand=2, text_align='center'),
                    ft.Text(stock_text, expand=1, text_align='center',
                            weight='bold', color=stock_color),
                    ft.OutlinedButton(
                        content=ft.Text('Manage', no_wrap=True, size=12),
                        width=100,
                        on_click=lambda e, n=name: open_manage_view(n),
                        style=ft.ButtonStyle(bgcolor='#34495e', color='white', shape=ft.RoundedRectangleBorder(
                            radius=8), padding=ft.padding.symmetric(horizontal=8))
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

            product_list.controls.append(row)

        build_alert_banner()
        page.update()

    def view_barcode(product):
        barcode_path = f'barcodes/barcode_{product.barcode}.png'

        if not os.path.exists(barcode_path):
            barcode_path = engine.generate_product_barcode(product.barcode)

        show_barcode_popup(barcode_path, product.barcode)

    def open_manage_view(product_name):
        current_view['mode'] = 'manage'
        current_view['filter_name'] = product_name
        product_list.controls.clear()

        variants = [p for p in all_products if p.name == product_name]
        variants.sort(key=lambda p: p.get_variant_label())

        product_list.controls.append(
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ARROW_BACK, size=16),
                    ft.Text('Back to All Products')
                ]),
                on_click=lambda e: refresh_table()
            )
        )

        product_list.controls.append(
            ft.Container(
                bgcolor='#e0e0e0',
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                content=ft.Row([
                    ft.Text('Variant', weight='bold', width=350),
                    ft.Text('Price', weight='bold',
                            width=120, text_align='center'),
                    ft.Text('Stock', weight='bold',
                            width=80, text_align='center'),
                    ft.Container(expand=True),
                ])
            )
        )

        for p in variants:
            stock_color = '#e74c3c' if p.stock == 0 else '#e67e22' if p.stock <= 5 else '#27ae60'

            row = ft.Container(
                bgcolor='white',
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                content=ft.Row([
                    ft.Text(p.get_variant_label(), width=350),
                    ft.Text(f'₱{p.price:.2f}', width=120, text_align='center'),
                    ft.Text(str(p.stock), width=80, text_align='center',
                            weight='bold', color=stock_color),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.ElevatedButton(
                            'Barcode',
                            on_click=lambda e, prod=p: view_barcode(prod),
                            style=ft.ButtonStyle(
                                bgcolor='#8e44ad',
                                color='white',
                                shape=ft.RoundedRectangleBorder(radius=8)
                            )
                        ),
                        ft.ElevatedButton(
                            'Restock',
                            on_click=lambda e, prod=p: open_restock_dialog(
                                prod),
                            style=ft.ButtonStyle(
                                bgcolor='#27ae60', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.ElevatedButton(
                            'Edit',
                            on_click=lambda e, prod=p: open_edit_dialog(prod),
                            style=ft.ButtonStyle(
                                bgcolor='#2980b9', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.ElevatedButton(
                            'Delete',
                            on_click=lambda e, prod=p: confirm_delete(prod),
                            style=ft.ButtonStyle(
                                bgcolor='#2980b9', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                    ], spacing=6, tight=True)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

            product_list.controls.append(row)

        page.update()

    def open_restock_dialog(product):
        qty_field = ft.TextField(
            label='Quantity to add',
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            autofocus=True,
        )

        def confirm_restock(e):
            try:
                qty = int(qty_field.value or 0)
                if qty <= 0:
                    return
                engine.history.save_state(all_products)
                product.stock += qty
                engine.save_inventory(all_products)
                page.pop_dialog()
                open_manage_view(product.name)
            except ValueError:
                qty_field.error_text = 'Enter a valid number'
                qty_field.update()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(
                f'Restock: {product.get_variant_label()}', weight='bold'),
            content=qty_field,
            actions=[
                ft.TextButton(content=ft.Text('Cancel'),
                              on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton(
                    content=ft.Text('Confirm'),
                    on_click=confirm_restock,
                    style=ft.ButtonStyle(bgcolor='#27ae60', color='white')
                )
            ], modal=True
        ))

    def open_edit_dialog(product):
        name_field = ft.TextField(
            label='Name', value=product.name, border_radius=10)
        cost_field = ft.TextField(label='Cost per Unit (₱)', value=str(
            product.cost), keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        price_field = ft.TextField(label='Price (₱)', value=str(
            product.price), keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        stock_add_field = ft.TextField(label='Add to stock (leave blank for no change)',
                                       keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, hint_text='0')

        def save(e):
            try:
                engine.history.save_state(all_products)
                product.name = name_field.value.strip().title()
                product.cost = float(cost_field.value or 0)
                product.price = float(price_field.value)
                raw = stock_add_field.value.strip()
                if raw:
                    product.stock += int(raw)

                engine.save_inventory(all_products)
                page.pop_dialog()
                open_manage_view(product.name)
            except ValueError:
                price_field.error_text = 'Invalid value'
                price_field.update()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Edit Product', weight='bold'),
            content=ft.Column(
                [name_field, price_field, stock_add_field], spacing=12, tight=True, width=350),
            actions=[
                ft.TextButton(content=ft.Text('Cancel'),
                              on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton(
                    content=ft.Text('Save Changes'),
                    on_click=save,
                    style=ft.ButtonStyle(bgcolor='#2980b9', color='white')
                )
            ], modal=True
        ))

    def confirm_delete(product):
        def do_delete(e):
            engine.history.save_state(all_products)
            engine.delete_product(product, all_products)
            page.pop_dialog()
            refresh_table()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Delete Product?', weight='bold', color='#e74c3c'),
            content=ft.Text(
                f'Are you sure you want to delete "{product.name} - {product.get_variant_label()}"? This cannot be undone.'),
            actions=[
                ft.TextButton(content=ft.Text('Cancel'),
                              on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton(
                    content=ft.Text('Delete'),
                    on_click=do_delete,
                    style=ft.ButtonStyle(bgcolor='#e74c3c', color='white')
                )
            ], modal=True
        ))

    def handle_undo(e):
        prev = engine.history.undo(all_products)
        if prev:
            all_products.clear()
            all_products.extend(prev)
            engine.save_inventory(all_products)
            refresh_table()

    def handle_redo(e):
        nxt = engine.history.redo(all_products)
        if nxt:
            all_products.clear()
            all_products.extend(nxt)
            engine.save_inventory(all_products)
            refresh_table()

    def show_low_stock():
        refresh_table([p for p in all_products if p.stock <= 5])

    def open_add_product_dialog(e):
        name_f = ft.TextField(label='Product Name',
                              border_radius=10, autofocus=True)
        cost_f = ft.TextField(label='Cost per Unit (₱)',
                              keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        price_f = ft.TextField(
            label='Price (₱)', keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        stock_f = ft.TextField(
            label='Initial Stock', keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        category_f = ft.TextField(label='Category', border_radius=10)

        meta_fields = []
        meta_column = ft.Column(spacing=8)

        def add_meta_row(e=None):
            key_f = ft.TextField(hint_text='Field (e.g. Size)',
                                 expand=True, border_radius=8)
            val_f = ft.TextField(
                hint_text='Value (e.g. Large)', expand=True, border_radius=8)

            def remove_row(e, row_ref):
                meta_column.controls.remove(row_ref)
                meta_fields.remove((key_f, val_f))
                meta_column.update()

            row = ft.Row([key_f, val_f])
            row.controls.append(
                ft.IconButton(ft.Icons.REMOVE_CIRCLE, icon_color='red',
                              on_click=lambda e: remove_row(e, row))
            )
            meta_fields.append((key_f, val_f))
            meta_column.controls.append(row)
            meta_column.update()

        def submit(e):
            if not name_f.value.strip():
                name_f.error_text = 'Required'
                name_f.update()
                return
            try:
                data = {
                    'name': name_f.value.strip(),
                    'cost': float(cost_f.value or 0),
                    'price': float(price_f.value),
                    'stock': int(stock_f.value),
                    'category': category_f.value.strip()
                }
                for kf, vf in meta_fields:
                    k = kf.value.strip().lower()
                    v = vf.value.strip()
                    if k and v:
                        data[k] = v
                success, result = engine.add_new_product(data, all_products)

                if success:
                    barcode_id = result
                    barcode_path = engine.generate_product_barcode(barcode_id)
                    page.pop_dialog()
                    refresh_table()
                    show_barcode_popup(barcode_path, barcode_id)
                else:
                    name_f.error_text = result
                    name_f.update()

            except ValueError:
                price_f.error_text = 'Must be a number'
                price_f.update()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Add New Product', weight='bold'),
            content=ft.Container(
                width=420,
                content=ft.Column([
                    name_f, cost_f, price_f, stock_f, category_f,
                    ft.Divider(),
                    ft.Text('Extra Details (Variants)',
                            weight='bold', size=13),
                    meta_column,
                    ft.TextButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.ADD), ft.Text('Add Detail')]),
                        on_click=add_meta_row
                    )
                ], spacing=12, scroll=ft.ScrollMode.AUTO, tight=True)
            ),
            actions=[
                ft.TextButton(content=ft.Text('Cancel'),
                              on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton(
                    content=ft.Text('Save Product'),
                    on_click=submit,
                    style=ft.ButtonStyle(bgcolor='#27ae60', color='white')
                )
            ], modal=True
        ))

    def show_barcode_popup(image_path, barcode_id):
        with open(image_path, 'rb')as f:
            img_data = base64.b64encode(f.read()).decode()

        def print_barcode(e):
            try:
                os.startfile(os.path.abspath(image_path), 'print')
            except Exception as ex:
                print(f'Print Error: {ex}')

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Barcode Generated!',
                          weight='bold', color='#27ae60'),
            content=ft.Column([
                ft.Image(src=f'data:image/png;base64,{img_data}', width=350,
                         height=150,  fit='contain'),
                ft.Text(
                    f'Barcode ID: {barcode_id}', font_family='monospace', text_align='center', size=14)
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.ElevatedButton(
                    '🖨️ Print Barcode',
                    on_click=print_barcode,
                    style=ft.ButtonStyle(
                        bgcolor='#2980b9', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.TextButton(content=ft.Text('Close'),
                              on_click=lambda e: page.pop_dialog())
            ], modal=True
        ))

    def on_search_change(e):
        query = e.control.value.strip()
        if not query:
            refresh_table()
        else:
            results = engine.search_products(query, all_products)
            refresh_table(results)

    search_field = ft.TextField(
        hint_text='Search inventory by name...',
        prefix_icon=ft.Icons.SEARCH,
        border_radius=15,
        bgcolor='white',
        on_change=on_search_change
    )

    refresh_table()

    return ft.Column([
        ft.Row([
            ft.Text('Inventory Management', size=25,
                    weight='bold', expand=True),
            ft.Row([
                ft.ElevatedButton(
                    '↩ Undo',
                    on_click=handle_undo,
                    style=ft.ButtonStyle(
                        bgcolor='#7f8c8d', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.ElevatedButton(
                    '↪ Redo',
                    on_click=handle_redo,
                    style=ft.ButtonStyle(
                        bgcolor='#7f8c8d', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.ElevatedButton(
                    '+ Add Product',
                    on_click=open_add_product_dialog,
                    style=ft.ButtonStyle(
                        bgcolor='#27ae60', color='white', shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ], spacing=8)
        ]),
        search_field,
        alert_banner,
        ft.Container(content=product_list, expand=True)
    ], expand=True, spacing=12)
