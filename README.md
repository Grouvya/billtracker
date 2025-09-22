# Bill & Savings Tracker

![App Icon](https://toppng.com/uploads/preview/free-icons-dollar-bills-transparent-background-11553537979k4k0dooqsl.png)

A modern, multi-language, and multi-currency desktop application built with Python and Tkinter to help you manage your bills, track your budget, and stay on top of your finances. It features a sleek, dark-themed UI with live currency conversion rates.

---

## ✨ Key Features

* **Budget Management**: Set a monthly or periodic budget in any currency and track your spending against it.
* **Bill Tracking**: Add, edit, and delete bills. Move them from "Unpaid" to "Paid" with a single click.
* **Multi-Currency Support**: Add bills and set your budget in over 150 different currencies.
* **Live Exchange Rates**: Integrates with `exchangerate-api.com` to provide real-time currency conversion, ensuring your financial summary is always accurate.
* **Multi-Language Interface**: Supports multiple languages including English, Georgian, Russian, German, Spanish, and more.
* **Data Persistence**: Your data (bills, budget, settings) is saved locally in a JSON file, so you never lose your progress.
* **Visual Financial Summary**: A progress bar and color-coded labels give you an instant overview of your financial health.
* **Built-in Currency Converter**: A handy tool to quickly convert between currencies.
* **Sorting & Filtering**: Sort unpaid bills by name, due date, or amount. Filter currency dropdowns by typing.
* **Customizable Settings**: Configure your API key and change the location of your data file through the settings menu.

---

## 📸 Screenshots

Here’s a sneak peek of the application's interface.

**Main Interface**
*(Shows the main window with budget section, bill entry form, financial summary, and lists of unpaid/paid bills.)*


**Settings Window**
*(Shows the settings panel where the user can enter their API key and change the data file path.)*


**Currency Converter**
*(Shows the standalone currency converter tool.)*


---

## 🛠️ Requirements

To run this application, you need Python 3 and the following libraries:

* **requests**: For making HTTP requests to the currency exchange API.
* **tkcalendar**: A date-picker widget for Tkinter.

These are standard Python libraries and can be easily installed. `Tkinter` is included with most Python installations.

---

## 🚀 Installation & Setup

Follow these steps to get the application up and running on your local machine.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/bill-tracker.git](https://github.com/your-username/bill-tracker.git)
    cd bill-tracker
    ```
    Alternatively, you can download the source code as a ZIP file and extract it.

2.  **Install Dependencies**
    Open your terminal or command prompt and run the following command to install the required libraries:
    ```bash
    pip install requests tkcalendar
    ```

3.  **Get a Free API Key (Crucial for Currency Rates)**
    The application uses **ExchangeRate-API** for live currency data. Their free plan is more than sufficient for personal use.

    * Go to [www.exchangerate-api.com](https://www.exchangerate-api.com) and sign up for a **Free Account**.
    * After signing up, go to your dashboard. You will see your API key.
    * Copy this key.

4.  **Run the Application**
    Execute the Python script from your terminal:
    ```bash
    python your_script_name.py
    ```

5.  **Configure the API Key**
    * When you first run the app, click the **Settings** button.
    * Paste the API key you copied into the "ExchangeRate-API Key" field.
    * Click **Save Key**. The application will immediately fetch the latest exchange rates and be fully functional.

---

## 📖 How to Use

1.  **Set Your Budget**: Enter your total budget amount, select its currency, and click "Set Budget".
2.  **Add Bills**: Fill in the bill's name, amount, currency, and due date. Click "Add Bill". It will appear in the "Unpaid Bills" list.
3.  **Manage Bills**:
    * Click **Pay** to move a bill to the "Paid Bills" list and deduct its value from your budget.
    * Click **Edit** to modify a bill's details.
    * Click **Del** to permanently remove a bill.
4.  **Monitor Your Finances**: The summary section shows the total amount of unpaid bills and your remaining budget after all bills are paid, all converted to your chosen summary currency.
5.  **Change Language**: Use the dropdown menu at the top right to switch the application's language instantly.
6.  **Use Tools**: Access the **Converter**, **Clear Data**, or **Settings** from the action buttons.

---

## 📁 File Structure

The application will automatically create a configuration directory in your user's home folder (`~/.bill_tracker/`) to store its data.

* `config.json`: Stores the API key and the path to your data file.
* `bill_data.json`: Stores your budget, bills, and other application data. You can change the location of this file via the in-app Settings.

---

## ✒️ Author & Credits

This application was created with ❤️ by **Grouvya**.

* **Donate**: [Revolut](https://revolut.me/grouvya)
* **Contact**: [guns.lol/grouvya](https://guns.lol/grouvya)

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
