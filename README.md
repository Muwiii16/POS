# 🏪 Store POS System

A modern, lightweight Point of Sale (POS) application built with Python and CustomTkinter. Designed for quick retail transactions with a focus on a clean, high-contrast interface.

## ✨ Features
* **Dynamic Product Catalog**: Browse products using a responsive card-based layout.
* **Variant Selection**: Support for multiple product versions (e.g., different sizes or weights) within a single category.
* **Live Cart Management**:
    * **Grouped Items**: Clean view that totals quantities for identical products.
    * **Real-time Subtotals**: Each row displays the calculated price for that specific quantity.
    * **Quick Adjust**: Add or remove items directly from the sidebar with one click.
* **Financial Accuracy**: Automatic calculation of grand totals and customer change.


### 📦 Inventory Management
* **Responsive Table Layout**: A fully fluid inventory dashboard that adapts to window resizing and full-screen modes.
* **Intelligent Grouping**: Automatically groups individual stock items by their base product name to reduce clutter.
* **Price Spectrum**: Displays the price range (Min-Max) for products with multiple variants (e.g., `₱460.00 - ₱740.00`).
* **Smart Truncation**: Dynamically calculates available space and truncates long variant lists with an ellipsis (`...`) to prevent UI overflow.
* **Low Stock Alerts**: Visual warnings (red text) when total stock levels for a product or variant drop below 6 units.

## 🛠️ Technical Setup

### Prerequisites
* Python 3.10 or higher (Current dev environment: 3.14).
* `customtkinter` library for the modern UI.

### Responsive Implementation
The application uses a "Bulletproof" width calculation method to ensure the inventory table remains perfectly aligned across all monitor sizes:

```python
# Proportional stretching logic used in core/gui.py
total_w = self.inventory_scroll.winfo_width() - 40
w_name = int(total_w * 0.20)    # 20% width
w_vars = int(total_w * 0.40)    # 40% width
w_price = int(total_w * 0.15)   # 15% width
w_stock = int(total_w * 0.10)   # 10% width

### Installation
1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/YourUsername/POS.git](https://github.com/YourUsername/POS.git)
    ```
2.  **Install dependencies**:
    ```bash
    pip install customtkinter
    ```
3.  **Run the app**:
    ```bash
    python run.py
    ```

## 📂 Project Structure
* `run.py`: Entry point that initializes the `POSapp`.
* `core/gui.py`: The main UI logic, grid configurations, and event handling.
* `core/engine.py`: The "brain" of the app; handles math, checkout logic, and file I/O.
* `inventory.json`: JSON data store for products and stock levels.
* `sales_log.csv`: Persistent log for all completed transactions.

## 📝 Recent UI Improvements
* **Inventory Stretching**: Implemented percentage-based pixel widths to allow the inventory table to fill the screen in maximized mode.
* **Unified Alignment**: Replaced standard grid weights with a strict pack(`side='left'`) architecture for the inventory rows to ensure perfect vertical alignment.
* **Cart Optimization**: Implemented `grid_propagate(False)` and `minsize=450` to prevent the cart sidebar from shrinking during window adjustments.
* **Undo/Redo System**Added dedicated controls to manage and revert inventory changes safely.
---
