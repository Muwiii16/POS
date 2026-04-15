

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
    )

    def add_item(p: Product):
        cart_list.controls.append(
            ft.ListTile(
                leading=ft.Icon('coffee'),
                title=ft.Text(p.name),
                subtitle=ft.Text(p.get_variant_label()),
                trailing=ft.Text(f'₱{p.price:.2f}')
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
        preview_price = variants[0].price

        return ft.Container(
            content=ft.Column([
                ft.Icon('inventory_2', size=50, color='#A4907C'),
                ft.Text(name, weight='bold', size=20,
                        text_align='center', color='black'),
                ft.Text(f'{len(variants)} Variants', color='grey',
                        size=14),
                ft.Text(f'₱{preview_price:.2f}', size=18,
                        color='#4A4440', weight='bold')
            ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),

            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            alignment=ft.Alignment(0, 0),
            on_click=lambda _: open_variant_selector(name),
            shadow=ft.BoxShadow(blur_radius=15, color='black12'),
        )

    cart_list = ft.ListView(expand=True, spacing=10)
    total_lbl = ft.Text('Total: ₱0.00', size=30, weight='bold')

    print(f'Creating {len(grouped_products)} category cards...')
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
                cart_items_container := ft.Container(content=cart_list, expand=True),
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
