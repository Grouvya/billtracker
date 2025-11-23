
# Bill & Savings Tracker

A modern, native desktop application designed to help you organize your bills, manage your monthly budget, and handle multi-currency expenses effortlessly. Built with **Python**, **GTK4**, and **Libadwaita** for a seamless GNOME experience.

## ✨ Features

  * **Budget Management:** Set a monthly budget in your preferred currency and visualize your remaining funds after bills.
  * **Bill Tracking:**
      * Add, edit, delete, and mark bills as paid.
      * Track bill names, amounts, currencies, and due dates.
      * Visual indicators for overdue bills.
  * **Multi-Currency Support:**
      * Support for over 150 currencies (USD, EUR, GBP, JPY, etc.).
      * **Real-time Exchange Rates:** Automatically fetches live rates (no API key required).
      * **Offline Mode:** Caches rates locally so the app works even without an internet connection.
  * **Smart Summary:** Instantly view the "Total Unpaid" and "Budget After Bills" converted to your preferred summary currency.
  * **Built-in Tools:**
      * **Currency Converter:** A dedicated tool to quickly convert amounts between currencies.
      * **Sorting:** Sort your bills by Name, Due Date, or Amount (USD normalized).
  * **Privacy Focused:** All data is stored locally on your machine (`~/.bill_tracker/`).

## 🛠️ Prerequisites

To run this application, you need a Linux environment (recommended) with Python 3 and the GTK4/Libadwaita libraries installed.

### System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt install python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

**Fedora:**

```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita
```

**Arch Linux:**

```bash
sudo pacman -S python python-gobject gtk4 libadwaita
```

## 🚀 Installation & Usage

1.  **Clone or Download** the repository (or the `Billtracker.py` file).

2.  **Make the script executable:**

    ```bash
    chmod +x Billtracker.py
    ```

3.  **Run the application:**

    ```bash
    ./Billtracker.py
    ```

    *Or via python:*

    ```bash
    python3 Billtracker.py
    ```

## 📂 Data Storage

The application automatically creates a hidden directory in your home folder to store your settings and data:

  * **Directory:** `~/.bill_tracker/`
  * **Config File:** `config.json`
  * **Data File:** `bill_data.json` (Stores your bills and budget)
  * **Cache:** `rates_cache.json` (Stores the last known exchange rates)

*Note: You can change the location of the `bill_data.json` file in the application **Settings** if you wish to sync it via a cloud folder (e.g., Dropbox/Nextcloud).*

## 📖 User Guide

1.  **Setting a Budget:**
      * Enter your total income/budget at the top.
      * Select the currency (click the search icon to filter currencies).
      * Click **Set Budget**.
2.  **Adding a Bill:**
      * Enter the Bill Name (e.g., "Rent", "Netflix").
      * Enter the Amount and select the Currency.
      * Enter the Due Date (Format: YYYY-MM-DD).
      * Click **Add Bill**.
3.  **Summary View:**
      * Use the "Summarize in" dropdown to convert all your pending bills and remaining budget into a single currency for easy viewing.
4.  **Actions:**
      * **Pay:** Moves a bill from "Unpaid" to "Paid" and deducts the amount from your current budget.
      * **Edit:** Click the pencil icon to modify bill details.
      * **Converter:** Open the Currency Converter tool from the bottom action bar.

## 🤝 Contributing

Contributions are welcome\! If you find a bug or have a feature request, please open an issue.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 👤 Credits

  * **Developer:** [Grouvya](https://www.google.com/search?q=https://github.com/grouvya)
  * **Exchange Rates:** Data provided by [exchangerate.host](https://exchangerate.host) and [open.er-api.com](https://open.er-api.com).

## 📄 License

This project is open-source. Please check the repository for specific license details.

-----

*Made with \<3 by Grouvya*
