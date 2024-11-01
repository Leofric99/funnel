import json
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tabulate import tabulate

class FilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Data Filter Application")
        self.geometry("800x600")

        self.file_path = ""
        self.data = None
        self.headings = []
        self.column_types = {}
        self.filters = []
        self.filtered_data = []

        self.create_widgets()
    
    def create_widgets(self):
        self.file_label = tk.Label(self, text="No file selected", anchor='w')
        self.file_label.pack(pady=10, fill='x')

        self.load_button = tk.Button(self, text="Load File", command=self.load_file)
        self.load_button.pack(pady=10)

        self.headings_frame = tk.Frame(self)
        self.headings_frame.pack(pady=10, fill='x')

        self.filters_frame = tk.Frame(self)
        self.filters_frame.pack(pady=10, fill='x')

        self.results_label = tk.Label(self, text="Results: 0", anchor='w')
        self.results_label.pack(pady=10, fill='x')

        self.apply_button = tk.Button(self, text="Export Results", command=self.export_results)
        self.apply_button.pack(pady=10)
        self.apply_button.config(state=tk.DISABLED)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")])
        if file_path:
            self.file_path = file_path
            self.file_label.config(text=f"Loaded file: {file_path}")
            self.headings = self.get_headings(file_path)
            self.column_types = self.identify_column_types(file_path, self.headings)
            self.load_data(file_path)
            self.build_headings_menu()
            self.results_label.config(text=f"Results: {len(self.data)}")
            self.apply_button.config(state=tk.NORMAL)

    def get_headings(self, file_path):
        if file_path.endswith('.json'):
            with open(file_path, 'r') as file:
                data = json.load(file)
                if isinstance(data, list) and len(data) > 0:
                    return list(data[0].keys())
                elif isinstance(data, dict):
                    return list(data.keys())
        elif file_path.endswith('.csv'):
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                return next(reader)
        else:
            raise ValueError("Unsupported file format. Please provide a .json or .csv file.")
        return []

    def identify_column_types(self, file_path, headings):
        column_types = {}
        if file_path.endswith('.json'):
            with open(file_path, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    for heading in headings:
                        column_data = [row[heading] for row in data if heading in row]
                        column_types[heading] = self.identify_type(column_data)
                elif isinstance(data, dict):
                    for heading in headings:
                        column_data = data.get(heading, [])
                        column_types[heading] = self.identify_type(column_data)
        elif file_path.endswith('.csv'):
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)
                for heading in headings:
                    column_data = [row[heading] for row in reader if heading in row]
                    column_types[heading] = self.identify_type(column_data)
        else:
            raise ValueError("Unsupported file format. Please provide a .json or .csv file.")
        return column_types

    def identify_type(self, column_data):
        if all(isinstance(item, str) for item in column_data):
            return 'string'
        elif all(isinstance(item, (int, float)) for item in column_data):
            if all(isinstance(item, int) for item in column_data):
                return 'int'
            elif all(isinstance(item, float) for item in column_data):
                return 'float'
        else:
            return 'string'

    def load_data(self, file_path):
        if file_path.endswith('.json'):
            with open(file_path, 'r') as file:
                self.data = json.load(file)
        elif file_path.endswith('.csv'):
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)
                self.data = [row for row in reader]
        else:
            raise ValueError("Unsupported file format. Please provide a .json or .csv file.")

    def build_headings_menu(self):
        for widget in self.headings_frame.winfo_children():
            widget.destroy()

        tk.Label(self.headings_frame, text="Select headings and set filters:", anchor='w').pack(fill='x')

        for heading in self.headings:
            frame = tk.Frame(self.headings_frame)
            frame.pack(fill="x", pady=2)

            label = tk.Label(frame, text=heading, width=20, anchor='w')
            label.pack(side="left")

            col_type = self.column_types.get(heading, 'string')
            condition_var = tk.StringVar(value="any")
            condition_menu = ttk.Combobox(frame, textvariable=condition_var, values=["any", "equals", "contains", "less than", "more than", "starts with", "ends with"])
            condition_menu.pack(side="left")
            condition_menu.bind("<<ComboboxSelected>>", lambda event, h=heading, var=condition_var: self.update_filter_condition(h, var))

            if col_type in ['int', 'float']:
                min_val, max_val = self.get_min_max_values(heading)
                slider = tk.Scale(frame, from_=min_val, to=max_val, orient="horizontal", command=lambda v, h=heading: self.update_filter_value(h, v))
                slider.pack(side="left", fill="x", expand=True)
                self.filters.append({'heading': heading, 'type': col_type, 'value': 0, 'condition': condition_var, 'widget': slider})
            else:
                entry = tk.Entry(frame, justify='left')
                entry.pack(side="left", fill="x", expand=True)
                entry.bind("<KeyRelease>", lambda event, h=heading: self.update_filter_value(h, event.widget.get()))
                self.filters.append({'heading': heading, 'type': col_type, 'value': '', 'condition': condition_var, 'widget': entry})

    def get_min_max_values(self, heading):
        values = [float(row[heading]) for row in self.data if heading in row and row[heading] != ""]
        return min(values), max(values)

    def update_filter_value(self, heading, value):
        for f in self.filters:
            if f['heading'] == heading:
                f['value'] = value
                break
        self.apply_filters()

    def update_filter_condition(self, heading, condition_var):
        for f in self.filters:
            if f['heading'] == heading:
                f['condition'] = condition_var
                break
        self.apply_filters()

    def match_filter(self, value, filter_type, filter_value, condition):
        if condition.get() == "any":
            return True
        if condition.get() == "equals":
            return str(value) == str(filter_value)
        elif condition.get() == "contains":
            return filter_value in str(value)
        elif condition.get() == "less than":
            return float(value) < float(filter_value)
        elif condition.get() == "more than":
            return float(value) > float(filter_value)
        elif condition.get() == "starts with":
            return str(value).startswith(filter_value)
        elif condition.get() == "ends with":
            return str(value).endswith(filter_value)
        return False

    def apply_filters(self):
        if not self.file_path:
            return

        if self.file_path.endswith('.json'):
            self.filtered_data = [row for row in self.data if all(self.match_filter(row.get(f['heading']), f['type'], f['value'], f['condition']) for f in self.filters)]
        elif self.file_path.endswith('.csv'):
            self.filtered_data = [row for row in self.data if all(self.match_filter(row.get(f['heading']), f['type'], f['value'], f['condition']) for f in self.filters)]
        else:
            raise ValueError("Unsupported file format. Please provide a .json or .csv file.")

        self.results_label.config(text=f"Results: {len(self.filtered_data)}")

    def export_results(self):
        output_file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")])
        if output_file_path:
            if output_file_path.endswith('.json'):
                with open(output_file_path, 'w') as file:
                    json.dump(self.filtered_data, file, indent=4)
            elif output_file_path.endswith('.csv'):
                if len(self.filtered_data) > 0:
                    with open(output_file_path, 'w', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=self.filtered_data[0].keys())
                        writer.writeheader()
                        writer.writerows(self.filtered_data)
            messagebox.showinfo("Export Results", f"Filtered results saved to '{output_file_path}'")

if __name__ == "__main__":
    app = FilterApp()
    app.mainloop()