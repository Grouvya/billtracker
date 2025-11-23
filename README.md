
[![App Shot1](https://i.imgur.com/MFl4Q3V.png))

![App Shot2](https://i.imgur.com/6Q4Ht7h.png)

![App Shot3](https://i.imgur.com/rFiNg6B.png)

Bill & Savings Tracker
A modern, native desktop application built with Python, GTK 4, and Libadwaita to help you manage your finances, track bills across multiple currencies, and monitor your budget in real-time.
🌟 Features
Budget Management: Set a monthly budget and track how much remains after your bills are paid.
Multi-Currency Support: Add bills in different currencies. The app automatically fetches live exchange rates and normalizes totals to your preferred summary currency.
Bill Tracking:
Add bills with names, amounts, currencies, and due dates.
Mark bills as paid or delete them.
Visual indicators for overdue bills.
Smart Sorting: Sort your unpaid bills by Name, Due Date, or Amount.
Currency Converter: A built-in tool to quickly convert between dozens of global currencies.
Offline Capability: Caches exchange rates locally so the app remains functional even without an internet connection.
Data Persistence: Automatically saves your data and settings to your local machine.
Modern UI: Built with Libadwaita for a clean, adaptive, and native GNOME look.
🛠️ Prerequisites
To run this application, you need Python 3 and the GTK 4 / Libadwaita libraries installed on your system.
Linux (Debian/Ubuntu/Fedora)
You will need the system packages for GTK 4 and Libadwaita, plus the Python bindings (PyGObject).
Ubuntu/Debian:
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1


Fedora:
sudo dnf install python3-gobject gtk4 libadwaita


Arch Linux:
sudo pacman -S python-gobject gtk4 libadwaita


macOS / Windows
While primarily designed for Linux environments utilizing GNOME, it can run on macOS or Windows if a GTK 4 runtime environment is correctly set up via gvsbuild or Brew, though Linux is the recommended platform.
🚀 Installation & Usage
Clone the repository (or download the file):
git clone [https://github.com/yourusername/bill-tracker.git](https://github.com/yourusername/bill-tracker.git)
cd bill-tracker


Make the script executable:
chmod +x Billtracker.py


Run the application:
./Billtracker.py

Or via python:
python3 Billtracker.py


📂 Data Location
The application stores your configuration and database locally in your home directory:
Linux: ~/.bill_tracker/
config.json: Application settings.
bill_data.json: Your saved bills and budget.
rates_cache.json: Cached currency exchange rates.
You can change the location of the data file within the app's Settings menu.
💱 API Usage
This application uses exchangerate.host and open.er-api.com to fetch real-time currency exchange rates. No API key is required for the default configuration.
🤝 Credits
Author: Grouvya
Built with: Python, GTK 4, Libadwaita
