# billtracker

A modern, multi-currency, and multi-language desktop application built with Python and Tkinter to help you manage your bills, track your budget, and stay on top of your finances.

The main interface of the Bill & Savings Tracker, showcasing the budget summary, bill entry, and lists of unpaid/paid bills.

✨ Key Features
💰 Budget Management: Set a monthly or periodic budget in any currency and track your spending as you pay your bills.

🌍 Multi-Currency Support: Add bills and set your budget in over 150 different currencies.

📈 Real-time Exchange Rates: Integrates with the ExchangeRate-API to automatically fetch the latest conversion rates, ensuring your financial summary is always accurate.

🗣️ Multi-Language Interface: The UI is available in 9 languages, including English, Georgian, Russian, German, Spanish, Italian, French, Dutch, and Chinese.

📊 Visual Budget Summary: A dynamic progress bar and color-coded text show you exactly how much of your budget remains after all unpaid bills are accounted for.

📅 Due Date Tracking: Assign a due date to each bill. Overdue bills are highlighted in red so you never miss a payment.

🗂️ Smart Bill Organization:

Separate lists for Unpaid and Paid bills.

Sort unpaid bills by Name, Due Date, or Amount.

Edit or Delete any bill easily.

🔧 Built-in Tools:

A handy Currency Converter for quick calculations.

A Settings panel to manage your API key and data file location.

💾 Persistent Data: Your bills, budget, and settings are saved locally to a JSON file, so your data is always there when you launch the app.

🎨 Modern & Animated UI: A sleek, dark-themed interface built with ttk styles, featuring a subtle, animated background for a pleasant user experience.

⚙️ Installation & Setup
Follow these steps to get the application running on your local machine.

1. Prerequisites
Python 3.7 or newer.

Git (for cloning the repository).

2. Clone the Repository
Bash

git clone <repository_url>
cd <repository_directory>
3. Install Dependencies
The application requires two external Python libraries. You can install them using pip:

Bash

pip install requests tkcalendar
4. Get an ExchangeRate-API Key (Crucial for Currency Features)
The application needs a free API key to fetch live currency exchange rates.

Go to www.exchangerate-api.com.

Sign up for the Free Plan.

Find the API key in your user dashboard.

Launch the application and open the Settings window to paste your key.

Without an API key, all currency conversions will fail.

5. Run the Application
Execute the Python script to launch the tracker:

Bash

python main.py
(Note: Replace main.py with the actual name of your Python file.)

📖 How to Use
Set Your Budget:

Enter your total budget amount in the top input field.

Select your primary currency from the dropdown menu.

Click "Set Budget". The application will store your budget internally in USD for consistent calculations.

Add a Bill:

In the "Add a New Bill" section, enter the bill's name, amount, currency, and due date.

Click "Add Bill". It will appear in the "Unpaid Bills" list.

Manage Your Bills:

Pay: Click the red "Pay" button next to an unpaid bill. The bill's amount will be deducted from your budget, and the item will move to the "Paid Bills" list.

Edit: Click the "Edit" button to open a new window where you can change the bill's details.

Delete: Click the "Del" button to permanently remove a bill.

Use the Tools:

Summarize: Choose a currency in the "Summarize in:" dropdown to see your budget summary converted to that currency.

Converter: Open the currency converter for quick, ad-hoc calculations.

Settings: Configure your API key and change where the application's data is stored on your computer.

📂 Configuration
The application automatically creates a hidden directory in your user home folder to store its data:

Location: ~/.bill_tracker/

config.json: Stores your API key and the path to your data file.

bill_data.json: Stores your budget, bills, and app preferences.

You can change the location of bill_data.json from the Settings window.

❤️ Author & Credits
This application was created with <3 by Grouvya.

Donate: Revolut

Contact: guns.lol/grouvya

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
