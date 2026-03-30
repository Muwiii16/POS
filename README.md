# 🛒 Sari-Sari Smart POS (Point of Sale)

A robust, offline-first Desktop POS system built with Python and Tkinter. This project is designed specifically for small retail environments, combining high-speed barcode scanning with "Fuzzy Search" capabilities for manual item lookups.

## 🚀 Key Features
* **Dual-Mode Input:** Works with professional USB Barcode Scanners (Code128) and manual keyboard entry.
* **Fuzzy Logic Search:** Powered by `thefuzz`. If a sales lady types "pnts" or "notebk," the system intelligently finds "Pants" or "Notebooks."
* **Variant Management:** Handles product sub-types (Small, Medium, Large) with unique pricing and stock levels.
* **Real-Time Inventory:** Automatically deducts stock upon successful scan and prevents "Out of Stock" sales.
* **Native Windows UI:** Built with Tkinter for 100% offline reliability—no internet or browser required.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **GUI Framework:** Tkinter (Standard Library)
* **String Matching:** `thefuzz` (for fuzzy search logic)
* **Barcode standard:** Code128 / QR compatible

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/sari-sari-pos.git](https://github.com/YOUR_USERNAME/sari-sari-pos.git)
   cd sari-sari-pos