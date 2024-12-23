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

        self.save_option_button = tk.Button(self, text="Save Results", command=self.export_results)
        self.save_option_button.pack(pady=10)
        self.save_option_button.config(state=tk.DISABLED)

        self.display_option_button = tk.Button(self, text="Display Results", command=self.display_results)
        self.display_option_button.pack(pady=10)
        self.display_option_button.config(state=tk.DISABLED)

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
            self.save_option_button.config(state=tk.NORMAL)
            self.display_option_button.config(state=tk.NORMAL)

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
        # Clear previous filter widgets
        for widget in self.headings_frame.winfo_children():
            widget.destroy()

        # Create a new frame to hold canvas and scrollbar
        if not hasattr(self, 'canvas_frame'):
            self.canvas_frame = tk.Frame(self)
            self.canvas_frame.pack(fill="both", expand=True)

            # Create a canvas for scrollable area
            self.canvas = tk.Canvas(self.canvas_frame, height=300)  # Set desired height for scrollable area
            self.canvas.pack(side="left", fill="both", expand=True)

            # Add a vertical scrollbar to the canvas
            self.scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
            self.scrollbar.pack(side="right", fill="y")

            # Configure the canvas to work with the scrollbar
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            # Create the headings_frame inside the canvas
            self.headings_frame = tk.Frame(self.canvas)
            self.canvas.create_window((0, 0), window=self.headings_frame, anchor="nw")

            # Update scroll region when the frame is resized
            self.headings_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Add label and filters
        tk.Label(self.headings_frame, text="Select headings and set filters:", anchor='w').pack(fill='x')

        for heading in self.headings:
            frame = tk.Frame(self.headings_frame)
            frame.pack(fill="x", pady=2)

            label = tk.Label(frame, text=heading, width=20, anchor='w')
            label.pack(side="left")

            col_type = self.column_types.get(heading, 'string')
            condition_var = tk.StringVar(value="Any")
            condition_menu = ttk.Combobox(frame, textvariable=condition_var, values=["Any", "Equals", "Not Equal To", "Contains", "Less Than", "More Than", "Starts With", "Ends With"])
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
        if condition.get() == "Any":
            return True
        if condition.get() == "Equals":
            return str(value) == str(filter_value)
        elif condition.get() == "Contains":
            return filter_value in str(value)
        elif condition.get() == "Less Than":
            return float(value) < float(filter_value)
        elif condition.get() == "More Than":
            return float(value) > float(filter_value)
        elif condition.get() == "Starts With":
            return str(value).startswith(filter_value)
        elif condition.get() == "Ends With":
            return str(value).endswith(filter_value)
        elif condition.get() == "Not Equal To":
            return str(value) != str(filter_value)

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
            # Apply sorting if a sort field is selected
            sort_field = self.sort_field_var.get()  # Reference the variable defined in display_results
            sort_order = self.sort_order_var.get()  # Reference the variable defined in display_results
            if sort_field:
                is_numeric = self.column_types.get(sort_field) in ['int', 'float']
                reverse = sort_order == "Descending"
                self.filtered_data.sort(key=lambda x: float(x[sort_field]) if is_numeric and x[sort_field] else x[sort_field], reverse=reverse)

            # Export filtered and sorted data
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


    def display_results(self):
        display_window = tk.Toplevel(self)
        display_window.title("Select Fields to Display")
        display_window.geometry("400x500")

        # Create a canvas for scrollable area
        canvas = tk.Canvas(display_window)
        canvas.pack(side="left", fill="both", expand=True)

        # Add a vertical scrollbar to the canvas
        scrollbar = tk.Scrollbar(display_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the canvas to work with the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # Update scroll region when the frame is resized
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Dictionary to store the selection state of each field
        field_vars = {}
        for heading in self.headings:
            var = tk.BooleanVar(value=False)  # Set default value to False (unchecked)
            chk = tk.Checkbutton(frame, text=heading, variable=var)
            chk.pack(anchor='w')
            field_vars[heading] = var

        # Function to tick all fields
        def tick_all():
            for var in field_vars.values():
                var.set(True)

        # Function to untick all fields
        def tick_none():
            for var in field_vars.values():
                var.set(False)

        # Add Tick All and Tick None buttons
        tick_all_button = tk.Button(display_window, text="Tick All", command=tick_all)
        tick_all_button.pack(pady=5)

        tick_none_button = tk.Button(display_window, text="Tick None", command=tick_none)
        tick_none_button.pack(pady=5)

        # Sorting options
        tk.Label(display_window, text="Sort By:").pack(pady=5)
        sort_field_var = tk.StringVar(value="")
        sort_order_var = tk.StringVar(value="Ascending")

        sort_field_menu = ttk.Combobox(display_window, textvariable=sort_field_var, values=[""] + self.headings, state="readonly")
        sort_field_menu.pack()

        sort_order_menu = ttk.Combobox(display_window, textvariable=sort_order_var, values=["Ascending", "Descending"], state="readonly")
        sort_order_menu.pack()

        # Display button to show the results with the selected fields and sorting
        display_button = tk.Button(display_window, text="Display", command=lambda: self.show_results(field_vars, sort_field_var.get(), sort_order_var.get()))
        display_button.pack(pady=10)



    def show_results(self, field_vars, sort_field, sort_order):
        selected_fields = [field for field, var in field_vars.items() if var.get()]

        result_window = tk.Toplevel(self)
        result_window.title("Filtered Results")

        if not self.filtered_data:
            messagebox.showinfo("Display Results", "No results to display.")
            return

        # Apply sorting if a sort field is selected
        if sort_field:
            is_numeric = self.column_types.get(sort_field) in ['int', 'float']
            reverse = sort_order == "Descending"
            self.filtered_data.sort(key=lambda x: float(x[sort_field]) if is_numeric and x[sort_field] else x[sort_field], reverse=reverse)

        columns = selected_fields
        results = [{k: v for k, v in row.items() if k in selected_fields} for row in self.filtered_data]

        table_frame = tk.Frame(result_window)
        table_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='w')

        for row in results:
            tree.insert("", "end", values=[row[col] for col in columns])

        tree.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = FilterApp()
    app.mainloop()