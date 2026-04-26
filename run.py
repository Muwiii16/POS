import os
import base64
import json
import flet as ft
from ui.pos_view import pos_view_content
from ui.inventory_view import inventory_view_content
from ui.report_view import reports_view_content


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
        if page.data and 'scanner' in page.data:
            page.data['scanner'].stop()

        index = e.control.selected_index
        if index == 0:
            main_content.content = pos_view_content(page)
        elif index == 1:
            main_content.content = inventory_view_content(page)
        elif index == 2:
            main_content.content = reports_view_content(page)

        page.update()

    rail = ft.NavigationRail(selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100, min_extended_width=200, bgcolor='#E8E2DE',
                             destinations=[ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label='Cashier (POS)'),
                                           ft.NavigationRailDestination(
                                 icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label='Inventory'),
                                 ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label='Reports')], on_change=on_nav_change)

    def open_scanner_settings(e):
        from core.scanner import get_available_cameras
        cameras = get_available_cameras()

        if not cameras:
            page.show_dialog(ft.AlertDialog(
                title=ft.Text('No cameras found'),
                content=ft.Text('No cameras were detected on this device.'),
                actions=[ft.TextButton(
                    'OK', on_click=lambda e: page.pop_dialog())]
            ))
            return

        def on_camera_selected(e):
            page.data = {'camera_index': int(e.control.data)}
            page.pop_dialog()
            main_content.content = pos_view_content(page)
            page.update()

        camera_buttons = [
            ft.TextButton(
                content=ft.Text(name),
                data=str(index),
                on_click=on_camera_selected
            )
            for index, name in cameras
        ]

        page.show_dialog(ft.AlertDialog(
            title=ft.Text('Select Camera', weight='bold'),
            content=ft.Column(
                controls=[
                    ft.Text('Detected cameras:', color='grey', size=12),
                    *camera_buttons
                ],
                tight=True, spacing=5
            ),
            actions=[ft.TextButton(
                'Cancel', on_click=lambda e: page.pop_dialog())],
            modal=True
        ))

    def open_qr_settings(e):
        qr_data_file = os.path.join('data', 'qr_codes.json')
        qr_data = {}

        if os.path.exists(qr_data_file):
            with open(qr_data_file, 'r') as f:
                qr_data = json.load(f)

        gcash_lbl = ft.Text(
            'GCash: ' + ('✅ Set' if 'gcash' in qr_data else '❌ Not set'),
            size=13
        )
        maya_lbl = ft.Text(
            'GCash: ' + ('✅ Set' if 'maya' in qr_data else '❌ Not set'),
            size=13
        )

        current_method = {'value': None}

        def on_file_picked(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            path = e.files[0].path
            method_key = current_method['value']
            label = gcash_lbl if method_key == 'gcash' else maya_lbl

            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode()

            qr_data[method_key] = encoded
            os.makedirs('data', exist_ok=True)
            with open(qr_data_file, 'w') as f:
                json.dump(qr_data_file, f)

            label.value = f'{method_key.capitalize()}: ✅ Set'
            label.update()

        file_picker = ft.FilePicker(on_result=on_file_picked)
        page.overlay.append(file_picker)
        page.update()

        def pick_qr(method_key):
            current_method['value'] = method_key
            file_picker.pick_files(
                allowed_extensions=['png', 'jpg', 'jpeg'],
                allow_multiple=False
            )
        page.show_dialog(ft.AlertDialog(
            title=ft.Text('QR Code Settings', weight='bold'),
            content=ft.Column([
                ft.Text('Upload QR codes for digital payments',
                        color='grey', size=12),
                ft.Divider(),
                ft.Row([
                    gcash_lbl,
                    ft.ElevatedButton(
                        'Upload GCash QR',
                        on_click=lambda e: pick_qr('gcash'),
                        style=ft.ButtonStyle(
                            bgcolor='#1565c0', color='white',
                            shape=ft.RoundedRectangleBorder(radius=8)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    maya_lbl,
                    ft.ElevatedButton(
                        'Upload Maya QR',
                        on_click=lambda e: pick_qr('maya'),
                        style=ft.ButtonStyle(
                            bgcolor='#00897b', color='white',
                            shape=ft.RoundedRectangleBorder(radius=8)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], tight=True, spacing=12, width=350),
            actions=[
                ft.TextButton(
                    content=ft.Text('Done'),
                    on_click=lambda e: page.pop_dialog()
                )
            ], modal=True
        ))

    page.appbar = ft.AppBar(
        title=ft.Text('POS System', weight='bold'),
        bgcolor='#E8E2DE',
        actions=[
            ft.TextButton(
                'QR Codes',
                icon=ft.Icons.QR_CODE,
                on_click=open_qr_settings,
                style=ft.ButtonStyle(color='#4A4440')
            ),
            ft.TextButton('Scanner', icon=ft.Icons.CAMERA_ALT_OUTLINED, on_click=open_scanner_settings, style=ft.ButtonStyle(color='#4A4440')
                          ),
        ]
    )

    main_content.content = pos_view_content(page)

    page.add(ft.Row([rail, ft.VerticalDivider(
        width=1, color='#D1C7BD'), main_content], expand=True))


if __name__ == '__main__':
    ft.run(main)
