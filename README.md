# 🏪 POS System

A modern, lightweight Point of Sale (POS) application built with Python and Flet. Designed for small retail stores with a clean, intuitive interface for fast transactions, inventory management, and revenue reporting.

---

## ✨ Features

### 🛒 Cashier (POS)
- **Product Search**: Quickly find products by name with fuzzy search support.
- **Barcode Scanner**: Scan barcodes via webcam using pyzbar for fast item lookup.
- **Live Cart Management**: Add, remove, and adjust item quantities in real time.
- **Multiple Payment Methods**: Supports Cash, GCash, and Maya payments.
- **Customer Display**: Launch a secondary display window for customers showing the current order and total.
- **Automatic Change Calculation**: Instantly computes change after payment.

### 📦 Inventory Management
- **Product & Variant Support**: Manage products with multiple variants (size, color, etc.).
- **Stock Tracking**: Monitor stock levels with low stock alerts.
- **Barcode Generation**: Auto-generate barcodes for products.
- **Add / Edit / Delete**: Full CRUD support for products and variants.

### 📊 Revenue Reports
- **Monthly & Quarterly Views**: Toggle between monthly and quarterly breakdowns.
- **Summary Cards**: At-a-glance Total Revenue, Total Cost, and Total Profit.
- **Bar Chart**: Visual Revenue vs. Profit chart that auto-scrolls to the latest period.
- **Persistent Sales Log**: All transactions are logged to `data/sales_log.csv`.

---

## 🛠️ Technical Setup

### Prerequisites
- Python 3.10 or higher (current dev environment: 3.14)
- pip

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/YourUsername/POS.git
    cd POS
    ```

2. **Install dependencies**:
    ```bash
    pip install -r Requirements.txt
    ```

3. **Run the app**:
    ```bash
    python run.py
    ```

---

## 📂 Project Structure

```
POS/
├── run.py                  # Entry point
├── core/
│   ├── engine.py           # Business logic, sales logging, inventory I/O
│   ├── scanner.py          # Webcam barcode scanning
│   ├── shared_state.py     # Shared cart state between windows
│   └── models.py           # Data models
├── ui/
│   ├── pos_view.py         # Cashier POS screen
│   ├── inventory_view.py   # Inventory management screen
│   ├── report_view.py      # Revenue report screen
│   └── customer_display.py # Secondary customer-facing display
├── data/
│   ├── inventory.json      # Product and stock data
│   ├── sales_log.csv       # Transaction history
│   ├── cart_state.json     # Shared cart state for customer display
│   ├── payment_ledger.json # Payment records
│   └── main_checkout.json  # Checkout session data
├── barcodes/               # Generated barcode images
├── qr_codes/               # QR code assets (e.g. GCash QR)
└── Requirements.txt
```

---

## 📦 Distribution

A Windows installer is available as a single `POS System Setup.exe`. End users do not need Python or any dependencies installed — everything is bundled.

### Building the Installer (for developers)

1. Build the executable:
    ```bash
    python -m PyInstaller --onedir --windowed --collect-all flet run.py
    ```

2. Copy the required zbar DLLs into `dist/POS/_internal/`:
    - `libiconv.dll`
    - `libzbar-64.dll`

    These can be found in your pyzbar package folder:
    ```
    %LOCALAPPDATA%\Python\pythoncore-3.14-64\Lib\site-packages\pyzbar\
    ```

3. Compile the installer using **Inno Setup 6** with the provided `POS.iss` script.

---

## 📝 Dependencies

| Package | Purpose |
|---|---|
| flet | UI framework |
| python-barcode | Barcode generation |
| pyzbar | Barcode scanning via webcam |
| opencv-python | Camera access |
| Pillow | Image processing |
| thefuzz | Fuzzy product search |
| python-Levenshtein | Fuzzy match performance |
| screeninfo | Multi-monitor support |
| pynput | Input handling |
| pyinstaller | Executable packaging |
