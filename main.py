#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import base64
import io
import webbrowser
import requests
import threading
from datetime import datetime, date
from tkcalendar import DateEntry # Added for date picking
import random

# -- Data and API Management Classes (Refactoring) --

class DataManager:
    """Handles loading and saving of config and application data."""
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.data_file = os.path.join(self.config_dir, 'bill_data.json') # Default data file
        os.makedirs(self.config_dir, exist_ok=True)

    def load_config(self):
        """Loads the app configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Update the data file path if it's in the config
                    self.data_file = config.get('data_file_path', self.data_file)
                    return config
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_config(self, config_data):
        """Saves the app configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def load_data(self):
        """Loads all bill and budget data."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, ValueError) as e:
                messagebox.showerror("Error", f"Could not read data file: {e}")
                return {}
        return {}

    def save_data(self, data_to_save):
        """Saves all bill and budget data."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            messagebox.showerror("Error", f"Could not write to data file: {e}")

class APIManager:
    """Handles all external API calls for exchange rates."""
    def __init__(self, api_key, result_callback):
        self.api_key = api_key
        self.result_callback = result_callback # Function to call with results

    def fetch_rates_async(self):
        """Fetches exchange rates in a background thread to avoid UI freezing."""
        if not self.api_key:
            self.result_callback({'status': 'error', 'message': 'api_key_missing'})
            return

        thread = threading.Thread(target=self._execute_fetch)
        thread.daemon = True
        thread.start()

    def _execute_fetch(self):
        """The actual network request logic."""
        url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("result") == "success":
                self.result_callback({'status': 'success', 'data': data})
            else:
                self.result_callback({'status': 'error', 'message': 'api_error'})
        except requests.exceptions.RequestException:
            self.result_callback({'status': 'error', 'message': 'network_error'})

class BillEditorWindow(tk.Toplevel):
    """A Toplevel window for editing a bill's details."""
    def __init__(self, parent, bill, currencies, save_callback, translations):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()

        self.bill = bill
        self.currencies = currencies
        self.save_callback = save_callback
        self.translations = translations

        self.title(self.translations["edit_bill_title"])
        self.configure(bg="#3c3c3c")
        self.geometry("400x350")

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TEntry', fieldbackground='#555555', foreground='#ffffff', font=('Helvetica', 12))
        self.style.configure('TLabel', background='#3c3c3c', foreground='#f0f0f0', font=('Helvetica', 12))
        self.style.configure('TButton', background='#005bb5', foreground='white', font=('Helvetica', 12, 'bold'))
        self.style.map('TButton', background=[('active', '#004b94')])

        frame = ttk.Frame(self, padding=20, style='TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        self.style.configure('TFrame', background='#3c3c3c')

        # --- Widgets ---
        ttk.Label(frame, text=self.translations["bill_name"]).pack(anchor='w')
        self.name_entry = ttk.Entry(frame)
        self.name_entry.pack(fill=tk.X, pady=(2, 10), ipady=4)
        self.name_entry.insert(0, bill['name'])

        ttk.Label(frame, text=self.translations["amount"]).pack(anchor='w')
        self.amount_entry = ttk.Entry(frame)
        self.amount_entry.pack(fill=tk.X, pady=(2, 10), ipady=4)
        self.amount_entry.insert(0, bill['amount'])

        ttk.Label(frame, text=self.translations["currency"]).pack(anchor='w')
        self.currency_var = tk.StringVar(value=bill['currency'])
        self.currency_menu = ttk.Combobox(frame, textvariable=self.currency_var, values=list(self.currencies.keys()), state='readonly')
        self.currency_menu.pack(fill=tk.X, pady=(2, 10), ipady=4)

        ttk.Label(frame, text=self.translations["due_date"]).pack(anchor='w')
        self.date_entry = DateEntry(frame, date_pattern='y-mm-dd', background='gray', foreground='white', borderwidth=2)
        self.date_entry.set_date(bill.get('due_date', date.today()))
        self.date_entry.pack(fill=tk.X, pady=(2, 20), ipady=4)

        save_button = ttk.Button(frame, text=self.translations["save_changes_button"], command=self.save_changes)
        save_button.pack(fill=tk.X, ipady=8)

    def save_changes(self):
        new_name = self.name_entry.get().strip()
        new_amount_str = self.amount_entry.get()

        if not new_name or not new_amount_str:
            messagebox.showerror(self.translations["input_error"], self.translations["name_amount_error"], parent=self)
            return

        try:
            new_amount = float(new_amount_str)
            if new_amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror(self.translations["input_error"], self.translations["positive_amount_error"], parent=self)
            return

        updated_bill = self.bill.copy()
        updated_bill['name'] = new_name
        updated_bill['amount'] = new_amount
        updated_bill['currency'] = self.currency_var.get()
        updated_bill['due_date'] = self.date_entry.get_date().strftime('%Y-%m-%d')

        self.save_callback(self.bill, updated_bill)
        self.destroy()


# -- Main Application Class --

class BillTrackerApp:
    """A desktop application for tracking bills and savings."""
    def __init__(self, root):
        self.root = root

        # --- Translations ---
        self.setup_translations()
        self.language_var = tk.StringVar(value="English")

        self.root.minsize(700, 800)
        self.root.title("Bill & Savings Tracker")
        self.setup_platform_tweaks()
        self.root.configure(bg="#3c3c3c")

        # --- Data & API Management ---
        config_dir = os.path.join(os.path.expanduser('~'), '.bill_tracker')
        self.data_manager = DataManager(config_dir)
        config = self.data_manager.load_config()
        self.api_key = config.get('api_key', "")
        self.api_manager = APIManager(self.api_key, self.handle_api_result)

        # --- Currency Data ---
        self.rates_status_var = tk.StringVar()
        self.currencies = self.get_currency_list()
        self.full_currency_list = list(self.currencies.keys())
        self.budget_currency_var = tk.StringVar(value="$ (USD)")
        self.bill_currency_var = tk.StringVar(value="$ (USD)")
        self.summary_currency_var = tk.StringVar(value="$ (USD)")
        self.exchange_rates = {}

        # --- Data storage ---
        self.unpaid_bills = []
        self.paid_bills = []
        self.budget = 0.0
        self.load_data()

        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # --- UI Initialization ---
        self.ui_elements = {}
        self.create_widgets()

        # --- Initial Data Load ---
        self.api_manager.fetch_rates_async()
        self.change_language()
        self.update_summary()
        self.update_bills_display()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.shades = []
        self.root.after(100, self.initialize_animation)

    def initialize_animation(self):
        self.shades = self.create_shades(20)
        self.animate_background()

    def setup_platform_tweaks(self):
        icon_b64 = """
        iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACx
        jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAd8SURBVHhe7Vt7sFdlGf7uvU+kl0ISAsKQRwgo
        G4EEElIYYiCDg8xMBkU1A5l0HBl1ZHR0dHTEdhxn1NEZRyf4A1d1RmeEdRzWZYMsyCKCiCBIgYSE
        BRLY/Z77OX/V3e++1V2v0nC/Tzqn53S/v+/vvO/7vu873/edhBDyv4TQZ1zQ51zQ51zQ51zQ51zQ
        59xPXXD19fXU6/W0XC7T0NCQ41wul9PU1JRyuZyWlpaU0+mU+vr6XNfX1xcj/uHhYdrd3ZXP+991
        wTMyMlJaWpps3traSnV1dZiamkp1dXWkpKSENm/eTFlZWZSUlERdXV2Sk5NDkZEROnToEAF++PBh
        SkpKSKVSKYmJiZLNZmlpaUkhISEkEgmsWLECubm5JBaLKS0tjcTERDpy5Ah9+vQphYWFKSgoSP+C
        /14XXHV1NcViMfn/0aNH5OfnEx0djb179+LEiRPYtGkTFi5ciMmTJ2Py5MlYv349tm3bhtWrV2Pj
        xo3Izs6GLVu2YM+ePaipqYEtW7bg4MGDCAwMxLJlyxAYGISLFy/iyJEj+Pz5M9RqNaysrKCurg63
        bt2Ca9euobKyEqdOncKVK1eQnJyMSZMmITU1FUuXLsXEiRNx4MABDB8+HJ9//jkuXryIpKQknDhx
        AmVlZaisrIS6ujq8efMGevx/nz5zF58mRcuXIF3t7eKCgoQEtLC2JiYmD48OHo1asX5s+fj8zM
        TDIyMsjPz6e6ujrpdLpc19DQkNfrX1/d3d2UlpZGNptlZWWlZBISEigUCiQSCWzbto3u3btHY2Mj
        RURE0NnZSWNjY+Sbb74hJCREhg4dSvX19XJxcZHS0lLp5+cn/Z/++gPz5s0jJSWF9u/fn/b399Or
        V68kLS2NsrKyZGlpKb19+5YWFhZKIBDIwMCAXN3d3TKVSmXg4uKihIWFyQcPHpS8vDzZ3Nys/Y31
        11dwcDB9/PixbNq0ifbu3Uvv3r2TPn78SLVaja5du4b58+ejR48eYDAY0NjYiE2bNuH8+XN4eXmB
        J0+e4ODBg4iMjMTo0aPx6dMnhIaG4vHjx/Dw8IDp06cjIiICPz8/OHz4MK5cuYKioiJUVVVBW1kZ
        oqOj8eTJExw4cECGqqqqoqSkBCMjI2hubsa0adPQo0cPeHp6orKyEmlpaVi5ciXmzZuHixcvoqOj
        g8TERBw9ehTHjx+Hc+fOobm5GWVlZWhtbUV0dDTOnz+PFStWYOvWrahRo0Zy/v7+ZGVlJQkJCXLs
        9/vJwcFBTk+m+/r6ZGFhobxL/11XcGpqKv369avE/v376dGjRxIfH0/9/f2SlJTEzs5OSUtLo7Ky
        Mjly5Ah9+vSJsrKyZGBgIL///nvp7++XsrKyZOTk5OQnJyZCQkJkpqZiamkpJSQkyMvL4dGjR8jM
        zMSBAwdw/PjxTe/evRMWFhZYWloiPz8fmZmZiIuLg4eHBwYPHoyTJ0+i1qxZuHnzJm7duoVTp05h
        6NChyMzMxMqVK7F69WosWLAAGxsbGDNmDI4cOYLq6mooLCxESkoKFizwP/7d+/H8uWLUMgEGBiYiKe
        PXuGY8eOobq6GjExMSgtLcWlS5fwySefICUlBQsWLMCaNWvQu3fvOHXqFLy9veHi4oKsrCycO3cO
        Ojo6sHDhQqxatQqTk5O4dOkSDg4OOHLkCDIyMhAYGIjU1FS8f/+e/v37IygoCGFhYeTk5GDmzJm4
        dOkSGhoa4OjoiOjoaCgoKKCvry+RSCTy9z9wXZ8p6POmYgGfc0Gfc0Gfc0Gfc0Gfc0Gfcz8v6POK
        tSgAAAAASUVORK5CYII=
        """
        try:
            icon_image = tk.PhotoImage(data=icon_b64)
            self.root.iconphoto(True, icon_image)
        except tk.TclError:
              print("Could not set app icon.")

    def load_data(self):
        data = self.data_manager.load_data()
        self.unpaid_bills = data.get('unpaid_bills', [])
        self.paid_bills = data.get('paid_bills', [])
        self.budget = float(data.get('budget', 0.0))

        saved_lang = data.get('language', 'English')
        if saved_lang in self.languages: self.language_var.set(saved_lang)

        default_currency = '$ (USD)'
        self.budget_currency_var.set(data.get('budget_currency', default_currency))
        self.bill_currency_var.set(data.get('bill_currency', default_currency))
        self.summary_currency_var.set(data.get('summary_currency', default_currency))

    def save_data(self):
        data = {
            'language': self.language_var.get(), 'budget': self.budget,
            'budget_currency': self.budget_currency_var.get(),
            'unpaid_bills': self.unpaid_bills, 'paid_bills': self.paid_bills,
            'bill_currency': self.bill_currency_var.get(),
            'summary_currency': self.summary_currency_var.get()
        }
        self.data_manager.save_data(data)

    def handle_api_result(self, result):
        lang_dict = self.translations[self.language_var.get()]
        if result['status'] == 'success':
            data = result['data']
            api_rates = data.get("conversion_rates", {})
            updated_rates = {}
            for app_currency_str in self.currencies:
                code = app_currency_str.split('(')[-1].replace(')', '').strip()
                if code in api_rates:
                    updated_rates[app_currency_str] = api_rates[code]
            updated_rates['$ (USD)'] = 1.0
            self.exchange_rates = updated_rates
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.rates_status_var.set(lang_dict["rates_updated_at"].format(now))
        else:
            self.rates_status_var.set(lang_dict[result['message']])

        self.root.after(0, self.update_budget_display)
        self.root.after(0, self.update_summary)

    def _filter_combobox(self, event, var, combobox_widget):
        query = var.get().lower()

        if query:
            filtered_list = [c for c in self.full_currency_list if query in c.lower()]
            combobox_widget['values'] = filtered_list
            if filtered_list:
                current_text = var.get()
                for item in filtered_list:
                    if item.lower().startswith(current_text.lower()):
                        var.set(item)
                        combobox_widget.icursor(len(current_text))
                        combobox_widget.selection_range(len(current_text), tk.END)
                        break
        else:
            combobox_widget['values'] = self.full_currency_list


    def configure_styles(self):
        dark_bg, light_fg, entry_bg = '#3c3c3c', '#f0f0f0', '#555555'
        self.style.configure('Main.TFrame', background=dark_bg)
        self.style.configure('Header.TLabel', background=dark_bg, foreground=light_fg, font=('Helvetica', 18, 'bold'))
        self.style.configure('Normal.TLabel', background='#4a4a4a', foreground=light_fg, font=('Helvetica', 12))
        self.style.configure('Paid.TLabel', background='#4a4a4a', foreground='#999999', font=('Helvetica', 12, 'overstrike'))
        self.style.configure('Overdue.TLabel', background='#4a4a4a', foreground='#ff6b6b', font=('Helvetica', 12, 'bold'))
        self.style.configure('Summary.TLabel', background=dark_bg, foreground=light_fg, font=('Helvetica', 14))
        self.style.configure('Credits.TLabel', background=dark_bg, foreground='#a0a0a0', font=('Helvetica', 9))
        self.style.configure('Status.TLabel', background=dark_bg, foreground='#cccccc', font=('Helvetica', 9, 'italic'))
        self.style.configure('Add.TButton', background='#005bb5', foreground='white', font=('Helvetica', 12, 'bold'), borderwidth=0, padding=10)
        self.style.map('Add.TButton', background=[('active', '#004b94')])
        self.style.configure('Pay.TButton', background='#a30018', foreground='white', font=('Helvetica', 10, 'bold'), borderwidth=0, padding=5)
        self.style.map('Pay.TButton', background=[('active', '#8b0014')])
        self.style.configure('Action.TButton', background='#333333', foreground='white', font=('Helvetica', 8), borderwidth=0, padding=4)
        self.style.map('Action.TButton', background=[('active', '#555555')])
        self.style.configure('Converter.TButton', background='#555555', foreground='white', font=('Helvetica', 10), borderwidth=0, padding=8)
        self.style.map('Converter.TButton', background=[('active', '#333333')])
        self.style.configure('TEntry', fieldbackground=entry_bg, foreground='#ffffff', font=('Helvetica', 12), bordercolor='#777777', borderwidth=1, relief='solid')
        self.style.map('TEntry', bordercolor=[('focus', '#007aff')])
        self.style.map('TCombobox', fieldbackground=[('readonly', entry_bg)], selectbackground=[('readonly', entry_bg)], foreground=[('readonly', light_fg)])
        self.style.configure("green.Horizontal.TProgressbar", background='#4caf50')
        self.style.configure("yellow.Horizontal.TProgressbar", background='#ffc107')
        self.style.configure("red.Horizontal.TProgressbar", background='#f44336')

    def create_widgets(self):
        self.bg_canvas = tk.Canvas(self.root, bg="#3c3c3c", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.bg_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.bg_canvas.configure(yscrollcommand=scrollbar.set)
        self.bg_canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = ttk.Frame(self.bg_canvas, style='Main.TFrame')
        self.canvas_frame_id = self.bg_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", lambda e: self.bg_canvas.configure(scrollregion=self.bg_canvas.bbox("all")))
        self.bg_canvas.bind("<Configure>", lambda e: self.bg_canvas.itemconfig(self.canvas_frame_id, width=e.width))
        self.bg_canvas.bind_all("<MouseWheel>", lambda e: self.bg_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        main_frame = ttk.Frame(self.scrollable_frame, padding="20", style='Main.TFrame')
        main_frame.pack(fill=tk.X, expand=True)

        lang_frame = ttk.Frame(main_frame, style='Main.TFrame')
        lang_frame.pack(fill=tk.X, anchor='ne', pady=(0, 10))
        lang_menu = ttk.Combobox(lang_frame, textvariable=self.language_var, values=list(self.translations.keys()), state='readonly', width=10)
        lang_menu.pack(side=tk.RIGHT)
        lang_menu.bind("<<ComboboxSelected>>", self.change_language)

        budget_frame = ttk.Frame(main_frame, style='Main.TFrame')
        budget_frame.pack(fill=tk.X, pady=(0, 20))
        self.ui_elements['budget_label'] = ttk.Label(budget_frame, style='Header.TLabel')
        self.ui_elements['budget_label'].pack(pady=(0, 10), anchor='w')
        budget_entry_frame = ttk.Frame(budget_frame, style='Main.TFrame')
        budget_entry_frame.pack(fill=tk.X)
        self.budget_entry = ttk.Entry(budget_entry_frame, width=30, style='TEntry')
        self.budget_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.budget_currency_menu = ttk.Combobox(budget_entry_frame, textvariable=self.budget_currency_var, values=self.full_currency_list, width=15)
        self.budget_currency_menu.pack(side=tk.LEFT, ipady=4, padx=(5,0))
        self.budget_currency_menu.bind('<KeyRelease>', lambda e: self._filter_combobox(e, self.budget_currency_var, self.budget_currency_menu))
        self.budget_currency_menu.bind("<<ComboboxSelected>>", lambda e: self.update_budget_display())
        self.ui_elements['set_budget_button'] = ttk.Button(budget_frame, command=self.set_budget, style='Converter.TButton')
        self.ui_elements['set_budget_button'].pack(fill=tk.X, pady=(10,0))

        input_frame = ttk.Frame(main_frame, style='Main.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 20))
        self.ui_elements['add_bill_label'] = ttk.Label(input_frame, style='Header.TLabel')
        self.ui_elements['add_bill_label'].pack(pady=(0, 15), anchor='w')
        self.ui_elements['bill_name_label'] = ttk.Label(input_frame, style='Summary.TLabel', font=('Helvetica', 10))
        self.ui_elements['bill_name_label'].pack(anchor='w', pady=(0,2))
        self.bill_name_entry = ttk.Entry(input_frame, width=40, style='TEntry')
        self.bill_name_entry.pack(fill=tk.X, pady=(0, 10), ipady=4)

        amount_frame = ttk.Frame(input_frame, style='Main.TFrame')
        amount_frame.pack(fill=tk.X, pady=(0, 15))

        amount_sub_frame = ttk.Frame(amount_frame, style='Main.TFrame')
        amount_sub_frame.pack(side=tk.LEFT, fill=tk.X, expand=True,padx=(0,10))
        self.ui_elements['amount_label'] = ttk.Label(amount_sub_frame, style='Summary.TLabel', font=('Helvetica', 10))
        self.ui_elements['amount_label'].pack(anchor='w', pady=(0,2))
        self.bill_amount_entry = ttk.Entry(amount_sub_frame, style='TEntry')
        self.bill_amount_entry.pack(fill=tk.X, ipady=4)

        currency_sub_frame = ttk.Frame(amount_frame, style='Main.TFrame')
        currency_sub_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        self.ui_elements['currency_label'] = ttk.Label(currency_sub_frame, style='Summary.TLabel', font=('Helvetica', 10))
        self.ui_elements['currency_label'].pack(anchor='w', pady=(0,2))
        self.currency_menu = ttk.Combobox(currency_sub_frame, textvariable=self.bill_currency_var, values=self.full_currency_list, width=15)
        self.currency_menu.pack(fill=tk.X, ipady=4)
        self.currency_menu.bind('<KeyRelease>', lambda e: self._filter_combobox(e, self.bill_currency_var, self.currency_menu))

        date_sub_frame = ttk.Frame(amount_frame, style='Main.TFrame')
        date_sub_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ui_elements['due_date_label'] = ttk.Label(date_sub_frame, style='Summary.TLabel', font=('Helvetica', 10))
        self.ui_elements['due_date_label'].pack(anchor='w', pady=(0,2))
        self.due_date_entry = DateEntry(date_sub_frame, date_pattern='y-mm-dd', background='gray', foreground='white', borderwidth=2)
        self.due_date_entry.pack(fill=tk.X, ipady=4)

        self.ui_elements['add_bill_button'] = ttk.Button(input_frame, command=self.add_bill, style='Add.TButton')
        self.ui_elements['add_bill_button'].pack(fill=tk.X, pady=(10,0))

        summary_frame = ttk.Frame(main_frame, style='Main.TFrame')
        summary_frame.pack(fill=tk.X, pady=15)
        summary_currency_frame = ttk.Frame(summary_frame, style='Main.TFrame')
        summary_currency_frame.pack(pady=(0,10))
        self.ui_elements['summarize_label'] = ttk.Label(summary_currency_frame, style='Summary.TLabel', font=('Helvetica', 10))
        self.ui_elements['summarize_label'].pack(side=tk.LEFT, padx=(0,5))
        self.summary_currency_menu = ttk.Combobox(summary_currency_frame, textvariable=self.summary_currency_var, values=self.full_currency_list, width=15)
        self.summary_currency_menu.pack(side=tk.LEFT)
        self.summary_currency_menu.bind("<<ComboboxSelected>>", self.on_currency_change)
        self.summary_currency_menu.bind('<KeyRelease>', lambda e: self._filter_combobox(e, self.summary_currency_var, self.summary_currency_menu))
        self.total_to_pay_var = tk.StringVar()
        self.remaining_budget_var = tk.StringVar()
        ttk.Label(summary_frame, textvariable=self.total_to_pay_var, style='Summary.TLabel').pack()
        self.remaining_budget_label = ttk.Label(summary_frame, textvariable=self.remaining_budget_var, style='Summary.TLabel', font=('Helvetica', 14, 'bold'))
        self.remaining_budget_label.pack(pady=5)
        self.budget_progressbar = ttk.Progressbar(summary_frame, orient='horizontal', mode='determinate', length=300)
        self.budget_progressbar.pack(fill=tk.X, pady=5)
        self.ui_elements['rates_status_label'] = ttk.Label(summary_frame, textvariable=self.rates_status_var, style='Status.TLabel')
        self.ui_elements['rates_status_label'].pack(pady=(5,0))

        actions_frame = ttk.Frame(main_frame, style='Main.TFrame')
        actions_frame.pack(pady=(0, 10))
        self.ui_elements['converter_button'] = ttk.Button(actions_frame, style='Converter.TButton', command=self.open_converter_window)
        self.ui_elements['converter_button'].pack(side=tk.LEFT, padx=5)
        self.ui_elements['clear_data_button'] = ttk.Button(actions_frame, style='Converter.TButton', command=self.clear_data)
        self.ui_elements['clear_data_button'].pack(side=tk.LEFT, padx=5)
        self.ui_elements['donate_button'] = ttk.Button(actions_frame, style='Converter.TButton', command=self.open_donate_link)
        self.ui_elements['donate_button'].pack(side=tk.LEFT, padx=5)
        self.ui_elements['refresh_rates_button'] = ttk.Button(actions_frame, style='Converter.TButton', command=self.api_manager.fetch_rates_async)
        self.ui_elements['refresh_rates_button'].pack(side=tk.LEFT, padx=5)
        self.ui_elements['settings_button'] = ttk.Button(actions_frame, style='Converter.TButton', command=self.open_settings_window)
        self.ui_elements['settings_button'].pack(side=tk.LEFT, padx=5)

        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        unpaid_frame = ttk.Frame(main_frame, style='Main.TFrame')
        unpaid_frame.pack(fill=tk.BOTH, expand=True)
        unpaid_header_frame = ttk.Frame(unpaid_frame, style='Main.TFrame')
        unpaid_header_frame.pack(fill=tk.X)
        self.ui_elements['unpaid_bills_label'] = ttk.Label(unpaid_header_frame, font=('Helvetica', 16, 'bold'), style='Header.TLabel')
        self.ui_elements['unpaid_bills_label'].pack(pady=5, anchor='w', side=tk.LEFT)
        sort_frame = ttk.Frame(unpaid_header_frame, style='Main.TFrame')
        sort_frame.pack(side=tk.RIGHT)
        self.ui_elements['sort_name_button'] = ttk.Button(sort_frame, style='Converter.TButton', command=self.sort_bills_by_name)
        self.ui_elements['sort_name_button'].pack(side=tk.LEFT, padx=2)
        self.ui_elements['sort_date_button'] = ttk.Button(sort_frame, style='Converter.TButton', command=self.sort_bills_by_date)
        self.ui_elements['sort_date_button'].pack(side=tk.LEFT, padx=2)
        self.ui_elements['sort_amount_button'] = ttk.Button(sort_frame, style='Converter.TButton', command=self.sort_bills_by_amount)
        self.ui_elements['sort_amount_button'].pack(side=tk.LEFT, padx=2)

        self.unpaid_bills_frame = ttk.Frame(unpaid_frame, style='Main.TFrame')
        self.unpaid_bills_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)
        paid_frame = ttk.Frame(main_frame, style='Main.TFrame')
        paid_frame.pack(fill=tk.BOTH, expand=True)
        self.ui_elements['paid_bills_label'] = ttk.Label(paid_frame, font=('Helvetica', 16, 'bold'), style='Header.TLabel')
        self.ui_elements['paid_bills_label'].pack(pady=5, anchor='w')
        self.paid_bills_frame = ttk.Frame(paid_frame, style='Main.TFrame')
        self.paid_bills_frame.pack(fill=tk.BOTH, expand=True)

        self.ui_elements['credits_label'] = ttk.Label(main_frame, style='Credits.TLabel', anchor='center', cursor="hand2")
        self.ui_elements['credits_label'].pack(side=tk.BOTTOM, fill=tk.X, pady=(10,0))
        self.ui_elements['credits_label'].bind("<Button-1>", self.open_credits_link)

    def create_shades(self, number):
        shades = []
        colors = ["#4a4a4a", "#555555", "#404040", "#4f4f4f"]
        for _ in range(number):
            radius = random.randint(30, 80)
            x = random.randint(radius, 600 - radius)
            y = random.randint(radius, 800 - radius)
            oval_id = self.bg_canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=random.choice(colors), outline="")
            self.bg_canvas.tag_lower(oval_id)
            shades.append({'id': oval_id, 'dx': random.uniform(-0.5, 0.5), 'dy': random.uniform(-0.5, 0.5)})
        return shades

    def animate_background(self):
        canvas_width = self.bg_canvas.winfo_width()
        canvas_height = self.bg_canvas.winfo_height()
        for shade in self.shades:
            coords = self.bg_canvas.coords(shade['id'])
            if coords and (coords[0] <= 0 or coords[2] >= canvas_width): shade['dx'] *= -1
            if coords and (coords[1] <= 0 or coords[3] >= canvas_height): shade['dy'] *= -1
            self.bg_canvas.move(shade['id'], shade['dx'], shade['dy'])
        self.root.after(50, self.animate_background)

    def change_language(self, event=None):
        t = self.translations[self.language_var.get()]
        self.root.title(t["window_title"])
        self.ui_elements['budget_label'].config(text=t["set_your_budget"])
        self.ui_elements['set_budget_button'].config(text=t["set_budget"])
        self.ui_elements['add_bill_label'].config(text=t["add_bill"])
        self.ui_elements['bill_name_label'].config(text=t["bill_name"])
        self.ui_elements['amount_label'].config(text=t["amount"])
        self.ui_elements['currency_label'].config(text=t["currency"])
        self.ui_elements['due_date_label'].config(text=t["due_date"])
        self.ui_elements['add_bill_button'].config(text=t["add_bill_button"])
        self.ui_elements['summarize_label'].config(text=t["summarize_in"])
        self.ui_elements['converter_button'].config(text=t["converter_button"])
        self.ui_elements['clear_data_button'].config(text=t["clear_data_button"])
        self.ui_elements['donate_button'].config(text=t["donate_button"])
        self.ui_elements['unpaid_bills_label'].config(text=t["unpaid_bills"])
        self.ui_elements['paid_bills_label'].config(text=t["paid_bills"])
        self.ui_elements['credits_label'].config(text=t["credits"])
        self.ui_elements['refresh_rates_button'].config(text=t["refresh_rates_button"])
        self.ui_elements['settings_button'].config(text=t["settings_button"])
        self.ui_elements['sort_name_button'].config(text=t["sort_by_name"])
        self.ui_elements['sort_date_button'].config(text=t["sort_by_date"])
        self.ui_elements['sort_amount_button'].config(text=t["sort_by_amount"])
        self.update_summary()
        self.update_bills_display()

    def update_budget_display(self, event=None):
        rate = self.exchange_rates.get(self.budget_currency_var.get())
        if rate and rate > 0:
            display_amount = self.budget * rate
            self.budget_entry.delete(0, tk.END)
            self.budget_entry.insert(0, f"{display_amount:,.2f}")
        else:
            self.budget_entry.delete(0, tk.END)
            self.budget_entry.insert(0, f"{self.budget:,.2f}")

    def on_currency_change(self, event=None):
        self.update_summary()
        self.update_bills_display()

    def set_budget(self):
        lang_dict = self.translations[self.language_var.get()]
        try:
            displayed_amount = float(self.budget_entry.get().replace(',', ''))
            budget_curr = self.budget_currency_var.get()
            rate = self.exchange_rates.get(budget_curr)

            if not rate or rate <= 0:
                messagebox.showwarning("Error", "Could not find exchange rate for budget currency.", parent=self.root)
                return

            self.budget = displayed_amount / rate
            self.update_summary()

            formatted_amount = f"{self.currencies.get(budget_curr, '')}{displayed_amount:,.2f}"
            messagebox.showinfo(lang_dict["budget_set"], lang_dict["budget_set_to"].format(formatted_amount))
        except ValueError:
            messagebox.showwarning(lang_dict["input_error"], lang_dict["valid_number_error"])

    def add_bill(self):
        lang_dict = self.translations[self.language_var.get()]
        name = self.bill_name_entry.get().strip()
        amount_str = self.bill_amount_entry.get()
        currency = self.bill_currency_var.get()
        due_date = self.due_date_entry.get_date().strftime('%Y-%m-%d')

        if not name or not amount_str:
            messagebox.showwarning(lang_dict["input_error"], lang_dict["name_amount_error"])
            return
        try:
            amount = float(amount_str.replace(',', ''))
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning(lang_dict["input_error"], lang_dict["positive_amount_error"])
            return

        bill = {"name": name, "amount": amount, "currency": currency, "due_date": due_date}
        self.unpaid_bills.append(bill)
        self.bill_name_entry.delete(0, tk.END)
        self.bill_amount_entry.delete(0, tk.END)
        self.update_summary()
        self.update_bills_display()

    def pay_bill(self, bill_to_pay):
        lang_dict = self.translations[self.language_var.get()]
        if not messagebox.askyesno(lang_dict["confirm_payment_title"], lang_dict["confirm_payment_msg"].format(bill_to_pay['name'])):
            return

        rate_vs_usd = self.exchange_rates.get(bill_to_pay['currency'])
        if rate_vs_usd and rate_vs_usd > 0:
            self.budget -= bill_to_pay['amount'] / rate_vs_usd
            self.update_budget_display()

        self.unpaid_bills.remove(bill_to_pay)
        self.paid_bills.append(bill_to_pay)
        self.update_summary()
        self.update_bills_display()

    def delete_bill(self, bill_to_delete):
        lang_dict = self.translations[self.language_var.get()]
        if messagebox.askyesno(lang_dict["confirm_delete_title"], lang_dict["confirm_delete_msg"].format(bill_to_delete['name'])):
            if bill_to_delete in self.unpaid_bills:
                self.unpaid_bills.remove(bill_to_delete)
            elif bill_to_delete in self.paid_bills:
                self.paid_bills.remove(bill_to_delete)
            self.update_summary()
            self.update_bills_display()

    def edit_bill(self, bill_to_edit):
        lang_dict = self.translations[self.language_var.get()]
        BillEditorWindow(self.root, bill_to_edit, self.currencies, self.handle_bill_edited, lang_dict)

    def handle_bill_edited(self, original_bill, updated_bill):
        try:
            index = self.unpaid_bills.index(original_bill)
            self.unpaid_bills[index] = updated_bill
            self.update_summary()
            self.update_bills_display()
        except ValueError:
            print("Could not find original bill to update.")

    def sort_bills_by_name(self):
        self.unpaid_bills.sort(key=lambda b: b['name'].lower())
        self.update_bills_display()

    def sort_bills_by_date(self):
        self.unpaid_bills.sort(key=lambda b: datetime.strptime(b.get('due_date', '9999-12-31'), '%Y-%m-%d'))
        self.update_bills_display()

    def sort_bills_by_amount(self):
        def get_usd_amount(bill):
            rate = self.exchange_rates.get(bill['currency'], 1)
            return bill['amount'] / rate if rate > 0 else float('inf')
        self.unpaid_bills.sort(key=get_usd_amount, reverse=True)
        self.update_bills_display()

    def update_summary(self):
        lang_dict = self.translations[self.language_var.get()]
        summary_curr_str = self.summary_currency_var.get()
        summary_symbol = self.currencies.get(summary_curr_str, '$')
        target_rate = self.exchange_rates.get(summary_curr_str)

        if not target_rate:
            return

        total_to_pay_usd = sum(b['amount'] / self.exchange_rates.get(b['currency'], 1) for b in self.unpaid_bills if self.exchange_rates.get(b['currency']))
        remaining_budget_usd = self.budget - total_to_pay_usd

        final_to_pay = total_to_pay_usd * target_rate
        remaining_budget_display = remaining_budget_usd * target_rate

        self.total_to_pay_var.set(f"{lang_dict['total_unpaid']} {summary_symbol}{final_to_pay:,.2f}")
        self.remaining_budget_var.set(f"{lang_dict['budget_after_paying']} {summary_symbol}{remaining_budget_display:,.2f}")

        if self.budget > 0:
            percentage = (remaining_budget_usd / self.budget) * 100
            self.budget_progressbar['value'] = max(0, percentage)
            if percentage < 25:
                self.budget_progressbar.config(style="red.Horizontal.TProgressbar")
                self.remaining_budget_label.config(foreground='#f44336')
            elif percentage < 50:
                self.budget_progressbar.config(style="yellow.Horizontal.TProgressbar")
                self.remaining_budget_label.config(foreground='#ffc107')
            else:
                self.budget_progressbar.config(style="green.Horizontal.TProgressbar")
                self.remaining_budget_label.config(foreground='#4caf50')
        else:
            self.budget_progressbar['value'] = 0

    def update_bills_display(self):
        lang_dict = self.translations[self.language_var.get()]
        for frame in [self.unpaid_bills_frame, self.paid_bills_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        for bill in self.unpaid_bills:
            bill_frame = ttk.Frame(self.unpaid_bills_frame, style='Normal.TLabel', padding=10)
            bill_frame.pack(fill=tk.X, pady=4)

            symbol = self.currencies.get(bill['currency'], '$')
            due_date_str = bill.get('due_date', lang_dict["no_date"])
            label_text = f"{bill['name']}: {symbol}{bill['amount']:,.2f} ({lang_dict['due_on']} {due_date_str})"

            label_style = 'Normal.TLabel'
            try:
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date_obj < date.today():
                    label_style = 'Overdue.TLabel'
            except (ValueError, TypeError):
                pass

            ttk.Label(bill_frame, text=label_text, style=label_style).pack(side=tk.LEFT, expand=True, fill=tk.X)

            button_frame = ttk.Frame(bill_frame, style='Normal.TLabel')
            button_frame.pack(side=tk.RIGHT)
            ttk.Button(button_frame, text=lang_dict["edit_button"], style='Action.TButton', command=lambda b=bill: self.edit_bill(b)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text=lang_dict["delete_button"], style='Action.TButton', command=lambda b=bill: self.delete_bill(b)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text=lang_dict["pay_button"], style='Pay.TButton', command=lambda b=bill: self.pay_bill(b)).pack(side=tk.LEFT, padx=2)

        for bill in self.paid_bills:
            bill_frame = ttk.Frame(self.paid_bills_frame, style='Normal.TLabel', padding=10)
            bill_frame.pack(fill=tk.X, pady=4)
            symbol = self.currencies.get(bill['currency'], '$')
            label_text = f"{bill['name']}: {symbol}{bill['amount']:,.2f}"
            ttk.Label(bill_frame, text=label_text, style='Paid.TLabel').pack(side=tk.LEFT, expand=True, fill=tk.X)

    def open_converter_window(self):
        lang_dict = self.translations[self.language_var.get()]
        converter_window = tk.Toplevel(self.root)
        converter_window.title(lang_dict["converter_window_title"])
        converter_window.geometry("400x350")
        converter_window.configure(bg="#3c3c3c")
        try:
            converter_window.attributes('-alpha', 0.95)
        except tk.TclError: pass

        frame = ttk.Frame(converter_window, padding=20, style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=lang_dict["amount"], style='Header.TLabel', font=('Helvetica', 12)).pack(pady=5)
        amount_entry = ttk.Entry(frame, style='TEntry')
        amount_entry.pack(fill=tk.X, ipady=4)

        from_currency_var = tk.StringVar(value="$ (USD)")
        to_currency_var = tk.StringVar(value="€ (EUR)")

        from_menu = ttk.Combobox(frame, textvariable=from_currency_var, values=self.full_currency_list, width=15)
        to_menu = ttk.Combobox(frame, textvariable=to_currency_var, values=self.full_currency_list, width=15)

        ttk.Label(frame, text=lang_dict["from"], style='Header.TLabel', font=('Helvetica', 12)).pack(pady=5)
        from_menu.pack(fill=tk.X, ipady=4)
        from_menu.bind('<KeyRelease>', lambda e: self._filter_combobox(e, from_currency_var, from_menu))

        ttk.Label(frame, text=lang_dict["to"], style='Header.TLabel', font=('Helvetica', 12)).pack(pady=5)
        to_menu.pack(fill=tk.X, ipady=4)
        to_menu.bind('<KeyRelease>', lambda e: self._filter_combobox(e, to_currency_var, to_menu))

        result_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=result_var, style='Summary.TLabel', font=('Helvetica', 14, 'bold')).pack(pady=20)

        def perform_conversion():
            try:
                amount = float(amount_entry.get().replace(',', ''))
                from_rate_vs_usd = self.exchange_rates.get(from_currency_var.get())
                to_rate_vs_usd = self.exchange_rates.get(to_currency_var.get())

                if not from_rate_vs_usd or not to_rate_vs_usd:
                    raise KeyError

                amount_in_usd = amount / from_rate_vs_usd
                converted_amount = amount_in_usd * to_rate_vs_usd

                to_symbol = self.currencies[to_currency_var.get()]
                result_var.set(f"{to_symbol}{converted_amount:,.2f}")
            except (ValueError, KeyError):
                result_var.set(lang_dict["invalid_input"])

        convert_button = ttk.Button(frame, text=lang_dict["convert_button"], command=perform_conversion, style='Add.TButton')
        convert_button.pack(fill=tk.X)

    def clear_data(self):
        lang_dict = self.translations[self.language_var.get()]
        if messagebox.askyesno(lang_dict["clear_data_confirm_title"], lang_dict["clear_data_confirm_msg"]):
            self.unpaid_bills, self.paid_bills, self.budget = [], [], 0.0
            self.update_budget_display()
            self.update_summary()
            self.update_bills_display()
            self.save_data()
            messagebox.showinfo(lang_dict["data_cleared_title"], lang_dict["data_cleared_msg"])

    def open_settings_window(self):
        lang_dict = self.translations[self.language_var.get()]
        settings_window = tk.Toplevel(self.root)
        settings_window.title(lang_dict["settings_window_title"])
        settings_window.geometry("450x450")
        settings_window.configure(bg="#3c3c3c")

        frame = ttk.Frame(settings_window, padding=20, style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        instructions_label = tk.Label(
            frame, text=lang_dict["api_instructions"], wraplength=400, justify=tk.LEFT,
            bg="#3c3c3c", fg="#cccccc", font=('Helvetica', 11),
        )
        instructions_label.pack(pady=(0, 10), fill=tk.X)

        def open_api_link(event):
            webbrowser.open_new("https://www.exchangerate-api.com")

        link_label = tk.Label(
            frame, text="www.exchangerate-api.com", fg="#64b5f6", cursor="hand2",
            bg="#3c3c3c", font=('Helvetica', 11, 'underline')
        )
        link_label.pack()
        link_label.bind("<Button-1>", open_api_link)

        ttk.Label(frame, text=lang_dict["api_key_label"], style='Header.TLabel', font=('Helvetica', 12)).pack(pady=5)
        api_key_entry = ttk.Entry(frame, style='TEntry', width=40)
        api_key_entry.pack(fill=tk.X, ipady=4, pady=(0, 10))
        api_key_entry.insert(0, self.api_key)
        save_button = ttk.Button(frame, text=lang_dict["save_key_button"], style='Converter.TButton')
        save_button.pack(fill=tk.X, pady=(0,20))

        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)

        ttk.Label(frame, text=lang_dict["data_file_location"], style='Header.TLabel', font=('Helvetica', 12)).pack(pady=5)
        path_frame = ttk.Frame(frame, style='Main.TFrame')
        path_frame.pack(fill=tk.X)

        data_path_var = tk.StringVar(value=self.data_manager.data_file)
        path_entry = ttk.Entry(path_frame, textvariable=data_path_var, style='TEntry', state='readonly')
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def browse_and_set_path():
            new_path = filedialog.asksaveasfilename(
                parent=settings_window, title="Choose a new data file location",
                initialfile="bill_data.json", defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            if new_path:
                self.data_manager.data_file = new_path
                data_path_var.set(new_path)
                config = self.data_manager.load_config()
                config['data_file_path'] = new_path
                self.data_manager.save_config(config)
                self.save_data()
                messagebox.showinfo(lang_dict["path_saved_title"], lang_dict["path_saved_msg"], parent=settings_window)

        browse_button = ttk.Button(path_frame, text=lang_dict["browse_button"], command=browse_and_set_path, style='Converter.TButton')
        browse_button.pack(side=tk.LEFT, padx=(5,0))

        def save_key_action():
            self.api_key = api_key_entry.get().strip()
            self.api_manager.api_key = self.api_key
            config = self.data_manager.load_config()
            config['api_key'] = self.api_key
            self.data_manager.save_config(config)
            self.api_manager.fetch_rates_async()
            messagebox.showinfo(lang_dict["api_key_saved_title"], lang_dict["api_key_saved_msg"], parent=settings_window)

        save_button['command'] = save_key_action

    def open_donate_link(self):
        webbrowser.open_new("https://revolut.me/grouvya")

    def open_credits_link(self, event=None):
        webbrowser.open_new("https://guns.lol/grouvya")

    def on_closing(self):
        config = {'api_key': self.api_key, 'data_file_path': self.data_manager.data_file}
        self.data_manager.save_config(config)
        self.save_data()
        self.root.destroy()

    def get_currency_list(self):
        return { '؋ (AFN)': '؋', 'Lek (ALL)': 'Lek', 'դր. (AMD)': 'դր.', 'ƒ (ANG)': 'ƒ', 'Kz (AOA)': 'Kz', '$ (ARS)': '$', 'A$ (AUD)': 'A$', 'ƒ (AWG)': 'ƒ', '₼ (AZN)': '₼', 'KM (BAM)': 'KM', '$ (BBD)': '$', '৳ (BDT)': '৳', 'лв (BGN)': 'лв', '.د.ب (BHD)': '.د.ب', 'FBu (BIF)': 'FBu', '$ (BMD)': '$', '$ (BND)': '$', 'Bs. (BOB)': 'Bs.', 'R$ (BRL)': 'R$', '$ (BSD)': '$', 'Nu. (BTN)': 'Nu.', 'P (BWP)': 'P', 'Br (BYN)': 'Br', '$ (BZD)': '$', 'C$ (CAD)': 'C$', 'Fr (CDF)': 'Fr', 'Fr (CHF)': 'Fr', '$ (CLP)': '$', '¥ (CNY)': '¥', '$ (COP)': '$', '₡ (CRC)': '₡', '$ (CUP)': 'CUP', '$ (CVE)': '$', 'Kč (CZK)': 'Kč', 'Fdj (DJF)': 'Fdj', 'kr (DKK)': 'kr', 'RD$ (DOP)': 'RD$', 'DA (DZD)': 'DA', 'E£ (EGP)': 'E£', 'Nfk (ERN)': 'Nfk', 'Br (ETB)': 'Br', '€ (EUR)': '€', '$ (FJD)': '$', '£ (FKP)': '£', '£ (GBP)': '£', '₾ (GEL)': '₾', '£ (GGP)': '£', 'GH₵ (GHS)': 'GH₵', '£ (GIP)': '£', 'D (GMD)': 'D', 'Fr (GNF)': 'Fr', 'Q (GTQ)': 'Q', '$ (GYD)': '$', 'HK$ (HKD)': 'HK$', 'L (HNL)': 'L', 'kn (HRK)': 'kn', 'G (HTG)': 'G', 'Ft (HUF)': 'Ft', 'Rp (IDR)': 'Rp', '₪ (ILS)': '₪', '£ (IMP)': '£', '₹ (INR)': '₹', 'ع.د (IQD)': 'ع.د', '﷼ (IRR)': '﷼', 'kr (ISK)': 'kr', '£ (JEP)': '£', '$ (JMD)': '$', 'JD (JOD)': 'JD', '¥ (JPY)': '¥', 'KSh (KES)': 'KSh', 'лв (KGS)': 'лв', '៛ (KHR)': '៛', 'Fr (KMF)': 'Fr', '₩ (KPW)': '₩', '₩ (KRW)': '₩', 'KD (KWD)': 'KD', '$ (KYD)': '$', '〒 (KZT)': '〒', '₭ (LAK)': '₭', 'ل.ل (LBP)': 'ل.ل', '₨ (LKR)': '₨', '$ (LRD)': '$', 'L (LSL)': 'L', 'LTL (LTL)': 'LTL', 'Ls (LVL)': 'Ls', 'ل.د (LYD)': 'ل.د', 'د.م. (MAD)': 'د.მ.', 'L (MDL)': 'L', 'Ar (MGA)': 'Ar', 'ден (MKD)': 'ден', 'K (MMK)': 'K', '₮ (MNT)': '₮', 'P (MOP)': 'P', 'UM (MRO)': 'UM', '₨ (MUR)': '₨', 'Rf (MVR)': 'Rf', 'MK (MWK)': 'MK', '$ (MXN)': '$', 'RM (MYR)': 'RM', 'MTn (MZN)': 'MTn', 'N$ (NAD)': 'N$', '₦ (NGN)': '₦', 'C$ (NIO)': 'C$', 'kr (NOK)': 'kr', '₨ (NPR)': '₨', 'NZ$ (NZD)': 'NZ$', '﷼ (OMR)': '﷼', 'B/. (PAB)': 'B/.', 'S/. (PEN)': 'S/.', 'K (PGK)': 'K', '₱ (PHP)': '₱', '₨ (PKR)': '₨', 'zł (PLN)': 'zł', '₲ (PYG)': '₲', '﷼ (QAR)': '﷼', 'lei (RON)': 'lei', 'din (RSD)': 'din', '₽ (RUB)': '₽', 'FRw (RWF)': 'FRw', '﷼ (SAR)': '﷼', '$ (SBD)': '$', '₨ (SCR)': '₨', 'ج.س. (SDG)': 'ج.س.', 'kr (SEK)': 'kr', 'S$ (SGD)': 'S$', '£ (SHP)': '£', 'Le (SLL)': 'Le', 'S (SOS)': 'S', '$ (SRD)': '$', 'Db (STD)': 'Db', '$ (SVC)': '$', '£S (SYP)': '£S', 'L (SZL)': 'L', '฿ (THB)': '฿', 'ЅМ (TJS)': 'ЅМ', 'T (TMT)': 'T', 'د.ت (TND)': 'د.ت', 'T$ (TOP)': 'T$', '₺ (TRY)': '₺', 'TT$ (TTD)': 'TT$', 'NT$ (TWD)': 'NT$', 'TSh (TZS)': 'TSh', '₴ (UAH)': '₴', 'USh (UGX)': 'USh', '$ (USD)': '$', '$U (UYU)': '$U', 'soʻm (UZS)': 'soʻm', 'Bs (VEF)': 'Bs', '₫ (VND)': '₫', 'Vt (VUV)': 'Vt', 'T (WST)': 'T', 'Fr (XAF)': 'Fr', '$ (XCD)': '$', 'Fr (XOF)': 'Fr', 'Fr (XPF)': 'Fr', '﷼ (YER)': '﷼', 'R (ZAR)': 'R', 'ZK (ZMW)': 'ZK', 'Z$ (ZWL)': 'Z$' }

    def setup_translations(self):
        self.languages = ["English", "Georgian", "Russian", "German", "Spanish", "Italian", "French", "Dutch", "Chinese"]
        self.translations = {
            "English": {
                "window_title": "Bill & Savings Tracker", "set_your_budget": "Set Your Budget:", "set_budget": "Set Budget",
                "add_bill": "Add a New Bill", "bill_name": "Bill Name:", "amount": "Amount:", "currency": "Currency:", "due_date": "Due Date:",
                "add_bill_button": "Add Bill", "summarize_in": "Summarize in:", "total_unpaid": "Total of Unpaid Bills:",
                "budget_after_paying": "Budget After Paying Bills:", "converter_button": "Converter", "clear_data_button": "Clear Data",
                "donate_button": "Donate", "unpaid_bills": "Unpaid Bills", "paid_bills": "Paid Bills", "credits": "made with <3 by Grouvya!",
                "pay_button": "Pay", "converter_window_title": "Currency Converter", "from": "From:", "to": "To:", "convert_button": "Convert",
                "input_error": "Input Error", "valid_number_error": "Please enter a valid number for the budget.", "budget_set": "Budget Set",
                "budget_set_to": "Budget set to {}", "valid_currency_error": "Please select a valid currency.",
                "name_amount_error": "Please enter both name and amount.", "positive_amount_error": "Please enter a valid positive amount.",
                "invalid_input": "Invalid Input", "clear_data_confirm_title": "Clear All Data",
                "clear_data_confirm_msg": "Are you sure you want to delete all bills and reset your budget? This action cannot be undone.",
                "data_cleared_title": "Data Cleared", "data_cleared_msg": "All data has been successfully cleared.", "error": "Error",
                "refresh_rates_button": "Refresh Rates", "settings_button": "Settings", "settings_window_title": "Settings",
                "api_key_label": "ExchangeRate-API Key:", "save_key_button": "Save Key",
                "api_instructions": "To get real-time currency rates:\n1. Go to www.exchangerate-api.com\n2. Sign up for the free plan.\n3. Find the API key in your dashboard.\n4. Copy and paste it here.",
                "api_key_saved_title": "API Key Saved", "api_key_saved_msg": "Your API key has been saved successfully!",
                "api_key_missing": "API key missing. Go to Settings.", "rates_updated_at": "Live rates updated: {}",
                "api_error": "API error. Using cached rates.", "network_error": "Network error. Using cached rates.",
                "data_file_location": "Data File Location:", "browse_button": "Browse...", "path_saved_title": "Path Saved",
                "path_saved_msg": "Data file path has been updated. The app will use this new path on next launch.",
                "sort_by_name": "Sort: Name", "sort_by_date": "Sort: Date", "sort_by_amount": "Sort: Amount",
                "edit_bill_title": "Edit Bill", "save_changes_button": "Save Changes", "due_on": "Due:", "no_date": "No Date",
                "edit_button": "Edit", "delete_button": "Del", "confirm_payment_title": "Confirm Payment", "confirm_payment_msg": "Are you sure you want to pay '{}'?",
                "confirm_delete_title": "Confirm Delete", "confirm_delete_msg": "Are you sure you want to delete '{}'?"
            },
            "Georgian": {
                "window_title": "ანგარიშების და დანაზოგების ტრეკერი", "set_your_budget": "ბიუჯეტის დაყენება:", "set_budget": "ბიუჯეტის დაყენება",
                "add_bill": "ახალი ანგარიშის დამატება", "bill_name": "ანგარიშის სახელი:", "amount": "თანხა:", "currency": "ვალუტა:", "due_date": "გადახდის თარიღი:",
                "add_bill_button": "ანგარიშის დამატება", "summarize_in": "შეჯამება:", "total_unpaid": "გადასახდელი ანგარიშების ჯამი:",
                "budget_after_paying": "ბიუჯეტი გადახდების შემდეგ:", "converter_button": "კონვერტორი", "clear_data_button": "მონაცემების წაშლა",
                "donate_button": "შემოწირულობა", "unpaid_bills": "გადაუხდელი ანგარიშები", "paid_bills": "გადახდილი ანგარიშები", "credits": "შექმნილია <3-ით Grouvya-ს მიერ!",
                "pay_button": "გადახდა", "converter_window_title": "ვალუტის კონვერტორი", "from": "საიდან:", "to": "სად:", "convert_button": "კონვერტაცია",
                "input_error": "შეყვანის შეცდომა", "valid_number_error": "გთხოვთ შეიყვანოთ სწორი რიცხვი ბიუჯეტისთვის.", "budget_set": "ბიუჯეტი დაყენებულია",
                "budget_set_to": "ბიუჯეტი დაყენებულია: {}", "valid_currency_error": "გთხოვთ აირჩიოთ სწორი ვალუტა.",
                "name_amount_error": "გთხოვთ შეიყვანოთ სახელი და თანხა.", "positive_amount_error": "გთხოვთ შეიყვანოთ დადებითი თანხა.",
                "invalid_input": "არასწორი შეყვანა", "clear_data_confirm_title": "ყველა მონაცემის წაშლა",
                "clear_data_confirm_msg": "დარწმუნებული ხართ რომ გსურთ ყველა ანგარიშის წაშლა და ბიუჯეტის განულება? ამ მოქმედების დაბრუნება შეუძლებელია.",
                "data_cleared_title": "მონაცემები წაშლილია", "data_cleared_msg": "ყველა მონაცემი წარმატებით წაიშალა.", "error": "შეცდომა",
                "refresh_rates_button": "კურსების განახლება", "settings_button": "პარამეტრები", "settings_window_title": "პარამეტრები",
                "api_key_label": "ExchangeRate-API გასაღები:", "save_key_button": "გასაღების შენახვა",
                "api_instructions": "რეალური კურსების მისაღებად:\n1. გადადით www.exchangerate-api.com\n2. დარეგისტრირდით უფასო გეგმაზე.\n3. იპოვეთ API გასაღები თქვენს პანელში.\n4. დააკოპირეთ და ჩასვით აქ.",
                "api_key_saved_title": "API გასაღები შენახულია", "api_key_saved_msg": "თქვენი API გასაღები წარმატებით შეინახა!",
                "api_key_missing": "API გასაღები აკლია. გადადით პარამეტრებში.", "rates_updated_at": "კურსები განახლდა: {}",
                "api_error": "API შეცდომა. გამოიყენება შენახული კურსები.", "network_error": "ქსელის შეცდომა. გამოიყენება შენახული კურსები.",
                "data_file_location": "მონაცემთა ფაილის მდებარეობა:", "browse_button": "არჩევა...", "path_saved_title": "გზა შენახულია",
                "path_saved_msg": "მონაცემთა ფაილის გზა განახლდა. აპლიკაცია გამოიყენებს ახალ გზას შემდეგ გაშვებაზე.",
                "sort_by_name": "დალაგება: სახელით", "sort_by_date": "დალაგება: თარიღით", "sort_by_amount": "დალაგება: თანხით",
                "edit_bill_title": "ანგარიშის რედაქტირება", "save_changes_button": "ცვლილებების შენახვა", "due_on": "ვადა:", "no_date": "თარიღის გარეშე",
                "edit_button": "რედაქ.", "delete_button": "წაშლა", "confirm_payment_title": "გადახდის დადასტურება", "confirm_payment_msg": "დარწმუნებული ხართ რომ გსურთ გადაიხადოთ '{}'?",
                "confirm_delete_title": "წაშლის დადასტურება", "confirm_delete_msg": "დარწმუნებული ხართ რომ გსურთ წაშალოთ '{}'?"
            },
            "Russian": {
                "window_title": "Трекер счетов и сбережений", "set_your_budget": "Установить бюджет:", "set_budget": "Установить бюджет",
                "add_bill": "Добавить новый счет", "bill_name": "Название счета:", "amount": "Сумма:", "currency": "Валюта:", "due_date": "Срок оплаты:",
                "add_bill_button": "Добавить счет", "summarize_in": "Суммировать в:", "total_unpaid": "Сумма неоплаченных счетов:",
                "budget_after_paying": "Бюджет после оплаты:", "converter_button": "Конвертер", "clear_data_button": "Очистить данные",
                "donate_button": "Пожертвовать", "unpaid_bills": "Неоплаченные счета", "paid_bills": "Оплаченные счета", "credits": "сделано с <3 от Grouvya!",
                "pay_button": "Оплатить", "converter_window_title": "Конвертер валют", "from": "Из:", "to": "В:", "convert_button": "Конвертировать",
                "input_error": "Ошибка ввода", "valid_number_error": "Пожалуйста, введите правильное число для бюджета.", "budget_set": "Бюджет установлен",
                "budget_set_to": "Бюджет установлен на {}", "valid_currency_error": "Пожалуйста, выберите валюту.",
                "name_amount_error": "Пожалуйста, введите название и сумму.", "positive_amount_error": "Пожалуйста, введите положительную сумму.",
                "invalid_input": "Неверный ввод", "clear_data_confirm_title": "Очистить все данные",
                "clear_data_confirm_msg": "Вы уверены, что хотите удалить все счета и сбросить бюджет? Это действие нельзя отменить.",
                "data_cleared_title": "Данные очищены", "data_cleared_msg": "Все данные были успешно удалены.", "error": "Ошибка",
                "refresh_rates_button": "Обновить курсы", "settings_button": "Настройки", "settings_window_title": "Настройки",
                "api_key_label": "API-ключ ExchangeRate-API:", "save_key_button": "Сохранить ключ",
                "api_instructions": "Для получения курсов в реальном времени:\n1. Перейдите на www.exchangerate-api.com\n2. Зарегистрируйтесь на бесплатном тарифе.\n3. Найдите API-ключ в вашей панели управления.\n4. Скопируйте и вставьте его сюда.",
                "api_key_saved_title": "API-ключ сохранен", "api_key_saved_msg": "Ваш API-ключ успешно сохранен!",
                "api_key_missing": "API-ключ отсутствует. Перейдите в Настройки.", "rates_updated_at": "Курсы обновлены: {}",
                "api_error": "Ошибка API. Используются кэшированные курсы.", "network_error": "Ошибка сети. Используются кэшированные курсы.",
                "data_file_location": "Расположение файла данных:", "browse_button": "Обзор...", "path_saved_title": "Путь сохранен",
                "path_saved_msg": "Путь к файлу данных обновлен. Приложение будет использовать новый путь при следующем запуске.",
                "sort_by_name": "Сорт: Имя", "sort_by_date": "Сорт: Дата", "sort_by_amount": "Сорт: Сумма",
                "edit_bill_title": "Редактировать счет", "save_changes_button": "Сохранить изменения", "due_on": "Срок:", "no_date": "Без даты",
                "edit_button": "Ред.", "delete_button": "Удал.", "confirm_payment_title": "Подтверждение оплаты", "confirm_payment_msg": "Вы уверены, что хотите оплатить '{}'?",
                "confirm_delete_title": "Подтверждение удаления", "confirm_delete_msg": "Вы уверены, что хотите удалить '{}'?"
            },
            "German": {
                "window_title": "Rechnungs- & Spar-Tracker", "set_your_budget": "Legen Sie Ihr Budget fest:", "set_budget": "Budget festlegen",
                "add_bill": "Neue Rechnung hinzufügen", "bill_name": "Rechnungsname:", "amount": "Betrag:", "currency": "Währung:", "due_date": "Fälligkeitsdatum:",
                "add_bill_button": "Rechnung hinzufügen", "summarize_in": "Zusammenfassen in:", "total_unpaid": "Summe unbezahlter Rechnungen:",
                "budget_after_paying": "Budget nach Zahlung:", "converter_button": "Umrechner", "clear_data_button": "Daten löschen",
                "donate_button": "Spenden", "unpaid_bills": "Unbezahlte Rechnungen", "paid_bills": "Bezahlte Rechnungen", "credits": "gemacht mit <3 von Grouvya!",
                "pay_button": "Bezahlen", "converter_window_title": "Währungsrechner", "from": "Von:", "to": "Nach:", "convert_button": "Umrechnen",
                "input_error": "Eingabefehler", "valid_number_error": "Bitte geben Sie eine gültige Zahl für das Budget ein.", "budget_set": "Budget festgelegt",
                "budget_set_to": "Budget auf {} gesetzt", "valid_currency_error": "Bitte wählen Sie eine gültige Währung.",
                "name_amount_error": "Bitte geben Sie Name und Betrag ein.", "positive_amount_error": "Bitte geben Sie einen gültigen positiven Betrag ein.",
                "invalid_input": "Ungültige Eingabe", "clear_data_confirm_title": "Alle Daten löschen",
                "clear_data_confirm_msg": "Sind Sie sicher, dass Sie alle Rechnungen löschen und Ihr Budget zurücksetzen möchten? Diese Aktion kann nicht rückgängig gemacht werden.",
                "data_cleared_title": "Daten gelöscht", "data_cleared_msg": "Alle Daten wurden erfolgreich gelöscht.", "error": "Fehler",
                "refresh_rates_button": "Kurse aktualisieren", "settings_button": "Einstellungen", "settings_window_title": "Einstellungen",
                "api_key_label": "ExchangeRate-API-Schlüssel:", "save_key_button": "Schlüssel speichern",
                "api_instructions": "So erhalten Sie Echtzeit-Währungskurse:\n1. Gehen Sie zu www.exchangerate-api.com\n2. Melden Sie sich für den kostenlosen Plan an.\n3. Finden Sie den API-Schlüssel in Ihrem Dashboard.\n4. Kopieren Sie ihn und fügen Sie ihn hier ein.",
                "api_key_saved_title": "API-Schlüssel gespeichert", "api_key_saved_msg": "Ihr API-Schlüssel wurde erfolgreich gespeichert!",
                "api_key_missing": "API-Schlüssel fehlt. Gehen Sie zu den Einstellungen.", "rates_updated_at": "Live-Kurse aktualisiert: {}",
                "api_error": "API-Fehler. Zwischengespeicherte Kurse werden verwendet.", "network_error": "Netzwerkfehler. Zwischengespeicherte Kurse werden verwendet.",
                "data_file_location": "Speicherort der Datendatei:", "browse_button": "Durchsuchen...", "path_saved_title": "Pfad gespeichert",
                "path_saved_msg": "Der Pfad der Datendatei wurde aktualisiert. Die App wird diesen neuen Pfad beim nächsten Start verwenden.",
                "sort_by_name": "Sortieren: Name", "sort_by_date": "Sortieren: Datum", "sort_by_amount": "Sortieren: Betrag",
                "edit_bill_title": "Rechnung bearbeiten", "save_changes_button": "Änderungen speichern", "due_on": "Fällig:", "no_date": "Kein Datum",
                "edit_button": "Bearb.", "delete_button": "Lösch.", "confirm_payment_title": "Zahlung bestätigen", "confirm_payment_msg": "Möchten Sie '{}' wirklich bezahlen?",
                "confirm_delete_title": "Löschen bestätigen", "confirm_delete_msg": "Möchten Sie '{}' wirklich löschen?"
            },
            "Spanish": {
                "window_title": "Seguimiento de Facturas y Ahorros", "set_your_budget": "Establezca su presupuesto:", "set_budget": "Establecer presupuesto",
                "add_bill": "Añadir nueva factura", "bill_name": "Nombre de la factura:", "amount": "Monto:", "currency": "Moneda:", "due_date": "Fecha de vencimiento:",
                "add_bill_button": "Añadir factura", "summarize_in": "Resumir en:", "total_unpaid": "Total de facturas no pagadas:",
                "budget_after_paying": "Presupuesto después de pagar:", "converter_button": "Convertidor", "clear_data_button": "Borrar datos",
                "donate_button": "Donar", "unpaid_bills": "Facturas no pagadas", "paid_bills": "Facturas pagadas", "credits": "hecho con <3 por Grouvya!",
                "pay_button": "Pagar", "converter_window_title": "Convertidor de divisas", "from": "De:", "to": "A:", "convert_button": "Convertir",
                "input_error": "Error de entrada", "valid_number_error": "Por favor, ingrese un número válido para el presupuesto.", "budget_set": "Presupuesto establecido",
                "budget_set_to": "Presupuesto establecido en {}", "valid_currency_error": "Por favor, seleccione una moneda válida.",
                "name_amount_error": "Por favor, ingrese el nombre y el monto.", "positive_amount_error": "Por favor, ingrese un monto positivo válido.",
                "invalid_input": "Entrada no válida", "clear_data_confirm_title": "Borrar todos los datos",
                "clear_data_confirm_msg": "¿Está seguro de que desea eliminar todas las facturas y restablecer su presupuesto? Esta acción no se puede deshacer.",
                "data_cleared_title": "Datos borrados", "data_cleared_msg": "Todos los datos han sido borrados con éxito.", "error": "Error",
                "refresh_rates_button": "Actualizar tasas", "settings_button": "Ajustes", "settings_window_title": "Ajustes",
                "api_key_label": "Clave de API de ExchangeRate-API:", "save_key_button": "Guardar clave",
                "api_instructions": "Para obtener tasas de cambio en tiempo real:\n1. Vaya a www.exchangerate-api.com\n2. Regístrese en el plan gratuito.\n3. Encuentre la clave de API en su panel de control.\n4. Cópiela y péguela aquí.",
                "api_key_saved_title": "Clave de API guardada", "api_key_saved_msg": "¡Su clave de API se ha guardado correctamente!",
                "api_key_missing": "Falta la clave de API. Vaya a Ajustes.", "rates_updated_at": "Tasas actualizadas: {}",
                "api_error": "Error de API. Usando tasas en caché.", "network_error": "Error de red. Usando tasas en caché.",
                "data_file_location": "Ubicación del archivo de datos:", "browse_button": "Examinar...", "path_saved_title": "Ruta guardada",
                "path_saved_msg": "La ruta del archivo de datos ha sido actualizada. La aplicación usará esta nueva ruta en el próximo inicio.",
                "sort_by_name": "Ordenar: Nombre", "sort_by_date": "Ordenar: Fecha", "sort_by_amount": "Ordenar: Monto",
                "edit_bill_title": "Editar factura", "save_changes_button": "Guardar cambios", "due_on": "Vence:", "no_date": "Sin fecha",
                "edit_button": "Editar", "delete_button": "Elim.", "confirm_payment_title": "Confirmar pago", "confirm_payment_msg": "¿Seguro que quieres pagar '{}'?",
                "confirm_delete_title": "Confirmar eliminación", "confirm_delete_msg": "¿Seguro que quieres eliminar '{}'?"
            },
            "Italian": {
                "window_title": "Tracciatore di Bollette e Risparmi", "set_your_budget": "Imposta il tuo budget:", "set_budget": "Imposta Budget",
                "add_bill": "Aggiungi una nuova bolletta", "bill_name": "Nome bolletta:", "amount": "Importo:", "currency": "Valuta:", "due_date": "Data di scadenza:",
                "add_bill_button": "Aggiungi Bolletta", "summarize_in": "Riassumi in:", "total_unpaid": "Totale bollette non pagate:",
                "budget_after_paying": "Budget dopo i pagamenti:", "converter_button": "Convertitore", "clear_data_button": "Cancella Dati",
                "donate_button": "Dona", "unpaid_bills": "Bollette non pagate", "paid_bills": "Bollette pagate", "credits": "fatto con <3 da Grouvya!",
                "pay_button": "Paga", "converter_window_title": "Convertitore di valuta", "from": "Da:", "to": "A:", "convert_button": "Converti",
                "input_error": "Errore di inserimento", "valid_number_error": "Inserisci un numero valido per il budget.", "budget_set": "Budget impostato",
                "budget_set_to": "Budget impostato a {}", "valid_currency_error": "Seleziona una valuta valida.",
                "name_amount_error": "Inserisci sia il nome che l'importo.", "positive_amount_error": "Inserisci un importo positivo valido.",
                "invalid_input": "Input non valido", "clear_data_confirm_title": "Cancella tutti i dati",
                "clear_data_confirm_msg": "Sei sicuro di voler eliminare tutte le bollette e reimpostare il budget? Questa azione non può essere annullata.",
                "data_cleared_title": "Dati cancellati", "data_cleared_msg": "Tutti i dati sono stati cancellati con successo.", "error": "Errore",
                "refresh_rates_button": "Aggiorna Tassi", "settings_button": "Impostazioni", "settings_window_title": "Impostazioni",
                "api_key_label": "Chiave API ExchangeRate-API:", "save_key_button": "Salva Chiave",
                "api_instructions": "Per ottenere tassi di cambio in tempo reale:\n1. Vai su www.exchangerate-api.com\n2. Iscriviti al piano gratuito.\n3. Trova la chiave API nella tua dashboard.\n4. Copiala e incollala qui.",
                "api_key_saved_title": "Chiave API salvata", "api_key_saved_msg": "La tua chiave API è stata salvata con successo!",
                "api_key_missing": "Chiave API mancante. Vai alle Impostazioni.", "rates_updated_at": "Tassi aggiornati: {}",
                "api_error": "Errore API. Utilizzo tassi memorizzati.", "network_error": "Errore di rete. Utilizzo tassi memorizzati.",
                "data_file_location": "Posizione file dati:", "browse_button": "Sfoglia...", "path_saved_title": "Percorso salvato",
                "path_saved_msg": "Il percorso del file dati è stato aggiornato. L'app utilizzerà questo nuovo percorso al prossimo avvio.",
                "sort_by_name": "Ordina: Nome", "sort_by_date": "Ordina: Data", "sort_by_amount": "Ordina: Importo",
                "edit_bill_title": "Modifica Bolletta", "save_changes_button": "Salva Modifiche", "due_on": "Scad.:", "no_date": "Nessuna data",
                "edit_button": "Mod.", "delete_button": "Elim.", "confirm_payment_title": "Conferma Pagamento", "confirm_payment_msg": "Sei sicuro di voler pagare '{}'?",
                "confirm_delete_title": "Conferma Eliminazione", "confirm_delete_msg": "Sei sicuro di voler eliminare '{}'?"
            },
            "French": {
                "window_title": "Suivi des Factures et Épargnes", "set_your_budget": "Définissez votre budget :", "set_budget": "Définir le budget",
                "add_bill": "Ajouter une nouvelle facture", "bill_name": "Nom de la facture :", "amount": "Montant :", "currency": "Devise :", "due_date": "Date d'échéance :",
                "add_bill_button": "Ajouter la facture", "summarize_in": "Résumer en :", "total_unpaid": "Total des factures impayées :",
                "budget_after_paying": "Budget après paiement :", "converter_button": "Convertisseur", "clear_data_button": "Effacer les données",
                "donate_button": "Faire un don", "unpaid_bills": "Factures impayées", "paid_bills": "Factures payées", "credits": "fait avec <3 par Grouvya !",
                "pay_button": "Payer", "converter_window_title": "Convertisseur de devises", "from": "De :", "to": "À :", "convert_button": "Convertir",
                "input_error": "Erreur de saisie", "valid_number_error": "Veuillez entrer un nombre valide pour le budget.", "budget_set": "Budget défini",
                "budget_set_to": "Budget défini à {}", "valid_currency_error": "Veuillez sélectionner une devise valide.",
                "name_amount_error": "Veuillez entrer un nom et un montant.", "positive_amount_error": "Veuillez entrer un montant positif valide.",
                "invalid_input": "Saisie invalide", "clear_data_confirm_title": "Effacer toutes les données",
                "clear_data_confirm_msg": "Êtes-vous sûr de vouloir supprimer toutes les factures et réinitialiser votre budget ? Cette action est irréversible.",
                "data_cleared_title": "Données effacées", "data_cleared_msg": "Toutes les données ont été effacées avec succès.", "error": "Erreur",
                "refresh_rates_button": "Actualiser les taux", "settings_button": "Paramètres", "settings_window_title": "Paramètres",
                "api_key_label": "Clé API ExchangeRate-API :", "save_key_button": "Enregistrer la clé",
                "api_instructions": "Pour obtenir les taux de change en temps réel :\n1. Allez sur www.exchangerate-api.com\n2. Inscrivez-vous au plan gratuit.\n3. Trouvez la clé API dans votre tableau de bord.\n4. Copiez-la et collez-la ici.",
                "api_key_saved_title": "Clé API enregistrée", "api_key_saved_msg": "Votre clé API a été enregistrée avec succès !",
                "api_key_missing": "Clé API manquante. Allez dans les Paramètres.", "rates_updated_at": "Taux mis à jour : {}",
                "api_error": "Erreur API. Utilisation des taux en cache.", "network_error": "Erreur réseau. Utilisation des taux en cache.",
                "data_file_location": "Emplacement du fichier de données :", "browse_button": "Parcourir...", "path_saved_title": "Chemin enregistré",
                "path_saved_msg": "Le chemin du fichier de données a été mis à jour. L'application utilisera ce nouveau chemin au prochain lancement.",
                "sort_by_name": "Trier : Nom", "sort_by_date": "Trier : Date", "sort_by_amount": "Trier : Montant",
                "edit_bill_title": "Modifier la facture", "save_changes_button": "Enregistrer les modifications", "due_on": "Échéance :", "no_date": "Pas de date",
                "edit_button": "Modif.", "delete_button": "Suppr.", "confirm_payment_title": "Confirmer le paiement", "confirm_payment_msg": "Voulez-vous vraiment payer '{}' ?",
                "confirm_delete_title": "Confirmer la suppression", "confirm_delete_msg": "Voulez-vous vraiment supprimer '{}' ?"
            },
            "Dutch": {
                "window_title": "Rekening & Besparingen Tracker", "set_your_budget": "Stel uw budget in:", "set_budget": "Budget instellen",
                "add_bill": "Nieuwe rekening toevoegen", "bill_name": "Naam rekening:", "amount": "Bedrag:", "currency": "Valuta:", "due_date": "Vervaldatum:",
                "add_bill_button": "Rekening toevoegen", "summarize_in": "Samenvatten in:", "total_unpaid": "Totaal onbetaalde rekeningen:",
                "budget_after_paying": "Budget na betaling:", "converter_button": "Omzetter", "clear_data_button": "Gegevens wissen",
                "donate_button": "Doneren", "unpaid_bills": "Onbetaalde rekeningen", "paid_bills": "Betaalde rekeningen", "credits": "gemaakt met <3 door Grouvya!",
                "pay_button": "Betalen", "converter_window_title": "Valuta-omzetter", "from": "Van:", "to": "Naar:", "convert_button": "Omzetten",
                "input_error": "Invoerfout", "valid_number_error": "Voer een geldig getal in voor het budget.", "budget_set": "Budget ingesteld",
                "budget_set_to": "Budget ingesteld op {}", "valid_currency_error": "Selecteer een geldige valuta.",
                "name_amount_error": "Voer zowel naam als bedrag in.", "positive_amount_error": "Voer een geldig positief bedrag in.",
                "invalid_input": "Ongeldige invoer", "clear_data_confirm_title": "Alle gegevens wissen",
                "clear_data_confirm_msg": "Weet u zeker dat u alle rekeningen wilt verwijderen en uw budget wilt resetten? Deze actie kan niet ongedaan worden gemaakt.",
                "data_cleared_title": "Gegevens gewist", "data_cleared_msg": "Alle gegevens zijn succesvol gewist.", "error": "Fout",
                "refresh_rates_button": "Tarieven vernieuwen", "settings_button": "Instellingen", "settings_window_title": "Instellingen",
                "api_key_label": "ExchangeRate-API-sleutel:", "save_key_button": "Sleutel opslaan",
                "api_instructions": "Om realtime valutakoersen te krijgen:\n1. Ga naar www.exchangerate-api.com\n2. Meld u aan voor het gratis abonnement.\n3. Zoek de API-sleutel in uw dashboard.\n4. Kopieer en plak deze hier.",
                "api_key_saved_title": "API-sleutel opgeslagen", "api_key_saved_msg": "Uw API-sleutel is succesvol opgeslagen!",
                "api_key_missing": "API-sleutel ontbreekt. Ga naar Instellingen.", "rates_updated_at": "Live tarieven bijgewerkt: {}",
                "api_error": "API-fout. Gecachte tarieven worden gebruikt.", "network_error": "Netwerkfout. Gecachte tarieven worden gebruikt.",
                "data_file_location": "Locatie gegevensbestand:", "browse_button": "Bladeren...", "path_saved_title": "Pad opgeslagen",
                "path_saved_msg": "Het pad van het gegevensbestand is bijgewerkt. De app zal dit nieuwe pad gebruiken bij de volgende start.",
                "sort_by_name": "Sorteren: Naam", "sort_by_date": "Sorteren: Datum", "sort_by_amount": "Sorteren: Bedrag",
                "edit_bill_title": "Rekening bewerken", "save_changes_button": "Wijzigingen opslaan", "due_on": "Vervalt:", "no_date": "Geen datum",
                "edit_button": "Bewerk", "delete_button": "Verw.", "confirm_payment_title": "Betaling bevestigen", "confirm_payment_msg": "Weet je zeker dat je '{}' wilt betalen?",
                "confirm_delete_title": "Verwijderen bevestigen", "confirm_delete_msg": "Weet je zeker dat je '{}' wilt verwijderen?"
            },
            "Chinese": {
                "window_title": "账单与储蓄追踪器", "set_your_budget": "设置您的预算：", "set_budget": "设置预算",
                "add_bill": "添加新账单", "bill_name": "账单名称：", "amount": "金额：", "currency": "货币：", "due_date": "截止日期：",
                "add_bill_button": "添加账单", "summarize_in": "汇总货币：", "total_unpaid": "未付账单总额：",
                "budget_after_paying": "支付后预算：", "converter_button": "转换器", "clear_data_button": "清除数据",
                "donate_button": "捐赠", "unpaid_bills": "未付账单", "paid_bills": "已付账单", "credits": "由 Grouvya 用 <3 制作！",
                "pay_button": "支付", "converter_window_title": "货币转换器", "from": "从：", "to": "到：", "convert_button": "转换",
                "input_error": "输入错误", "valid_number_error": "请输入有效的预算金额。", "budget_set": "预算已设置",
                "budget_set_to": "预算设置为 {}", "valid_currency_error": "请选择有效的货币。",
                "name_amount_error": "请输入名称和金额。", "positive_amount_error": "请输入有效的正数金额。",
                "invalid_input": "输入无效", "clear_data_confirm_title": "清除所有数据",
                "clear_data_confirm_msg": "您确定要删除所有账单并重置预算吗？此操作无法撤销。",
                "data_cleared_title": "数据已清除", "data_cleared_msg": "所有数据已成功清除。", "error": "错误",
                "refresh_rates_button": "刷新汇率", "settings_button": "设置", "settings_window_title": "设置",
                "api_key_label": "ExchangeRate-API 密钥：", "save_key_button": "保存密钥",
                "api_instructions": "要获取实时货币汇率：\n1. 前往 www.exchangerate-api.com\n2. 注册免费计划。\n3. 在您的仪表板中找到 API 密钥。\n4. 复制并粘贴到此处。",
                "api_key_saved_title": "API 密钥已保存", "api_key_saved_msg": "您的 API 密钥已成功保存！",
                "api_key_missing": "缺少 API 密钥。请前往设置。", "rates_updated_at": "实时汇率更新于：{}",
                "api_error": "API 错误。正在使用缓存汇率。", "network_error": "网络错误。正在使用缓存汇率。",
                "data_file_location": "数据文件位置：", "browse_button": "浏览...", "path_saved_title": "路径已保存",
                "path_saved_msg": "数据文件路径已更新。应用程序将在下次启动时使用此新路径。",
                "sort_by_name": "排序：名称", "sort_by_date": "排序：日期", "sort_by_amount": "排序：金额",
                "edit_bill_title": "编辑账单", "save_changes_button": "保存更改", "due_on": "截止：", "no_date": "无日期",
                "edit_button": "编辑", "delete_button": "删除", "confirm_payment_title": "确认支付", "confirm_payment_msg": "您确定要支付“{}”吗？",
                "confirm_delete_title": "确认删除", "confirm_delete_msg": "您确定要删除“{}”吗？"
            }
        }

if __name__ == "__main__":
    root = tk.Tk()
    app = BillTrackerApp(root)
    root.mainloop()
