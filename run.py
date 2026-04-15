import flet as ft
from ui.pos_view import pos_view_content
from ui.inventory_view import inventory_view_content


def main(page: ft.Page):
    page.title = 'POS System'
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.bgcolor = '#F8F4F1'
    page.padding = 0
    page.spacing = 0

    main_content = ft.Container(expand=True, padding=20)

    def on_nav_change(e):
        index = e.control.selected_index
        if index == 0:
            main_content.content = pos_view_content(page)
        elif index == 1:
            main_content.content = inventory_view_content(page)

        page.update()

    rail = ft.NavigationRail(selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100, min_extended_width=200, bgcolor='#E8E2DE', destinations=[ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label='Cashier (POS)'), ft.NavigationRailDestination(
        icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label='Inventory'), ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label='Reports')], on_change=on_nav_change)

    main_content.content = pos_view_content(page)

    page.add(ft.Row([rail, ft.VerticalDivider(
        width=1, color='#D1C7BD'), main_content], expand=True))


if __name__ == '__main__':
    ft.run(main)
