# 🏪 Dad's Store POS System

A modern, lightweight Point of Sale (POS) application built with Python and CustomTkinter. Designed for quick retail transactions with a focus on a clean, high-contrast interface.

## ✨ Features
* **Dynamic Product Catalog**: Browse products using a responsive card-based layout.
* **Variant Selection**: Support for multiple product versions (e.g., different sizes or weights) within a single category.
* **Live Cart Management**:
    * **Grouped Items**: Clean view that totals quantities for identical products.
    * **Real-time Subtotals**: Each row displays the calculated price for that specific quantity.
    * **Quick Adjust**: Add or remove items directly from the sidebar with one click.
* **Financial Accuracy**: Automatic calculation of grand totals and customer change.
* **Inventory Alerts**: Visual warnings (red text) when stock levels for a variant drop below 5 units.

## 🛠️ Technical Setup

### Prerequisites
* Python 3.10 or higher (Current dev environment: 3.14).
* `customtkinter` library for the modern UI.

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
* **Fixed Cart Scuffing**: Implemented `grid_propagate(False)` and `minsize=450` to prevent the cart from shrinking.
* **Subtotal Alignment**: Added right-aligned (`anchor='e'`) subtotal labels with expanded widths to prevent currency symbol cropping.
* **Grid Optimization**: Updated `grid_columnconfigure` weights to prioritize the product catalog while keeping the sidebar and cart stable.

---
