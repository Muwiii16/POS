import math
import flet as ft
from core import engine


def generate_colors(n):
    colors = []
    golden_ratio = 0.618033988749895
    hue = 0.0
    for _ in range(n):
        hue = (hue + golden_ratio) % 1.0
        h = hue * 6
        c = (1 - abs(2 * 0.55 - 1)) * 0.65
        x = c * (1 - abs(h % 2 - 1))

        if h < 1:
            r, g, b = c, x, 0
        elif h < 2:
            r, g, b = x, c, 0
        elif h < 3:
            r, g, b = 0, c, x
        elif h < 4:
            r, g, b = 0, x, c
        elif h < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        m = 0.55 - c / 2
        r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
        colors.append(f'#{r:02x}{g:02x}{b:02x}')
    return colors


def reports_view_content(page: ft.Page):
    content_area = ft.Column(expand=True)

    def make_pie_chart(data: dict, size=220):
        if not data:
            return ft.Container(
                width=size, height=size,
                content=ft.Text('No data', color='grey'),
                alignment=ft.Alignment(0, 0)
            )

        colors = generate_colors(len(data))
        total = sum(data.values())
        cx = cy = size / 2
        r = size / 2 - 10
        paths = []
        angle = -math.pi / 2

        for i, (label, val) in enumerate(data.items()):
            sweep = (val / total) * 2 * math.pi
            x1 = cx + r * math.cos(angle)
            y1 = cy + r * math.sin(angle)
            x2 = cx + r * math.cos(angle + sweep)
            y2 = cy + r * math.sin(angle + sweep)
            large = 1 if sweep > math.pi else 0
            color = colors[i % len(colors)]

            path = (
                f'<path d="M {cx},{cy} L {x1:.2f},{y1:.2f} '
                f'A {r},{r} 0 {large},1 {x2:.2f},{y2:.2f} Z" '
                f'fill="{color}" stroke="white" stroke-width="2"/>'
            )
            paths.append(path)
            angle += sweep

        svg = (
            f'<svg width="{size}" height="{size}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            + ''.join(paths) +
            '</svg>'
        )
        return ft.Image(src=f'data:image/svg+xml,{svg}',
                        width=size, height=size, fit='contain')

    def make_legend(data: dict):
        colors = generate_colors(len(data))
        total = sum(data.values())
        items = []
        for i, (label, val) in enumerate(data.items()):
            pct = val / total * 100
            color = colors[i % len(colors)]
            items.append(
                ft.Row([
                    ft.Container(width=14, height=14,
                                 bgcolor=color, border_radius=3),
                    ft.Text(f'{label}', size=12, expand=True),
                    ft.Text(f'{val} ({pct:.1f}%)', size=12, color='grey')
                ], spacing=8)
            )
        return ft.Column(items, spacing=6)

    def show_eod_report():
        report = engine.get_daily_summary()
        avg = (report['revenue'] / report['transactions']
               if report['transactions'] > 0 else 0)

        def go_back(e):
            show_home()

        def stat_card(title, value, color):
            return ft.Container(
                expand=True,
                bgcolor=color,
                border_radius=15,
                padding=20,
                content=ft.Column([
                    ft.Text(title, color='white', size=13),
                    ft.Text(value, color='white', size=28, weight='bold'),
                ], spacing=4)
            )

        stats_row = ft.Row([
            stat_card('Total Revenue', f'₱{report["revenue"]:.2f}', '#27ae60'),
            stat_card('Transactions', str(report['transactions']), '#2980b9'),
            stat_card('Avg per Sale', f'₱{avg:.2f}', '#8e44ad'),
        ], spacing=16)

        sorted_sales = sorted(
            report['category_sales'].items(),
            key=lambda x: x[1], reverse=True
        ) if report['category_sales'] else []

        top_items = ft.Column([
            ft.Text('Top Selling Items', weight='bold', size=16),
            ft.ListView(
                controls=[
                    ft.Container(
                        bgcolor='white',
                        border_radius=10,
                        padding=ft.padding.symmetric(
                            horizontal=16, vertical=10),
                        shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                        content=ft.Row([
                            ft.Text(f'#{i+1}', weight='bold',
                                    color='#2980b9', width=30),
                            ft.Text(name, expand=True),
                            ft.Text(f'{count} sold', color='grey', italic=True)
                        ])
                    )
                    for i, (name, count) in enumerate(sorted_sales)
                ] if sorted_sales else [
                    ft.Text('No sales recorded today.', color='grey')
                ],
                spacing=8,
                expand=True
            )
        ], expand=True, spacing=8)

        chart_section = ft.Column([
            ft.Text('Sales Distribution', weight='bold', size=16),
            ft.Container(height=8),
            ft.Row([
                make_pie_chart(report['category_sales']),
                ft.Container(width=20),
                ft.Container(
                    content=make_legend(report['category_sales']),
                    expand=True
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            if report['category_sales'] else
            ft.Text('No chart data available.', color='grey')
        ], spacing=8)

        content_area.controls = [
            ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=16),
                            ft.Text('Back')
                        ]),
                        on_click=go_back
                    ),
                    ft.Text(f'End of Day Report — {report["date"]}',
                            size=20, weight='bold', expand=True),
                ]),
                ft.Divider(),
                stats_row,
                ft.Container(height=8),
                ft.Row([
                    ft.Container(content=top_items, expand=1),
                    ft.Container(width=20),
                    ft.Container(content=chart_section, expand=2),
                ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            ], expand=True, spacing=12)
        ]
        page.update()

    def show_payment_ledger():
        entries = engine.load_payment_ledger()

        def go_back(e):
            show_home()

        summary = {}
        for entry in entries:
            m = entry.get('method', 'Unknown')
            summary[m] = summary.get(m, 0)+entry.get('amount', 0)

        summary_cards = ft.Row([
            ft.Container(
                expand=True, bgcolor=color, border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text(method, color='white', size=12),
                    ft.Text(f'₱{total:.2f}', color='white',
                            size=22, weight='bold')
                ], spacing=4)
            )
            for method, total, color in [
                ('Cash', summary.get('Cash', 0), '#27ae60'),
                ('GCash', summary.get('GCash', 0), '#1565c0'),
                ('Maya', summary.get('Maya', 0), '#00897b'),
                ('Credit', summary.get('Credit', 0), '#e67e22'),
            ]
        ], spacing=12)

        rows = [
            ft.Container(
                bgcolor='#e0e0e0', border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                content=ft.Row([
                        ft.Text('Date/Time', weight='bold', width=160),
                        ft.Text('Method', weight='bold', width=80),
                        ft.Text('Amount', weight='bold', expand=True),
                ])
            )
        ] + ([
            ft.Container(
                bgcolor='white', border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                content=ft.Row([
                    ft.Text(e.get('timestamp', ''),
                            width=160, size=12),
                    ft.Text(e.get('method', ''), width=80,
                            color='#2980b9', weight='bold'),
                    ft.Text(f'₱{e.get("amount", 0):.2f}', expand=True),
                ])
            )
            for e in reversed(entries)
        ] if entries else [ft.Text('No payment entries yet.', color='grey')])

        content_area.controls = [
            ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16),
                                        ft.Text('Back')]),
                        on_click=go_back
                    ),
                    ft.Text('Payment Ledger', size=20,
                            weight='bold', expand=True),
                ]),
                ft.Divider(),
                summary_cards,
                ft.Container(height=8),
                ft.ListView(controls=rows, spacing=6, expand=True),
            ], expand=True, spacing=12)
        ]
        page.update()

    def show_credit_ledger():
        entries = engine.load_credit_ledger()

        def go_back(e):
            show_home()

        def mark_paid(entry_id):
            engine.mark_credit_paid(entry_id)
            show_credit_ledger()

        unpaid = [e for e in entries if not e.get('paid')]
        paid = [e for e in entries if e.get('paid')]
        total_owed = sum(e.get('amount_owed', 0) for e in unpaid)

        summary_cards = ft.Row([
            ft.Container(
                expand=True, bgcolor='#e74c3c', border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text('Total Outstanding', color='white', size=12),
                    ft.Text(f'₱{total_owed:.2f}', color='white',
                            size=22, weight='bold')
                ], spacing=4)
            ),
            ft.Container(
                expand=True, bgcolor='#27ae60', border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text('Paid Credits', color='white', size=12),
                    ft.Text(str(len(paid)), color='white',
                            size=22, weight='bold')
                ], spacing=4)
            ),
            ft.Container(
                expand=True, bgcolor='#e67e22', border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text('Unpaid Credits', color='white', size=12),
                    ft.Text(str(len(unpaid)), color='white',
                            size=22, weight='bold')
                ], spacing=4)
            ),
        ], spacing=12)

        def build_row(e):
            is_paid = e.get('paid', False)
            return ft.Container(
                bgcolor='white', border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                content=ft.Row([
                    ft.Column([
                        ft.Text(e.get('customer', ''),
                                weight='bold', size=13),
                        ft.Text(f'Due: {e.get("due_date", "")}',
                                size=11, color='grey'),
                        ft.Text(e.get('timestamp', ''),
                                size=10, color='grey'),
                    ], expand=True),
                    ft.Column([
                        ft.Text(f'₱{e.get("amount_owed", 0):.2f}',
                                weight='bold', size=14,
                                color='#27ae60' if is_paid else '#e74c3c'),
                        ft.Text('PAID' if is_paid else 'UNPAID',
                                size=11,
                                color='#27ae60' if is_paid else '#e74c3c',
                                weight='bold'),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END),
                    ft.ElevatedButton(
                        'Mark Paid',
                        visible=not is_paid,
                        on_click=lambda ev, eid=e['id']: mark_paid(eid),
                        style=ft.ButtonStyle(
                            bgcolor='#27ae60', color='white',
                            shape=ft.RoundedRectangleBorder(radius=8))
                    ) if not is_paid else ft.Container(width=0)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        rows = [build_row(e) for e in reversed(entries)] if entries else [
            ft.Text('No credit entries yet.', color='grey')
        ]

        content_area.controls = [
            ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16),
                                        ft.Text('Back')]),
                        on_click=go_back
                    ),
                    ft.Text('Credit Ledger', size=20,
                            weight='bold', expand=True),
                ]),
                ft.Divider(),
                summary_cards,
                ft.Container(height=8),
                ft.ListView(controls=rows, spacing=6, expand=True),
            ], expand=True, spacing=12)
        ]
        page.update()

    def show_expenses_ledger():
        entries = engine.load_expenses_ledger()

        def go_back(e):
            show_home()

        def add_expense(e):
            cat_field = ft.Dropdown(
                label='Category',
                options=[
                    ft.dropdown.Option('Overhead'),
                    ft.dropdown.Option('Restock'),
                    ft.dropdown.Option('Other'),
                ],
                border_radius=8,
                value='Overhead'
            )
            amount_field = ft.TextField(
                label='Amount (₱)',
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=8,
                autofocus=True
            )
            desc_field = ft.TextField(
                label='Description',
                border_radius=8
            )

            def save(e):
                try:
                    amt = float(amount_field.value or 0)
                    if amt <= 0:
                        amount_field.error_text = 'Enter a valid amount'
                        amount_field.update()
                        return
                    engine.save_expense_entry(
                        category=cat_field.value,
                        amount=amt,
                        description=desc_field.value.strip()
                    )
                    page.pop_dialog()
                    show_expenses_ledger()
                except ValueError:
                    amount_field.error_text = 'Must be a number'
                    amount_field.update()

            page.show_dialog(ft.AlertDialog(
                title=ft.Text('Add Expense', weight='bold'),
                content=ft.Column([cat_field, amount_field, desc_field],
                                  spacing=12, tight=True, width=350),
                actions=[
                    ft.TextButton(content=ft.Text('Cancel'),
                                  on_click=lambda e: page.pop_dialog()),
                    ft.ElevatedButton(
                        content=ft.Text('Save'),
                        on_click=save,
                        style=ft.ButtonStyle(bgcolor='#e67e22', color='white')
                    )
                ],
                modal=True
            ))

        total_expenses = sum(e.get('amount', 0) for e in entries)
        by_category = {}
        for e in entries:
            cat = e.get('category', 'Other')
            by_category[cat] = by_category.get(cat, 0) + e.get('amount', 0)

        summary_cards = ft.Row([
            ft.Container(
                expand=True, bgcolor='#e67e22', border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text('Total Expenses', color='white', size=12),
                    ft.Text(f'₱{total_expenses:.2f}', color='white',
                            size=22, weight='bold')
                ], spacing=4)
            ),
        ] + [
            ft.Container(
                expand=True, bgcolor='#34495e', border_radius=12, padding=16,
                content=ft.Column([
                    ft.Text(cat, color='white', size=12),
                    ft.Text(f'₱{amt:.2f}', color='white',
                            size=22, weight='bold')
                ], spacing=4)
            )
            for cat, amt in by_category.items()
        ], spacing=12)

        rows = [
            ft.Container(
                bgcolor='#e0e0e0', border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                content=ft.Row([
                    ft.Text('Date/Time', weight='bold', width=160),
                    ft.Text('Category', weight='bold', width=100),
                    ft.Text('Description', weight='bold', expand=True),
                    ft.Text('Amount', weight='bold', width=100),
                ])
            )
        ] + ([
            ft.Container(
                bgcolor='white', border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                shadow=ft.BoxShadow(blur_radius=4, color='black12'),
                content=ft.Row([
                    ft.Text(e.get('timestamp', ''), width=160, size=12),
                    ft.Text(e.get('category', ''), width=100,
                            color='#e67e22', weight='bold'),
                    ft.Text(e.get('description', ''), expand=True),
                    ft.Text(f'₱{e.get("amount", 0):.2f}', width=100,
                            weight='bold'),
                ])
            )
            for e in reversed(entries)
        ] if entries else [ft.Text('No expense entries yet.', color='grey')])

        content_area.controls = [
            ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16),
                                        ft.Text('Back')]),
                        on_click=go_back
                    ),
                    ft.Text('Expenses Ledger', size=20,
                            weight='bold', expand=True),
                    ft.ElevatedButton(
                        '+ Add Expense',
                        on_click=add_expense,
                        style=ft.ButtonStyle(
                            bgcolor='#e67e22', color='white',
                            shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ]),
                ft.Divider(),
                summary_cards,
                ft.Container(height=8),
                ft.ListView(controls=rows, spacing=6, expand=True),
            ], expand=True, spacing=12)
        ]
        page.update()

    def show_home():
        def report_card(title, subtitle, icon, color, on_click):
            return ft.Container(
                width=200,
                height=160,
                bgcolor='white',
                border_radius=20,
                padding=24,
                shadow=ft.BoxShadow(blur_radius=12, color='black12'),
                on_click=on_click,
                content=ft.Column([
                    ft.Container(
                        bgcolor=color,
                        border_radius=12,
                        padding=10,
                        width=44, height=44,
                        content=ft.Icon(icon, color='white', size=22),
                    ),
                    ft.Container(height=10),
                    ft.Text(title, weight='bold', size=15),
                    ft.Text(subtitle, color='grey', size=11),
                ], spacing=2)
            )

        cards = ft.Row([
            report_card('End of Day', 'Daily summary & sales',
                        ft.Icons.TODAY, '#27ae60',
                        lambda e: show_eod_report()),
            report_card('Payment Ledger', 'GCash, Maya, Cash, Credit',
                        ft.Icons.PAYMENTS, '#2980b9',
                        lambda e: show_payment_ledger()),
            report_card('Credit Ledger', 'Customers who owe',
                        ft.Icons.CREDIT_CARD, '#8e44ad',
                        lambda e: show_credit_ledger()),
            report_card('Expenses', 'Overhead & restocking',
                        ft.Icons.RECEIPT_LONG, '#e67e22',
                        lambda e: show_expenses_ledger()),
        ], wrap=True, spacing=20, run_spacing=20)

        content_area.controls = [
            ft.Column([
                ft.Text('Reports', size=25, weight='bold'),
                ft.Text('Select a report to view', color='grey', size=13),
                ft.Container(height=10),
                cards,
            ], expand=True, spacing=8)
        ]
        page.update()

    show_home()
    return ft.Container(content=content_area, expand=True)
