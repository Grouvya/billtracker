import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

import sys
import json
import os
from datetime import datetime, date
import threading
import webbrowser
import urllib.request
import urllib.error

# Centralized dictionary for all user-facing strings
STRINGS = {
    "app_title": "Bill & Savings Tracker",
    "budget_group_title": "Set Your Budget",
    "budget_row_title": "Budget Amount",
    "set_budget_button": "Set Budget",
    "add_bill_group_title": "Add a New Bill",
    "bill_name_row": "Bill Name",
    "amount_row": "Amount",
    "due_date_row": "Due Date",
    "add_bill_button": "Add Bill",
    "summarize_in_label": "Summarize in:",
    "total_unpaid_label": "Total of Unpaid Bills:",
    "budget_after_paying_label": "Budget After Paying Bills:",
    "actions_group_title": "Actions",
    "converter_button": "Converter",
    "clear_data_button": "Clear Data",
    "donate_button": "Donate",
    "refresh_rates_button": "Refresh Rates",
    "settings_button": "Settings",
    "unpaid_bills_title": "Unpaid Bills",
    "sort_name_button": "Name",
    "sort_date_button": "Date",
    "sort_amount_button": "Amount",
    "paid_bills_title": "Paid Bills",
    "credits_label": "made with <3 by Grouvya!",
    "pay_button": "Pay",
    "due_on_label": "Due:",
    "no_date_label": "No Date",
    "edit_bill_title": "Edit Bill",
    "bill_name_label": "Bill Name",
    "amount_label": "Amount",
    "currency_label": "Currency",
    "due_date_label": "Due Date",
    "save_changes_button": "Save Changes",
    "converter_title": "Currency Converter",
    "from_label": "From",
    "to_label": "To",
    "convert_button": "Convert",
    "settings_title": "Settings",
    "api_key_group_title": "ExchangeRate-API Key",
    "api_instructions": "To get real-time currency rates, sign up for the free plan on exchangerate-api.com, find the API key in your dashboard, and paste it below.",
    "api_key_row_title": "ExchangeRate-API Key",
    "save_key_button": "Save Key",
    "data_file_group_title": "Data File Location",
    "browse_button": "Browse...",
    "dialog_input_error": "Input Error",
    "error_enter_name_amount": "Please enter both name and amount.",
    "error_positive_amount": "Please enter a valid positive amount.",
    "error_no_exchange_rate": "Could not find exchange rate.",
    "error_valid_number": "Please enter a valid number for the budget.",
    "info_budget_set": "Budget Set",
    "info_budget_set_to": "Budget set to {}",
    "info_api_key_saved": "API Key Saved",
    "info_api_key_saved_msg": "Your API key has been saved successfully!",
    "info_path_saved": "Path Saved",
    "info_path_saved_msg": "Data file path has been updated.",
    "info_data_cleared": "Data Cleared",
    "info_data_cleared_msg": "All data has been cleared.",
    "dialog_confirm_payment": "Confirm Payment",
    "confirm_payment_msg": "Are you sure you want to pay '{}'?",
    "dialog_confirm_delete": "Confirm Delete",
    "confirm_delete_msg": "Are you sure you want to delete '{}'?",
    "dialog_clear_data": "Clear All Data",
    "confirm_clear_data_msg": "Are you sure you want to delete all bills and reset your budget?",
    "invalid_input": "Invalid Input",
    "api_key_missing": "API key missing. Go to Settings.",
    "api_error": "API error. Using cached rates.",
    "network_error": "Network error. Using cached rates.",
    "rates_updated_at": "Live rates updated: {}",
}

# -- Data and API Management Classes --

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
                self.show_error_dialog("Error", f"Could not read data file: {e}")
                return {}
        return {}

    def save_data(self, data_to_save):
        """Saves all bill and budget data."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            self.show_error_dialog("Error", f"Could not write to data file: {e}")

    def show_error_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=None, modal=True, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title,
            secondary_text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()


class APIManager:
    """Handles all external API calls for exchange rates."""
    def __init__(self, api_key, result_callback):
        self.api_key = api_key
        self.result_callback = result_callback

    def fetch_rates_async(self):
        """Fetches exchange rates in a background thread."""
        thread = threading.Thread(target=self._execute_fetch)
        thread.daemon = True
        thread.start()

    def _execute_fetch(self):
        if not self.api_key:
            GLib.idle_add(self.result_callback, {'status': 'error', 'message': STRINGS["api_key_missing"]})
            return
        url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status != 200:
                    raise urllib.error.HTTPError(url, response.status, "HTTP Status not 200", response.headers, response)
                content = response.read().decode('utf-8')
                data = json.loads(content)
                if data.get("result") == "success":
                    GLib.idle_add(self.result_callback, {'status': 'success', 'data': data})
                else:
                    GLib.idle_add(self.result_callback, {'status': 'error', 'message': STRINGS["api_error"]})
        except (urllib.error.URLError, json.JSONDecodeError):
            GLib.idle_add(self.result_callback, {'status': 'error', 'message': STRINGS["network_error"]})


# -- GTK Windows --

class BillEditorWindow(Gtk.Window):
    def __init__(self, parent, bill, currencies, save_callback):
        super().__init__(transient_for=parent, modal=True)
        self.bill = bill
        self.currencies = currencies
        self.save_callback = save_callback

        self.set_title(STRINGS["edit_bill_title"])
        self.set_default_size(350, 400)
        self.set_resizable(False)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=15, margin_bottom=15, margin_start=15, margin_end=15)
        self.set_child(main_box)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["bill_name_label"]}</b>', use_markup=True, xalign=0))
        self.name_entry = Gtk.Entry(text=bill['name'])
        main_box.append(self.name_entry)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["amount_label"]}</b>', use_markup=True, xalign=0))
        self.amount_entry = Gtk.Entry(text=str(bill['amount']))
        main_box.append(self.amount_entry)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["currency_label"]}</b>', use_markup=True, xalign=0))
        self.currency_dropdown = Gtk.DropDown.new_from_strings(list(self.currencies.keys()))
        try:
            currency_index = list(self.currencies.keys()).index(bill['currency'])
            self.currency_dropdown.set_selected(currency_index)
        except ValueError:
            self.currency_dropdown.set_selected(0)
        main_box.append(self.currency_dropdown)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["due_date_label"]}</b>', use_markup=True, xalign=0))
        
        self.calendar = Gtk.Calendar()
        self.date_popover = Gtk.Popover(child=self.calendar)
        self.date_button = Gtk.Button(label=bill.get('due_date', date.today().strftime('%Y-%m-%d')))
        self.date_popover.set_parent(self.date_button)
        self.date_button.connect("clicked", self.on_date_button_clicked)
        
        initial_date = datetime.strptime(bill.get('due_date', date.today().strftime('%Y-%m-%d')), '%Y-%m-%d')
        self.calendar.select_day(GLib.DateTime.new_local(initial_date.year, initial_date.month, initial_date.day, 0, 0, 0))
        self.calendar.connect("day-selected", self.on_date_selected)
        main_box.append(self.date_button)

        save_button = Gtk.Button(label=STRINGS["save_changes_button"])
        save_button.add_css_class("suggested-action")
        save_button.set_margin_top(10)
        save_button.connect("clicked", self.on_save_clicked)
        main_box.append(save_button)
        
    def on_date_button_clicked(self, button):
        self.date_popover.popup()

    def on_date_selected(self, calendar):
        gdatetime = calendar.get_date()
        self.date_button.set_label(gdatetime.format("%Y-%m-%d"))
        self.date_popover.popdown()

    def on_save_clicked(self, button):
        new_name = self.name_entry.get_text().strip()
        new_amount_str = self.amount_entry.get_text()
        if not new_name or not new_amount_str:
            self.show_error(STRINGS["error_enter_name_amount"])
            return
        try:
            new_amount = float(new_amount_str)
            if new_amount <= 0: raise ValueError
        except ValueError:
            self.show_error(STRINGS["error_positive_amount"])
            return
        updated_bill = self.bill.copy()
        updated_bill['name'] = new_name
        updated_bill['amount'] = new_amount
        updated_bill['currency'] = self.currency_dropdown.get_selected_item().get_string()
        updated_bill['due_date'] = self.date_button.get_label()
        self.save_callback(self.bill, updated_bill)
        self.destroy()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=STRINGS["dialog_input_error"],
            secondary_text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()


class ConverterWindow(Gtk.Window):
    def __init__(self, parent, currencies, exchange_rates):
        super().__init__(transient_for=parent, modal=True)
        self.currencies = currencies
        self.exchange_rates = exchange_rates

        self.set_title(STRINGS["converter_title"])
        self.set_default_size(350, 400)
        self.set_resizable(False)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=15, margin_bottom=15, margin_start=15, margin_end=15)
        self.set_child(main_box)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["amount_label"]}</b>', use_markup=True, xalign=0))
        self.amount_entry = Gtk.Entry(placeholder_text="100.00")
        main_box.append(self.amount_entry)
        
        main_box.append(Gtk.Label(label=f'<b>{STRINGS["from_label"]}</b>', use_markup=True, xalign=0))
        self.from_dropdown = Gtk.DropDown.new_from_strings(list(self.currencies.keys()))
        self.from_dropdown.set_selected(list(self.currencies.keys()).index('$ (USD)'))
        main_box.append(self.from_dropdown)

        main_box.append(Gtk.Label(label=f'<b>{STRINGS["to_label"]}</b>', use_markup=True, xalign=0))
        self.to_dropdown = Gtk.DropDown.new_from_strings(list(self.currencies.keys()))
        self.to_dropdown.set_selected(list(self.currencies.keys()).index('€ (EUR)'))
        main_box.append(self.to_dropdown)

        self.result_label = Gtk.Label(label="")
        self.result_label.add_css_class("title-1")
        main_box.append(self.result_label)
        
        convert_button = Gtk.Button(label=STRINGS["convert_button"])
        convert_button.add_css_class("suggested-action")
        convert_button.set_margin_top(10)
        convert_button.connect("clicked", self.perform_conversion)
        main_box.append(convert_button)
        
    def perform_conversion(self, button):
        try:
            amount = float(self.amount_entry.get_text().replace(',', ''))
            from_curr = self.from_dropdown.get_selected_item().get_string()
            to_curr = self.to_dropdown.get_selected_item().get_string()
            
            from_rate_vs_usd = self.exchange_rates.get(from_curr)
            to_rate_vs_usd = self.exchange_rates.get(to_curr)

            if not from_rate_vs_usd or not to_rate_vs_usd:
                raise KeyError

            amount_in_usd = amount / from_rate_vs_usd
            converted_amount = amount_in_usd * to_rate_vs_usd

            to_symbol = self.currencies.get(to_curr, "")
            self.result_label.set_text(f"{to_symbol}{converted_amount:,.2f}")
        except (ValueError, KeyError):
            self.result_label.set_text(STRINGS["invalid_input"])


class SettingsWindow(Adw.PreferencesWindow):
    def __init__(self, parent):
        super().__init__(transient_for=parent, modal=True)
        self.main_window = parent
        
        self.set_title(STRINGS["settings_title"])
        self.set_default_size(500, 450)
        
        page = Adw.PreferencesPage()
        self.add(page)

        # --- API Key Group ---
        api_group = Adw.PreferencesGroup(title=STRINGS["api_key_group_title"])
        page.add(api_group)

        instructions = Gtk.Label(label=STRINGS["api_instructions"], wrap=True, xalign=0)
        api_group.add(instructions)

        link = Gtk.LinkButton(uri="https://www.exchangerate-api.com", label="www.exchangerate-api.com")
        api_group.add(link)

        self.api_key_entry = Adw.PasswordEntryRow(title=STRINGS["api_key_row_title"])
        self.api_key_entry.set_text(parent.api_key)
        api_group.add(self.api_key_entry)

        save_key_button = Gtk.Button(label=STRINGS["save_key_button"])
        save_key_button.add_css_class("suggested-action")
        save_key_button.set_halign(Gtk.Align.CENTER)
        save_key_button.connect("clicked", self.on_save_key_clicked)
        api_group.add(save_key_button)

        # --- Data File Group ---
        data_group = Adw.PreferencesGroup(title=STRINGS["data_file_group_title"])
        page.add(data_group)

        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.path_entry = Gtk.Entry(text=parent.data_manager.data_file, editable=False, hexpand=True)
        path_box.append(self.path_entry)
        browse_button = Gtk.Button(label=STRINGS["browse_button"])
        browse_button.connect("clicked", self.on_browse_clicked)
        path_box.append(browse_button)

        path_row = Adw.ActionRow(child=path_box)
        data_group.add(path_row)

    def on_save_key_clicked(self, button):
        new_key = self.api_key_entry.get_text()
        self.main_window.api_key = new_key
        self.main_window.api_manager.api_key = new_key
        
        config = self.main_window.data_manager.load_config()
        config['api_key'] = new_key
        self.main_window.data_manager.save_config(config)
        
        self.main_window.api_manager.fetch_rates_async()
        self.main_window.show_info_dialog(STRINGS["info_api_key_saved"], STRINGS["info_api_key_saved_msg"])
        self.destroy()

    def on_browse_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Choose a data file location",
            transient_for=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.ACCEPT)
        dialog.set_current_name("bill_data.json")

        def on_response(d, response_id):
            if response_id == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                new_path = file.get_path()
                self.path_entry.set_text(new_path)
                self.main_window.data_manager.data_file = new_path
                config = self.main_window.data_manager.load_config()
                config['data_file_path'] = new_path
                self.main_window.data_manager.save_config(config)
                self.main_window.save_data()
                self.main_window.show_info_dialog(STRINGS["info_path_saved"], STRINGS["info_path_saved_msg"])
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()


# -- GTK Main Application Window --

class BillTrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(STRINGS["app_title"])
        self.set_default_size(600, 800)
        self.set_icon_name("com.github.grouvya.billtracker")

        config_dir = os.path.join(os.path.expanduser('~'), '.bill_tracker')
        self.data_manager = DataManager(config_dir)
        config = self.data_manager.load_config()
        self.api_key = config.get('api_key', "")
        self.api_manager = APIManager(self.api_key, self.handle_api_result)

        self.currencies = self.get_currency_list()
        self.full_currency_list = list(self.currencies.keys())
        self.exchange_rates = {}

        self.unpaid_bills = []
        self.paid_bills = []
        self.budget = 0.0
        self.load_data()

        self.create_widgets()
        
        self.api_manager.fetch_rates_async()
        self.update_summary()
        self.update_bills_display()
        self.update_budget_display()

        self.connect("close-request", self.on_closing)

    def create_widgets(self):
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Adw.WindowTitle.new(STRINGS["app_title"], ""))
        self.set_titlebar(self.header)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        scrolled_window = Gtk.ScrolledWindow(child=main_box)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(scrolled_window)

        self.budget_frame = Adw.PreferencesGroup(title=STRINGS["budget_group_title"])
        main_box.append(self.budget_frame)
        budget_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.budget_entry = Gtk.Entry()
        self.budget_entry.set_hexpand(True)
        budget_box.append(self.budget_entry)
        self.budget_currency_dropdown = Gtk.DropDown.new_from_strings(self.full_currency_list)
        budget_box.append(self.budget_currency_dropdown)
        budget_row = Adw.ActionRow(title=STRINGS["budget_row_title"], child=budget_box)
        self.budget_frame.add(budget_row)
        self.set_budget_button = Gtk.Button(label=STRINGS["set_budget_button"])
        self.set_budget_button.connect("clicked", self.set_budget)
        main_box.append(self.set_budget_button)

        self.add_bill_frame = Adw.PreferencesGroup(title=STRINGS["add_bill_group_title"])
        main_box.append(self.add_bill_frame)
        self.bill_name_entry = Adw.EntryRow(title=STRINGS["bill_name_row"])
        self.add_bill_frame.add(self.bill_name_entry)
        amount_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bill_amount_entry = Gtk.Entry(hexpand=True)
        amount_box.append(self.bill_amount_entry)
        self.bill_currency_dropdown = Gtk.DropDown.new_from_strings(self.full_currency_list)
        amount_box.append(self.bill_currency_dropdown)
        self.amount_row = Adw.ActionRow(title=STRINGS["amount_row"], child=amount_box)
        self.add_bill_frame.add(self.amount_row)
        self.due_date_calendar = Gtk.Calendar()
        self.due_date_popover = Gtk.Popover(child=self.due_date_calendar)
        self.due_date_button = Gtk.Button(label=date.today().strftime('%Y-%m-%d'))
        self.due_date_popover.set_parent(self.due_date_button)
        self.due_date_button.connect("clicked", self.on_due_date_button_clicked)
        self.due_date_calendar.connect("day-selected", self.on_due_date_selected)
        self.date_row = Adw.ActionRow(title=STRINGS["due_date_row"], child=self.due_date_button)
        self.add_bill_frame.add(self.date_row)
        self.add_bill_button = Gtk.Button(label=STRINGS["add_bill_button"])
        self.add_bill_button.add_css_class("suggested-action")
        self.add_bill_button.connect("clicked", self.add_bill)
        main_box.append(self.add_bill_button)

        summary_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin_top=15, margin_bottom=15)
        main_box.append(summary_frame)
        summary_currency_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.CENTER)
        summary_currency_box.append(Gtk.Label(label=STRINGS["summarize_in_label"]))
        self.summary_currency_dropdown = Gtk.DropDown.new_from_strings(self.full_currency_list)
        summary_currency_box.append(self.summary_currency_dropdown)
        summary_frame.append(summary_currency_box)
        self.total_to_pay_label = Gtk.Label()
        summary_frame.append(self.total_to_pay_label)
        self.remaining_budget_label = Gtk.Label()
        self.remaining_budget_label.add_css_class("title-2")
        summary_frame.append(self.remaining_budget_label)
        self.budget_progressbar = Gtk.ProgressBar(show_text=True)
        summary_frame.append(self.budget_progressbar)
        self.rates_status_label = Gtk.Label()
        self.rates_status_label.add_css_class("caption")
        summary_frame.append(self.rates_status_label)
        
        actions_frame = Adw.PreferencesGroup(title=STRINGS["actions_group_title"])
        main_box.append(actions_frame)
        button_box = Gtk.FlowBox(valign=Gtk.Align.START, max_children_per_line=3, min_children_per_line=2, selection_mode=Gtk.SelectionMode.NONE)
        actions_frame.add(Adw.ActionRow(child=button_box))
        
        converter_button = Gtk.Button(label=STRINGS["converter_button"])
        converter_button.connect("clicked", self.open_converter_window)
        button_box.append(converter_button)
        
        clear_data_button = Gtk.Button(label=STRINGS["clear_data_button"])
        clear_data_button.add_css_class("destructive-action")
        clear_data_button.connect("clicked", self.clear_data)
        button_box.append(clear_data_button)
        
        donate_button = Gtk.Button(label=STRINGS["donate_button"])
        donate_button.connect("clicked", self.open_donate_link)
        button_box.append(donate_button)
        
        refresh_rates_button = Gtk.Button(label=STRINGS["refresh_rates_button"])
        refresh_rates_button.connect("clicked", lambda b: self.api_manager.fetch_rates_async())
        button_box.append(refresh_rates_button)

        settings_button = Gtk.Button(label=STRINGS["settings_button"], icon_name="document-properties-symbolic")
        settings_button.connect("clicked", self.open_settings_window)
        button_box.append(settings_button)

        main_box.append(Gtk.Separator(margin_top=10, margin_bottom=10))
        unpaid_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, margin_bottom=6)
        main_box.append(unpaid_header)
        unpaid_bills_label = Gtk.Label(label=f'<b>{STRINGS["unpaid_bills_title"]}</b>', use_markup=True, xalign=0, hexpand=True)
        unpaid_bills_label.add_css_class("title-2")
        unpaid_header.append(unpaid_bills_label)

        sort_box = Gtk.Box(spacing=6)
        unpaid_header.append(sort_box)
        sort_name_button = Gtk.Button(label=STRINGS["sort_name_button"])
        sort_name_button.connect("clicked", self.sort_bills_by_name)
        sort_box.append(sort_name_button)
        sort_date_button = Gtk.Button(label=STRINGS["sort_date_button"])
        sort_date_button.connect("clicked", self.sort_bills_by_date)
        sort_box.append(sort_date_button)
        sort_amount_button = Gtk.Button(label=STRINGS["sort_amount_button"])
        sort_amount_button.connect("clicked", self.sort_bills_by_amount)
        sort_box.append(sort_amount_button)

        self.unpaid_bills_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.append(self.unpaid_bills_box)
        
        main_box.append(Gtk.Separator(margin_top=10, margin_bottom=10))
        paid_bills_label = Gtk.Label(label=f'<b>{STRINGS["paid_bills_title"]}</b>', use_markup=True, xalign=0)
        paid_bills_label.add_css_class("title-2")
        main_box.append(paid_bills_label)
        self.paid_bills_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.append(self.paid_bills_box)

        credits_link = Gtk.LinkButton(uri="https://guns.lol/grouvya", label=STRINGS["credits_label"], halign=Gtk.Align.CENTER)
        main_box.append(credits_link)

        self.budget_currency_dropdown.connect("notify::selected-item", self.update_budget_display)
        self.summary_currency_dropdown.connect("notify::selected-item", self.on_currency_change)
        try:
            self.budget_currency_dropdown.set_selected(self.full_currency_list.index(self.saved_budget_currency))
            self.bill_currency_dropdown.set_selected(self.full_currency_list.index(self.saved_bill_currency))
            self.summary_currency_dropdown.set_selected(self.full_currency_list.index(self.saved_summary_currency))
        except ValueError:
            pass

    def on_due_date_button_clicked(self, button):
        self.due_date_popover.popup()
        
    def on_due_date_selected(self, calendar):
        gdatetime = calendar.get_date()
        self.due_date_button.set_label(gdatetime.format("%Y-%m-%d"))
        self.due_date_popover.popdown()

    def open_settings_window(self, button):
        win = SettingsWindow(self)
        win.present()
        
    def open_converter_window(self, button):
        win = ConverterWindow(self, self.currencies, self.exchange_rates)
        win.present()

    def open_donate_link(self, button):
        webbrowser.open_new("https://revolut.me/grouvya")

    def clear_data(self, button):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO, text=STRINGS["dialog_clear_data"],
            secondary_text=STRINGS["confirm_clear_data_msg"]
        )
        def on_response(d, response_id):
            d.destroy()
            if response_id == Gtk.ResponseType.YES:
                self.unpaid_bills, self.paid_bills, self.budget = [], [], 0.0
                self.update_budget_display()
                self.update_summary()
                self.update_bills_display()
                self.save_data()
                self.show_info_dialog(STRINGS["info_data_cleared"], STRINGS["info_data_cleared_msg"])
        dialog.connect("response", on_response)
        dialog.present()
    
    def sort_bills_by_name(self, button):
        self.unpaid_bills.sort(key=lambda b: b['name'].lower())
        self.update_bills_display()

    def sort_bills_by_date(self, button):
        self.unpaid_bills.sort(key=lambda b: datetime.strptime(b.get('due_date', '9999-12-31'), '%Y-%m-%d'))
        self.update_bills_display()

    def sort_bills_by_amount(self, button):
        def get_usd_amount(bill):
            rate = self.exchange_rates.get(bill['currency'], 1)
            return bill['amount'] / rate if rate > 0 else float('inf')
        self.unpaid_bills.sort(key=get_usd_amount, reverse=True)
        self.update_bills_display()

    def load_data(self):
        data = self.data_manager.load_data()
        self.unpaid_bills = data.get('unpaid_bills', [])
        self.paid_bills = data.get('paid_bills', [])
        self.budget = float(data.get('budget', 0.0))
        default_currency = '$ (USD)'
        self.saved_budget_currency = data.get('budget_currency', default_currency)
        self.saved_bill_currency = data.get('bill_currency', default_currency)
        self.saved_summary_currency = data.get('summary_currency', default_currency)

    def save_data(self):
        data = {
            'budget': self.budget,
            'budget_currency': self.budget_currency_dropdown.get_selected_item().get_string(),
            'unpaid_bills': self.unpaid_bills, 'paid_bills': self.paid_bills,
            'bill_currency': self.bill_currency_dropdown.get_selected_item().get_string(),
            'summary_currency': self.summary_currency_dropdown.get_selected_item().get_string()
        }
        self.data_manager.save_data(data)

    def handle_api_result(self, result):
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
            self.rates_status_label.set_text(STRINGS["rates_updated_at"].format(now))
        else:
            self.rates_status_label.set_text(result['message'])
        self.update_budget_display()
        self.update_summary()

    def set_budget(self, button=None):
        try:
            displayed_amount = float(self.budget_entry.get_text().replace(',', ''))
            budget_curr = self.budget_currency_dropdown.get_selected_item().get_string()
            rate = self.exchange_rates.get(budget_curr)
            if not rate or rate <= 0:
                self.show_error_dialog('Error', STRINGS["error_no_exchange_rate"])
                return
            self.budget = displayed_amount / rate
            self.update_summary()
            formatted_amount = f"{self.currencies.get(budget_curr, '')}{displayed_amount:,.2f}"
            self.show_info_dialog(STRINGS["info_budget_set"], STRINGS["info_budget_set_to"].format(formatted_amount))
        except ValueError:
            self.show_error_dialog(STRINGS["dialog_input_error"], STRINGS["error_valid_number"])

    def add_bill(self, button=None):
        name = self.bill_name_entry.get_text().strip()
        amount_str = self.bill_amount_entry.get_text()
        currency = self.bill_currency_dropdown.get_selected_item().get_string()
        due_date = self.due_date_button.get_label()
        if not name or not amount_str:
            self.show_error_dialog(STRINGS["dialog_input_error"], STRINGS["error_enter_name_amount"])
            return
        try:
            amount = float(amount_str.replace(',', ''))
            if amount <= 0: raise ValueError
        except ValueError:
            self.show_error_dialog(STRINGS["dialog_input_error"], STRINGS["error_positive_amount"])
            return
        bill = {"name": name, "amount": amount, "currency": currency, "due_date": due_date}
        self.unpaid_bills.append(bill)
        self.bill_name_entry.set_text("")
        self.bill_amount_entry.set_text("")
        self.update_summary()
        self.update_bills_display()

    def pay_bill(self, bill_to_pay):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO, text=STRINGS["dialog_confirm_payment"],
            secondary_text=STRINGS["confirm_payment_msg"].format(bill_to_pay['name'])
        )
        def on_response(d, response_id):
            d.destroy()
            if response_id == Gtk.ResponseType.YES:
                rate_vs_usd = self.exchange_rates.get(bill_to_pay['currency'])
                if rate_vs_usd and rate_vs_usd > 0:
                    self.budget -= bill_to_pay['amount'] / rate_vs_usd
                    self.update_budget_display()
                self.unpaid_bills.remove(bill_to_pay)
                self.paid_bills.append(bill_to_pay)
                self.update_summary()
                self.update_bills_display()
        dialog.connect("response", on_response)
        dialog.present()

    def delete_bill(self, bill_to_delete):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO, text=STRINGS["dialog_confirm_delete"],
            secondary_text=STRINGS["confirm_delete_msg"].format(bill_to_delete['name'])
        )
        def on_response(d, response_id):
            d.destroy()
            if response_id == Gtk.ResponseType.YES:
                if bill_to_delete in self.unpaid_bills: self.unpaid_bills.remove(bill_to_delete)
                elif bill_to_delete in self.paid_bills: self.paid_bills.remove(bill_to_delete)
                self.update_summary()
                self.update_bills_display()
        dialog.connect("response", on_response)
        dialog.present()

    def edit_bill(self, bill_to_edit):
        editor = BillEditorWindow(self, bill_to_edit, self.currencies, self.handle_bill_edited)
        editor.present()

    def handle_bill_edited(self, original_bill, updated_bill):
        try:
            index = self.unpaid_bills.index(original_bill)
            self.unpaid_bills[index] = updated_bill
            self.update_summary()
            self.update_bills_display()
        except ValueError:
            print("Could not find original bill to update.")

    def on_currency_change(self, dropdown, param):
        self.update_summary()

    def update_budget_display(self, dropdown=None, param=None):
        budget_curr = self.budget_currency_dropdown.get_selected_item().get_string()
        rate = self.exchange_rates.get(budget_curr)
        if rate and rate > 0:
            self.budget_entry.set_text(f"{self.budget * rate:,.2f}")
        else:
            self.budget_entry.set_text(f"{self.budget:,.2f}")

    def update_summary(self):
        summary_curr_str = self.summary_currency_dropdown.get_selected_item().get_string()
        summary_symbol = self.currencies.get(summary_curr_str, '$')
        target_rate = self.exchange_rates.get(summary_curr_str)
        if not target_rate: return
        total_to_pay_usd = sum(b['amount'] / self.exchange_rates.get(b['currency'], 1) for b in self.unpaid_bills if self.exchange_rates.get(b['currency']))
        remaining_budget_usd = self.budget - total_to_pay_usd
        final_to_pay = total_to_pay_usd * target_rate
        remaining_budget_display = remaining_budget_usd * target_rate
        self.total_to_pay_label.set_text(f'{STRINGS["total_unpaid_label"]} {summary_symbol}{final_to_pay:,.2f}')
        self.remaining_budget_label.set_text(f'{STRINGS["budget_after_paying_label"]} {summary_symbol}{remaining_budget_display:,.2f}')
        for css_class in ["success", "warning", "error"]:
             self.budget_progressbar.remove_css_class(css_class)
             self.remaining_budget_label.remove_css_class(css_class)
        if self.budget > 0:
            percentage = (remaining_budget_usd / self.budget)
            self.budget_progressbar.set_fraction(max(0, percentage))
            self.budget_progressbar.set_text(f"{max(0, percentage):.0%}")
            if percentage < 0.25:
                self.budget_progressbar.add_css_class("error")
                self.remaining_budget_label.add_css_class("error")
            elif percentage < 0.50:
                self.budget_progressbar.add_css_class("warning")
                self.remaining_budget_label.add_css_class("warning")
            else:
                self.budget_progressbar.add_css_class("success")
                self.remaining_budget_label.add_css_class("success")
        else:
            self.budget_progressbar.set_fraction(0)
            self.budget_progressbar.set_text("0%")

    def update_bills_display(self):
        for box in [self.unpaid_bills_box, self.paid_bills_box]:
            child = box.get_first_child()
            while child:
                box.remove(child)
                child = box.get_first_child()
        for bill in self.unpaid_bills:
            symbol = self.currencies.get(bill['currency'], '$')
            due_date_str = bill.get('due_date', STRINGS["no_date_label"])
            row = Adw.ActionRow(title=bill['name'], subtitle=f'{symbol}{bill["amount"]:.2f} — {STRINGS["due_on_label"]} {due_date_str}')
            try:
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date_obj < date.today(): row.add_css_class("error")
            except (ValueError, TypeError): pass

            button_box = Gtk.Box(spacing=6)
            row.add_suffix(button_box)

            pay_button = Gtk.Button(label=STRINGS["pay_button"])
            pay_button.add_css_class("pill")
            pay_button.set_valign(Gtk.Align.CENTER)
            pay_button.connect("clicked", lambda b, bill_ref=bill: self.pay_bill(bill_ref))
            button_box.append(pay_button)

            edit_button = Gtk.Button(icon_name="document-edit-symbolic")
            edit_button.connect("clicked", lambda b, bill_ref=bill: self.edit_bill(bill_ref))
            button_box.append(edit_button)

            delete_button = Gtk.Button(icon_name="user-trash-symbolic")
            delete_button.add_css_class("destructive-action")
            delete_button.connect("clicked", lambda b, bill_ref=bill: self.delete_bill(bill_ref))
            button_box.append(delete_button)
            
            self.unpaid_bills_box.append(row)
        for bill in self.paid_bills:
            symbol = self.currencies.get(bill['currency'], '$')
            row = Adw.ActionRow(title=bill['name'], subtitle=f"{symbol}{bill['amount']:.2f}", activatable=False)
            row.add_css_class("dim-label")
            self.paid_bills_box.append(row)
    
    def on_closing(self, window):
        self.save_data()
        return False

    def show_error_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title, secondary_text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()

    def show_info_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title, secondary_text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()

    def get_currency_list(self):
        return { '؋ (AFN)': '؋', 'Lek (ALL)': 'Lek', 'դր. (AMD)': 'դր.', 'ƒ (ANG)': 'ƒ', 'Kz (AOA)': 'Kz', '$ (ARS)': '$', 'A$ (AUD)': 'A$', 'ƒ (AWG)': 'ƒ', '₼ (AZN)': '₼', 'KM (BAM)': 'KM', '$ (BBD)': '$', '৳ (BDT)': '৳', 'лв (BGN)': 'лв', '.د.ب (BHD)': '.د.ب', 'FBu (BIF)': 'FBu', '$ (BMD)': '$', '$ (BND)': '$', 'Bs. (BOB)': 'Bs.', 'R$ (BRL)': 'R$', '$ (BSD)': '$', 'Nu. (BTN)': 'Nu.', 'P (BWP)': 'P', 'Br (BYN)': 'Br', '$ (BZD)': '$', 'C$ (CAD)': 'C$', 'Fr (CDF)': 'Fr', 'Fr (CHF)': 'Fr', '$ (CLP)': '$', '¥ (CNY)': '¥', '$ (COP)': '$', '₡ (CRC)': '₡', '$ (CUP)': 'CUP', '$ (CVE)': '$', 'Kč (CZK)': 'Kč', 'Fdj (DJF)': 'Fdj', 'kr (DKK)': 'kr', 'RD$ (DOP)': 'RD$', 'DA (DZD)': 'DA', 'E£ (EGP)': 'E£', 'Nfk (ERN)': 'Nfk', 'Br (ETB)': 'Br', '€ (EUR)': '€', '$ (FJD)': '$', '£ (FKP)': '£', '£ (GBP)': '£', '₾ (GEL)': '₾', '£ (GGP)': '£', 'GH₵ (GHS)': 'GH₵', '£ (GIP)': '£', 'D (GMD)': 'D', 'Fr (GNF)': 'Fr', 'Q (GTQ)': 'Q', '$ (GYD)': '$', 'HK$ (HKD)': 'HK$', 'L (HNL)': 'L', 'kn (HRK)': 'kn', 'G (HTG)': 'G', 'Ft (HUF)': 'Ft', 'Rp (IDR)': 'Rp', '₪ (ILS)': '₪', '£ (IMP)': '£', '₹ (INR)': '₹', 'ع.د (IQD)': 'ع.د', '﷼ (IRR)': '﷼', 'kr (ISK)': 'kr', '£ (JEP)': '£', '$ (JMD)': '$', 'JD (JOD)': 'JD', '¥ (JPY)': '¥', 'KSh (KES)': 'KSh', 'лв (KGS)': 'лв', '៛ (KHR)': '៛', 'Fr (KMF)': 'Fr', '₩ (KPW)': '₩', '₩ (KRW)': '₩', 'KD (KWD)': 'KD', '$ (KYD)': '$', '〒 (KZT)': '〒', '₭ (LAK)': '₭', 'ل.ل (LBP)': 'ل.ل', '₨ (LKR)': '₨', '$ (LRD)': '$', 'L (LSL)': 'L', 'LTL (LTL)': 'LTL', 'Ls (LVL)': 'Ls', 'ل.د (LYD)': 'ل.د', 'د.م. (MAD)': 'د.მ.', 'L (MDL)': 'L', 'Ar (MGA)': 'Ar', 'ден (MKD)': 'ден', 'K (MMK)': 'K', '₮ (MNT)': '₮', 'P (MOP)': 'P', 'UM (MRO)': 'UM', '₨ (MUR)': '₨', 'Rf (MVR)': 'Rf', 'MK (MWK)': 'MK', '$ (MXN)': '$', 'RM (MYR)': 'RM', 'MTn (MZN)': 'MTn', 'N$ (NAD)': 'N$', '₦ (NGN)': '₦', 'C$ (NIO)': 'C$', 'kr (NOK)': 'kr', '₨ (NPR)': '₨', 'NZ$ (NZD)': 'NZ$', '﷼ (OMR)': '﷼', 'B/. (PAB)': 'B/.', 'S/. (PEN)': 'S/.', 'K (PGK)': 'K', '₱ (PHP)': '₱', '₨ (PKR)': '₨', 'zł (PLN)': 'zł', '₲ (PYG)': '₲', '﷼ (QAR)': '﷼', 'lei (RON)': 'lei', 'din (RSD)': 'din', '₽ (RUB)': '₽', 'FRw (RWF)': 'FRw', '﷼ (SAR)': '﷼', '$ (SBD)': '$', '₨ (SCR)': '₨', 'ج.س. (SDG)': 'ج.س.', 'kr (SEK)': 'kr', 'S$ (SGD)': 'S$', '£ (SHP)': '£', 'Le (SLL)': 'Le', 'S (SOS)': 'S', '$ (SRD)': '$', 'Db (STD)': 'Db', '$ (SVC)': '$', '£S (SYP)': '£S', 'L (SZL)': 'L', '฿ (THB)': '฿', 'ЅМ (TJS)': 'ЅМ', 'T (TMT)': 'T', 'د.ت (TND)': 'د.ت', 'T$ (TOP)': 'T$', '₺ (TRY)': '₺', 'TT$ (TTD)': 'TT$', 'NT$ (TWD)': 'NT$', 'TSh (TZS)': 'TSh', '₴ (UAH)': '₴', 'USh (UGX)': 'USh', '$ (USD)': '$', '$U (UYU)': '$U', 'soʻm (UZS)': 'soʻm', 'Bs (VEF)': 'Bs', '₫ (VND)': '₫', 'Vt (VUV)': 'Vt', 'T (WST)': 'T', 'Fr (XAF)': 'Fr', '$ (XCD)': '$', 'Fr (XOF)': 'Fr', 'Fr (XPF)': 'Fr', '﷼ (YER)': '﷼', 'R (ZAR)': 'R', 'ZK (ZMW)': 'ZK', 'Z$ (ZWL)': 'Z$' }


# -- Application Class to manage the lifecycle --

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = BillTrackerWindow(application=app)
        self.win.present()

if __name__ == "__main__":
    app = MyApp(application_id="com.github.grouvya.billtracker")
    app.run(sys.argv)
