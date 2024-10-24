import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
import matplotlib.pyplot as plt
#import plotly.express as px
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import pandas as pd
from itertools import cycle

class JSONInputForm:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Form GUI")

        # Define font styles
        self.title_font = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.label_font = tkFont.Font(family="Helvetica", size=8)
        self.button_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.note_font = tkFont.Font(family="Helvetica", size=6)

        self.create_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handle the window close event."""
        self.root.quit()  # Quit the main loop
        self.root.destroy()  # Destroy the main window

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
        structure_scrollbar = tk.Scrollbar(parameters_scrollable_frame, orient="vertical")
        self.structures_listbox = tk.Listbox(parameters_scrollable_frame, 
                                             selectmode=tk.MULTIPLE, height=6, exportselection=False,
                                             yscrollcommand = structure_scrollbar.set)
        for item in self.refcodes:
            self.structures_listbox.insert(tk.END, item)
        self.structures_listbox.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        structure_scrollbar.config(command=self.structures_listbox.yview)
        structure_scrollbar.grid(row=1, column=2, sticky="ns")

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

class JSONOutputReader:
    def __init__(self, root):
        self.root = root
        self.json_file_path = tk.StringVar()
        self.df_json = None
        self.setup_file_selection_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handle the window close event."""
        self.root.quit()  # Quit the main loop
        self.root.destroy()  # Destroy the main window

    def setup_file_selection_gui(self):
        """Setup the GUI for file selection"""
        ttk.Label(self.root, text="Select Isotherms JSON File").pack(pady=10)
        self.file_entry = ttk.Entry(self.root, textvariable=self.json_file_path, width=50)
        self.file_entry.pack(pady=5)
        browse_button = ttk.Button(self.root, text="Browse", command=self.browse_file)
        browse_button.pack(pady=5)
        load_button = ttk.Button(self.root, text="Load File", command=self.load_json_data)
        load_button.pack(pady=10)

    def browse_file(self):
        """Open file dialog to select the JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select Isotherms JSON File", 
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.json_file_path.set(file_path)

    def load_json_data(self):
        """Load and clean JSON isotherm data, then open field selection window"""
        file_path = self.json_file_path.get()
        if file_path:
            with open(file_path, "r") as f:
                file_contents = f.read()
            parsed_json = json.loads(file_contents)
            self.df_json = pd.DataFrame(parsed_json["isotherms"])

            # Clean the data and extract unique values
            self.df_json["refcode"] = self.df_json["structure"].apply(lambda x: x.split("_clean")[0])
            unique_structures = self.df_json["refcode"].unique().tolist()
            unique_charge_methods = self.df_json["charge_method"].unique().tolist()
            unique_molecule_names = self.df_json["molecule_name"].unique().tolist()
            min_temp = self.df_json["temperature"].min()
            max_temp = self.df_json["temperature"].max()

            # Once the file is loaded, show the field selection window
            self.show_field_selection_window(unique_structures, unique_charge_methods, unique_molecule_names, min_temp, max_temp)

    def show_field_selection_window(self, structures, charge_methods, molecules, min_temp, max_temp):
        """Setup the GUI for selecting fields"""
        # Create a new window
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title("Select Parameters")
        
        # Structure selection (Multi-select Listbox) with scrollbar
        ttk.Label(self.selection_window, text="Select Structures:").grid(row=0, column=0, padx=10, pady=5)
        structure_scrollbar = tk.Scrollbar(self.selection_window, orient="vertical")
        self.structure_listbox = tk.Listbox(self.selection_window, selectmode="multiple", height=6, exportselection=False, 
                                            yscrollcommand=structure_scrollbar.set)
        for structure in structures:
            self.structure_listbox.insert(tk.END, structure)
        self.structure_listbox.grid(row=0, column=1, padx=10, pady=5)
        structure_scrollbar.config(command=self.structure_listbox.yview)
        structure_scrollbar.grid(row=0, column=2, sticky="ns")

        # Charge method selection (Multi-select Listbox)
        ttk.Label(self.selection_window, text="Select Charge methods:").grid(row=1, column=0, padx=10, pady=5)
        self.charge_method_listbox = tk.Listbox(self.selection_window, selectmode="multiple", height=6,exportselection=False)
        for charge_method in charge_methods:
            self.charge_method_listbox.insert(tk.END, charge_method)
        self.charge_method_listbox.grid(row=1, column=1, padx=10, pady=5)

        # Molecule name selection
        ttk.Label(self.selection_window, text="Select Molecule Name:").grid(row=2, column=0, padx=10, pady=5)
        self.molecule_listbox = tk.Listbox(self.selection_window, selectmode="multiple", height=6,exportselection=False)
        for molecule in molecules:
            self.molecule_listbox.insert(tk.END, molecule)
        self.molecule_listbox.grid(row=2, column=1, padx=10, pady=5)

        # Temperature range selection
        ttk.Label(self.selection_window, text="Min Temperature:").grid(row=3, column=0, padx=10, pady=5)
        self.min_temp_var = tk.DoubleVar(value=min_temp)
        min_temp_entry = ttk.Entry(self.selection_window, textvariable=self.min_temp_var)
        min_temp_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(self.selection_window, text="Max Temperature:").grid(row=4, column=0, padx=10, pady=5)
        self.max_temp_var = tk.DoubleVar(value=max_temp)
        max_temp_entry = ttk.Entry(self.selection_window, textvariable=self.max_temp_var)
        max_temp_entry.grid(row=4, column=1, padx=10, pady=5)

        # Button to confirm selection
        confirm_button = ttk.Button(self.selection_window, text="Confirm Selection", command=self.process_selection)
        confirm_button.grid(row=5, column=0, columnspan=2, pady=10)

    def process_selection(self):
        """Process the user-selected fields and plot the isotherms"""
        selected_structures = [self.structure_listbox.get(i) for i in self.structure_listbox.curselection()]
        selected_charge_methods = [self.charge_method_listbox.get(i) for i in self.charge_method_listbox.curselection()]
        selected_molecules = [self.molecule_listbox.get(i) for i in self.molecule_listbox.curselection()]
        #selected_charge_method = self.charge_method_var.get() # only one possible value
        #selected_molecule = self.molecule_var.get() # only one possible value

        min_temp = self.min_temp_var.get()
        max_temp = self.max_temp_var.get()

        # Filter the data based on user selection
        filtered_df = self.df_json[
            (self.df_json["refcode"].isin(selected_structures)) &
            (self.df_json["charge_method"].isin(selected_charge_methods)) &
            (self.df_json["molecule_name"].isin(selected_molecules)) &
            (self.df_json["temperature"] >= min_temp) &
            (self.df_json["temperature"] <= max_temp)
            ]

        # Plot all selected isotherms in a single graph
        self.plot_isotherms(filtered_df)

    def plot_isotherms(self, filtered_df):
        """Plot the filtered isotherms in a single matplotlib plot with proper legend"""
        fig, ax = plt.subplots()

        # Generate distinct line styles, colors, or markers
        markers = cycle(('o', 'v', '^', '<', '>', 's', 'p', '*', 'h', 'H', 'D', 'd'))
        colors = cycle(plt.cm.tab20.colors)  # Using tab20 colormap for distinct colors

        # Plot each row in the filtered dataframe
        for i, row in filtered_df.iterrows():
            structure = row["refcode"]
            temperature = row["temperature"]
            molecule = row["molecule_name"]
            charge_method = row["charge_method"]

            # Plot each isotherm with a unique color and marker
            ax.plot(row["Pressure(Pa)"], row["uptake(cm^3 (STP)/cm^3 framework)"],
                    label=f"{structure} {temperature}K {molecule} {charge_method}",
                    marker=next(markers), color=next(colors))

        # Set labels
        ax.set_xlabel("Pressure (Pa)")
        ax.set_ylabel("Uptake (cm^3 STP/cm^3 framework)")

        # Set the legend to the right of the plot
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

        # Display the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, self.selection_window)
        canvas.draw()
        canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, pady=10)

        plt.tight_layout()

        # Save button
        save_button = ttk.Button(self.selection_window, text="Save Plot", command=lambda: self.save_plot(fig))
        save_button.grid(row=7, column=0, columnspan=2, pady=10)

    def save_plot(self, fig):
        """Open a file dialog to save the plot"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            fig.savefig(file_path)
            print(f"Plot saved to {file_path}")

def run_gui_output():
    """Function to initialize and run the GUI"""
    root = tk.Tk()
    root.geometry("400x400") # define size of the GUI window
    root.title("Isotherm Data Query")
    app = JSONOutputReader(root)
    root.mainloop()

def run_gui_input():
    root = tk.Tk()
    root.geometry("400x800") # define size of the GUI window
    root.tk.call('tk', 'scaling', 2.0) # to increase resolution
    app = JSONInputForm(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui_output()
