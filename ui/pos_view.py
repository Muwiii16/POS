

import flet as ft
from core import engine
from core.models import Product


def pos_view_content(page: ft.Page):
    all_products = engine.load_inventory()

    grouped_products = {}

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

    def add_item(p: Product):
        cart_list.controls.append(
            ft.ListTile(
                leading=ft.Icon('coffee', color='#4A4440'),
                title=ft.Text(p.name, weight='bold'),
                subtitle=ft.Text(p.get_variant_label()),
                trailing=ft.Text(f'₱{p.price:.2f}', weight='bold')
            )
        )
        page.update()

    def open_variant_selector(product_name):
        variants = grouped_products[product_name]

        variant_options = ft.Column(spacing=10, tight=True)

        for v in variants:
            variant_options.controls.append(
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Text(v.get_variant_label(), weight='bold'),
                        ft.Text(f'₱{v.price:.2f}', color='grey')
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    on_click=lambda _, item=v: add_to_cart_and_close(item),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10))
                )
            )

        def add_to_cart_and_close(item):
            add_item(item)
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f'Select Variant: {product_name}'),
            content=variant_options,
        )
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
                ft.ElevatedButton(
                    'CHECKOUT',
                    height=50,
                    width=float('inf'),
                    bgcolor='#4A4440',
                    color='white',
                )
            ]),
            expand=1,
            bgcolor='#E8E2DE',
            padding=20,
            border_radius=20
        )
    ], expand=True)
