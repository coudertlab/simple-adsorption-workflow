import ctypes.wintypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
import json
import os
import pandas as pd

class JSONFormApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Form GUI")

        # Define font styles
        self.title_font = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.label_font = tkFont.Font(family="Helvetica", size=8)
        self.button_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.note_font = tkFont.Font(family="Helvetica", size=6)

        self.create_widgets()

    def create_widgets(self):
        # Create a Notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create frames for each tab
        self.parameters_frame = ttk.Frame(notebook)
        self.defaults_frame = ttk.Frame(notebook)

        notebook.add(self.parameters_frame, text='Parameters')
        notebook.add(self.defaults_frame, text='Advanced Configurations')

        # Create content for Parameters Tab
        self.create_parameters_tab()

        # Create content for Advanced Configurations Tab
        self.create_defaults_tab()

        # Save Button (placed below the notebook)
        save_button = tk.Button(self.root, text="Save to JSON", command=self.save_to_json, bg='green', fg='white', font=self.button_font)
        save_button.pack(pady=10)

    def create_parameters_tab(self):
        # Scrollable Frame within Parameters Tab
        parameters_canvas = tk.Canvas(self.parameters_frame)
        parameters_scrollbar = ttk.Scrollbar(self.parameters_frame, orient="vertical", command=parameters_canvas.yview)
        parameters_scrollable_frame = ttk.Frame(parameters_canvas)

        parameters_scrollable_frame.bind(
            "<Configure>",
            lambda e: parameters_canvas.configure(
                scrollregion=parameters_canvas.bbox("all")
            )
        )

        parameters_canvas.create_window((0, 0), window=parameters_scrollable_frame, anchor="nw")
        parameters_canvas.configure(yscrollcommand=parameters_scrollbar.set)

        parameters_canvas.pack(side="left", fill="both", expand=True)
        parameters_scrollbar.pack(side="right", fill="y")

        # Load refcodes from file
        try:
            package_dir = os.environ.get("PACKAGE_DIR", ".")  # Default to current directory if not set
            refcodes_path = os.path.join(package_dir, "parameters", "mofdb-version_dc8a0295db.txt")
            with open(refcodes_path, 'r') as file:
                self.refcodes = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"The file '{refcodes_path}' was not found.")
            self.refcodes = []

        # Structures
        structures_label = ttk.Label(parameters_scrollable_frame, text="Structures:", font=self.title_font)
        structures_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)

        self.structures_listbox = tk.Listbox(parameters_scrollable_frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        for item in self.refcodes:
            self.structures_listbox.insert(tk.END, item)
        self.structures_listbox.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        # Adsorbed gas molecules
        molecule_label = ttk.Label(parameters_scrollable_frame, text="Adsorbed Gas Molecules:", font=self.title_font)
        molecule_label.grid(row=2, column=0, sticky='w', padx=5, pady=5)

        # Load molecule options from CSV
        try:
            molecules_csv_path = os.path.join(package_dir, "parameters", "molecules.csv")
            molecules_df = pd.read_csv(molecules_csv_path)
            self.molecule_options = molecules_df["MOLECULE"].dropna().tolist()
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"The file '{molecules_csv_path}' was not found.")
            self.molecule_options = []
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading '{molecules_csv_path}':\n{e}")
            self.molecule_options = []

        self.molecule_listbox = tk.Listbox(parameters_scrollable_frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        for item in self.molecule_options:
            self.molecule_listbox.insert(tk.END, item)
        # Pre-select "CO2" and "N2" if they exist
        for molecule in ["CO2", "N2"]:
            if molecule in self.molecule_options:
                index = self.molecule_options.index(molecule)
                self.molecule_listbox.selection_set(index)
        self.molecule_listbox.grid(row=3, column=0, padx=5, pady=5, sticky='nsew')

        # Pressure Inputs
        pressure_label = ttk.Label(parameters_scrollable_frame, text="Pressure:", font=self.title_font)
        pressure_label.grid(row=4, column=0, sticky='w', padx=5, pady=5)

        pressure_frame = ttk.Frame(parameters_scrollable_frame)
        pressure_frame.grid(row=5, column=0, padx=20, pady=5, sticky='w')

        ttk.Label(pressure_frame, text="Min:", width=10).grid(row=0, column=0, padx=5, pady=2, sticky='e')
        self.pmin_entry = ttk.Entry(pressure_frame, width=20)
        self.pmin_entry.insert(0, "10")
        self.pmin_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(pressure_frame, text="Max:", width=10).grid(row=1, column=0, padx=5, pady=2, sticky='e')
        self.pmax_entry = ttk.Entry(pressure_frame, width=20)
        self.pmax_entry.insert(0, "1000000")
        self.pmax_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(pressure_frame, text="Steps:", width=10).grid(row=2, column=0, padx=5, pady=2, sticky='e')
        self.psteps_entry = ttk.Entry(pressure_frame, width=20)
        self.psteps_entry.insert(0, "8")
        self.psteps_entry.grid(row=2, column=1, padx=5, pady=2)

        # Temperatures
        temp_label = ttk.Label(parameters_scrollable_frame, text="Temperatures:", font=self.title_font)
        temp_label.grid(row=6, column=0, sticky='w', padx=5, pady=5)
        temp_label = ttk.Label(parameters_scrollable_frame, text="note : separate with comma for multiple values", font=self.note_font)
        temp_label.grid(row=7, column=0, sticky='w', padx=5, pady=5)
        self.temp_entry = ttk.Entry(parameters_scrollable_frame, width=40)
        self.temp_entry.insert(0, "298.15")
        self.temp_entry.grid(row=8, column=0, padx=5, pady=5, sticky='w')

        # Charge methods
        charge_label = ttk.Label(parameters_scrollable_frame, text="Charge Methods:", font=self.title_font)
        charge_label.grid(row=9, column=0, sticky='w', padx=5, pady=5)

        self.charge_options = ['EQeq', 'None']
        self.charge_listbox = tk.Listbox(parameters_scrollable_frame, selectmode=tk.MULTIPLE, height=2, exportselection=False)
        for item in self.charge_options:
            self.charge_listbox.insert(tk.END, item)
        # Pre-select 'EQeq' and 'None' if available
        for idx in range(len(self.charge_options)):
            self.charge_listbox.selection_set(idx)
        self.charge_listbox.grid(row=10, column=0, padx=5, pady=5, sticky='nsew')

        # Configure grid weights
        parameters_scrollable_frame.columnconfigure(0, weight=1)

    def create_defaults_tab(self):
        # Scrollable Frame within Defaults Tab
        defaults_canvas = tk.Canvas(self.defaults_frame)
        defaults_scrollbar = ttk.Scrollbar(self.defaults_frame, orient="vertical", command=defaults_canvas.yview)
        defaults_scrollable_frame = ttk.Frame(defaults_canvas)

        defaults_scrollable_frame.bind(
            "<Configure>",
            lambda e: defaults_canvas.configure(
                scrollregion=defaults_canvas.bbox("all")
            )
        )

        defaults_canvas.create_window((0, 0), window=defaults_scrollable_frame, anchor="nw")
        defaults_canvas.configure(yscrollcommand=defaults_scrollbar.set)

        defaults_canvas.pack(side="left", fill="both", expand=True)
        defaults_scrollbar.pack(side="right", fill="y")

        # Advanced Configurations Label
        advanced_label = ttk.Label(defaults_scrollable_frame, text="Advanced Configurations (Expert Users):", font=self.label_font)
        advanced_label.grid(row=0, column=0, sticky='w', padx=5, pady=10)

        # Forcefield
        forcefield_label = ttk.Label(defaults_scrollable_frame, text="Force Field:", font=self.title_font)
        forcefield_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.forcefield_var = tk.StringVar()
        self.forcefield_combobox = ttk.Combobox(
            defaults_scrollable_frame,
            textvariable=self.forcefield_var,
            values=['ExampleMOFsForceField', 'no other on register'],
            state='readonly',
            width=30
        )
        self.forcefield_combobox.current(0)
        self.forcefield_combobox.grid(row=2, column=0, padx=5, pady=5, sticky='w')

        # Init Cycles
        init_cycles_label = ttk.Label(defaults_scrollable_frame, text="Init Cycles:", font=self.title_font)
        init_cycles_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.init_cycles_entry = ttk.Entry(defaults_scrollable_frame, width=30)
        self.init_cycles_entry.insert(0, "20000")
        self.init_cycles_entry.grid(row=4, column=0, padx=5, pady=5, sticky='w')

        # Cycles
        cycles_label = ttk.Label(defaults_scrollable_frame, text="Cycles:", font=self.title_font)
        cycles_label.grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.cycles_entry = ttk.Entry(defaults_scrollable_frame, width=30)
        self.cycles_entry.insert(0, "10000")
        self.cycles_entry.grid(row=6, column=0, padx=5, pady=5, sticky='w')

        # Print Every
        print_every_label = ttk.Label(defaults_scrollable_frame, text="Print Every:", font=self.title_font)
        print_every_label.grid(row=7, column=0, sticky='w', padx=5, pady=5)
        self.print_every_entry = ttk.Entry(defaults_scrollable_frame, width=30)
        self.print_every_entry.insert(0, "500")
        self.print_every_entry.grid(row=8, column=0, padx=5, pady=5, sticky='w')

        # Use Grid
        grid_use_label = ttk.Label(defaults_scrollable_frame, text="Use Grid?", font=self.title_font)
        grid_use_label.grid(row=9, column=0, sticky='w', padx=5, pady=5)
        self.grid_use_var = tk.StringVar()
        self.grid_use_combobox = ttk.Combobox(
            defaults_scrollable_frame,
            textvariable=self.grid_use_var,
            values=['yes', 'no'],
            state='readonly',
            width=28
        )
        self.grid_use_combobox.current(1)  # Default to 'no'
        self.grid_use_combobox.grid(row=10, column=0, padx=5, pady=5, sticky='w')

        # Grid Spacing
        grid_spacing_label = ttk.Label(defaults_scrollable_frame, text="Grid Spacing:", font=self.title_font)
        grid_spacing_label.grid(row=11, column=0, sticky='w', padx=5, pady=5)
        self.grid_spacing_entry = ttk.Entry(defaults_scrollable_frame, width=30)
        self.grid_spacing_entry.insert(0, "0.1")
        self.grid_spacing_entry.grid(row=12, column=0, padx=5, pady=5, sticky='w')

        # Configure grid weights
        defaults_scrollable_frame.columnconfigure(0, weight=1)

    def save_to_json(self):
        # Collect Structures
        selected_structures_indices = self.structures_listbox.curselection()
        structures = [self.structures_listbox.get(i) for i in selected_structures_indices]

        # Collect Molecules
        selected_molecules_indices = self.molecule_listbox.curselection()
        molecule_name = [self.molecule_listbox.get(i) for i in selected_molecules_indices]

        # Collect Pressure
        try:
            pmin = float(self.pmin_entry.get())
            pmax = float(self.pmax_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Pressure min and max must be numbers.")
            return

        try:
            psteps = int(self.psteps_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Pressure steps must be an integer.")
            return

        # Collect Temperatures
        temp_str = self.temp_entry.get()
        try:
            temperatures = [float(t.strip()) for t in temp_str.split(',') if t.strip()]
        except ValueError:
            messagebox.showerror("Invalid Input", "Temperatures must be numbers separated by commas.")
            return

        # Collect Charge Methods
        selected_charge_indices = self.charge_listbox.curselection()
        charge_method = [self.charge_listbox.get(i) for i in selected_charge_indices]

        # Collect Advanced Configs
        forcefield = self.forcefield_var.get()

        try:
            init_cycles = int(self.init_cycles_entry.get())
            cycles = int(self.cycles_entry.get())
            print_every = int(self.print_every_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Cycle counts and print_every must be integers.")
            return

        grid_use = self.grid_use_var.get()

        try:
            grid_spacing = float(self.grid_spacing_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Grid spacing must be a number.")
            return

        # Prepare data
        data = {
            "parameters": {
                "structure": structures,
                "molecule_name": molecule_name,
                "pressure": [pmin, pmax],
                "npoints": psteps,
                "temperature": temperatures,
                "charge_method": charge_method
            },
            "defaults": {
                "forcefield": forcefield,
                "init_cycles": init_cycles,
                "cycles": cycles,
                "print_every": print_every,
                "grid_use": grid_use,
                "grid_spacing": grid_spacing
            }
        }

        # Write to JSON file
        try:
            # Optionally, let user choose the save location
            file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                     filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                                                     title="Save JSON File")
            if not file_path:
                return  # User cancelled the save dialog

            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            messagebox.showinfo("Success", f"JSON file has been saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write JSON file.\n{e}")

def run_gui_input():
    root = tk.Tk()
    root.geometry("400x800") # define size of the GUI window
    root.tk.call('tk', 'scaling', 2.0) # to increase resolution
    app = JSONFormApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui_input()
