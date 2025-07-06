import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import Toplevel
import matplotlib.pyplot as plt
import pandas as pd
import os
from abc import ABC, abstractmethod

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --- Backend ---
def process_data(data, step=1, change_sense=0.0015, zero_threshold=0.005):
    out = pd.DataFrame(data.iloc[:, 0])
    out["state"] = None

    peaks = []
    peak_start = 0
    peak_end = 0

    index = 0
    value_prev = 0
    value_new = float(out.iloc[index, 0])

    state = "changing"

    while data.shape[0] > index:
        value_prev = value_new
        value_new = float(out.iloc[index, 0])

        if abs(value_new - value_prev) > change_sense*step or value_new <= zero_threshold:
            if state == "flat":
                peak_end = index-step
                peaks.append((peak_start, peak_end))
            state = "changing"
        else:
            if state != "flat":
                peak_start = index
            state = "flat"
        
        for i in range(step):
            index_to_change = index - step + i
            if index_to_change >= 0:
                out.iloc[index_to_change, 1] = state
        
        index += step

    return (out, peaks)

def plot_processed_data(plot_data):
    fig, ax = plt.subplots()
    colors = ['red', 'green', 'blue', 'yellow', 'black', 'purple', 'orange', 'brown']

    group_refs = []

    for i, group_raw in enumerate(plot_data):
        group = group_raw[0]
        peaks = group_raw[1]

        group_ref = []

        line, = ax.plot(group.index, group.iloc[:, 0], color=colors[i%len(colors)], linewidth=1, label='Data')
        group_ref.append(line)

        for peak in peaks:
            x_segment = range(peak[0], peak[1])
            y_segment = group.iloc[peak[0]:peak[1], 0]

            # Fill between line and x-axis for each segment
            area = ax.fill_between(x_segment, y_segment, y2=0, color=colors[i%len(colors)], alpha=0.1)
            group_ref.append(area)
        
        group_refs.append(group_ref)

    return fig, group_refs

def find_stats(data, peaks, stat):
    out = []
    for peak in peaks:
        match stat:
            case "Middle": out.append(data.iloc[(peak[0] + peak[1]) // 2, 0])
            case "Median": out.append(data.iloc[peak[0]:peak[1], 0].median())
            case "Mean": out.append(data.iloc[peak[0]:peak[1], 0].mean())
            case "Maximum": out.append(data.iloc[peak[0]:peak[1], 0].max())
    return out


# --- Frontend ---
def main():
    app = application()
    app.mainloop()

class application(tk.Tk):
    def __init__(self):
        super().__init__()

        # Application variables
        self.csv_file_path = ""
        self.default_folder = ""
        self.default_name = ""
        self.df = None
        self.all_columns = []
        self.column_names = []
        self.processed_df = []
        self.processed_data = []
        self.parameters = {}
        self.stat_flags = []
        self.save_file_path = ""
        self.output_data = None
        
        self.options_names = ["Middle", "Median", "Mean", "Maximum"]

        # Window Setup
        self.title("DIC Speckle Data Peak Analysis Wizard")
        self.geometry("400x400")
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.page_container = tk.Frame(self)
        self.page_container.grid(row=0, column=0, sticky="nsew")

        # Navigation button frame at the bottom
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.grid(row=1, column=0, sticky="ew")

        self.back_button = ttk.Button(self.nav_frame, text="Back", command=self.go_back)
        self.back_button.pack(side='left', padx=10, pady=10)

        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.go_next)
        self.next_button.pack(side='right', padx=10, pady=10)

        # Create and store pages
        page_classes = [Page1, Page2, Page3, Page4, Page5]
        self.pages = [PageClass(self.page_container, controller=self) for PageClass in page_classes]

        self.current_page_index = 0
        self.show_page(0)

    def show_page(self, index, prev=-1):
        if prev != -1:
            self.pages[prev].on_exit()

        for page in self.pages:
            page.pack_forget()
        self.pages[index].pack(expand=True, fill='both')
        self.pages[index].on_enter()
        self.update_nav_buttons()

    def update_nav_buttons(self):
        self.back_button.config(state='normal' if self.current_page_index > 0 else 'disabled')
        # self.next_button.config(state='normal')
        self.next_button.config(
            text='Finish' if self.current_page_index == len(self.pages) - 1 else 'Next'
        )

    def go_back(self):
        if self.current_page_index > 0:
            prev_page_index = self.current_page_index
            self.current_page_index -= 1
            self.show_page(self.current_page_index, prev=prev_page_index)

    def go_next(self):
        if self.current_page_index < len(self.pages) - 1:
            prev_page_index = self.current_page_index
            self.current_page_index += 1
            self.show_page(self.current_page_index, prev=prev_page_index)
        else:
            self.quit()

class Page_Template(ttk.Frame, ABC):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
    
    def on_enter(self):
        pass

    def on_exit(self):
        pass

class Page1(Page_Template):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.columnconfigure(0, weight=1)

        # the contents of the entry to watch for changes
        self.entry_text = tk.StringVar()
        self.entry_text.trace_add("write", self.check_path)
        self.entry_text.set(self.controller.csv_file_path)

        # title lable
        ttk.Label(self, text="Select CSV").grid(row=0, column=0, columnspan=2, pady=20)

        # browse button
        ttk.Button(self, text="Browse", command=self.upload_csv).grid(row=1, column=1, pady=10, padx=10)
        
        # path display box
        self.display_box = ttk.Entry(self, textvariable=self.entry_text)
        self.display_box.grid(row=1, column=0, sticky="ew", pady=10, padx=10)

    def on_enter(self):
        self.check_path()

    # Open a file upload
    def upload_csv(self):
        self.entry_text.set(filedialog.askopenfilename(title="Select a CSV file", filetypes=(("CSV files", "*.csv"),)))
        # self.display_box.insert(0, application.csv_file_path)
    
    # Ensure the selected csv is a valid file 
    def check_path(self, *args):
        path = self.entry_text.get()
        if os.path.isfile(path) and path.endswith('.csv'):
            self.controller.next_button.config(state='normal')
            self.controller.csv_file_path = self.entry_text.get()

            self.controller.defualt_folder = os.path.dirname(self.controller.csv_file_path)
            self.controller.default_name = os.path.splitext(os.path.basename(self.controller.csv_file_path))[0] + "_results.csv"
            self.controller.save_file_path = self.controller.defualt_folder + "/" + self.controller.default_name
        else:
            self.controller.next_button.config(state='disabled')

class Page2(Page_Template):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

        # the contents of the entry to watch for changes
        self.entry_text = tk.StringVar()
        self.entry_text.trace_add("write", self.entry_update)
        
        self.name_text = tk.StringVar()

        # title label
        ttk.Label(self, text="Choose Column Groupings").grid(row=0, column=0, columnspan=3, pady=20)

        # key table
        self.key = ttk.Treeview(self, columns=("index", "heading"), show='headings', height=100)
        self.key.heading("index", text="Index")
        self.key.heading("heading", text="Heading")
        self.key.column("index", width=40, anchor="center")
        self.key.column("heading", width=80)
        self.key.bind("<<TreeviewSelect>>", self.key_select)
        self.key.grid(row=4, column=2, pady=10, padx=10)

        # buttons
        self.button_add = ttk.Button(self, text="Add Data Column", command=self.list_add)
        self.button_add.grid(row=1, column=2, pady=10, padx=10, sticky='ew')

        self.button_remove = ttk.Button(self, text="Remove Last Added", command=self.list_remove)
        self.button_remove.grid(row=2, column=2, pady=10, padx=10, sticky='ew')

        self.button_clear = ttk.Button(self, text="Clear All", command=self.list_clear)
        self.button_clear.grid(row=3, column=2, pady=10, padx=10, sticky='ew')

        # field labels
        ttk.Label(self, text="Column(s) Range").grid(row=1, column=0, padx=10, pady=8, sticky='sw')
        ttk.Label(self, text="Group Name").grid(row=1, column=1, padx=10, pady=8, sticky='sw')

        # range field
        vcmd = (self.register(self.valid_key), '%P')
        self.display_box = ttk.Entry(self, validate="key", validatecommand=vcmd, textvariable=self.entry_text)
        self.display_box.grid(row=2, column=0, sticky="ew", pady=10, padx=10)
        # name field
        self.display_box = ttk.Entry(self, textvariable=self.name_text)
        self.display_box.grid(row=2, column=1, sticky="ew", pady=10, padx=10)

        # Range List
        self.list = tk.Listbox(self)
        self.list.grid(row=3, column=0, rowspan=2, sticky="nsew", pady=10, padx=10)
        # Name List
        self.name_list = tk.Listbox(self)
        self.name_list.grid(row=3, column=1, rowspan=2, sticky="nsew", pady=10, padx=10)
        
        self.button_add.config(state='disabled')

    def on_enter(self):
        self.controller.df = pd.read_csv(self.controller.csv_file_path)
        self.entry_text.set("")
        
        self.key.delete(*self.key.get_children())
        for i, col in enumerate(self.controller.df.columns):
            self.key.insert("", tk.END, values=(i, col))
        
        self.list_updated()
    
    def key_select(self, *args):
        items = self.key.selection()

        select_str = ""
        in_range = False
        prev = -100

        for item in items:
            id = self.key.index(item)

            if prev == -100:
                select_str = str(id)
            elif prev == id-1:
                if in_range:
                    select_str = select_str[:select_str.rfind(":") + 1] + str(id)
                else:
                    in_range = True
                    select_str += ":" + str(id)
            elif prev < id-1:
                in_range = False
                select_str += "," + str(id)
            
            prev = id
        
        self.entry_text.set(select_str)

    def check_proceed(self):
        if len(self.controller.all_columns)>0:
            self.controller.next_button.config(state='normal')
        else:
            self.controller.next_button.config(state='disabled')

    def valid_key(self, entry_text):
        if entry_text == "":
            return True
        allowed_chars = set("0123456789,:")
        return all(c in allowed_chars for c in entry_text)

    def list_add(self):
        self.validate_range(self.entry_text.get())
        # self.list.insert(tk.END, self.entry_text.get())
        self.list_updated()

    def list_remove(self):
        self.list.delete(tk.END)
        self.controller.all_columns.pop()
        self.name_list.delete(tk.END)
        self.controller.column_names.pop()
        self.list_updated()

    def list_clear(self):
        self.list.delete(0, tk.END)
        self.controller.all_columns = []
        self.name_list.delete(0, tk.END)
        self.controller.column_names = []
        self.list_updated()

    def entry_update(self, *args):
        if len(self.entry_text.get()) > 0:
            self.button_add.config(state='normal')
        else:
            self.button_add.config(state='disabled')

    def list_updated(self):
        if self.list.size() > 0:
            self.button_remove.config(state='normal')
            self.button_clear.config(state='normal')
        else:
            self.button_remove.config(state='disabled')
            self.button_clear.config(state='disabled')
        self.check_proceed()
        print(self.controller.all_columns)
        print(self.controller.column_names)
    
    def validate_range(self, input_str):
        prev = 'start'
        curr = 'start'

        valid = True
        range_str = ""
        ranges = []
        error_message = ""

        after_colon = False

        if not input_str[0].isdigit() or not input_str[len(input_str)-1].isdigit():
            curr = 'invalid'
            error_message = "Column groups must start and end with digits (good 3,4:8 - bad ,2:8,10:)"
            valid = False

        for char in input_str:

            prev = curr
            curr = 'digit' if char.isdigit() else 'colon' if char == ":" else 'comma'

            if curr == 'colon':
                if after_colon:
                    valid = False
                    error_message = "Ranges may only include a single colon (good 3:8 - bad 1:8:3)"
                    break
                else:
                    after_colon = True

            match prev:

                case 'start':
                    range_str += char

                case 'digit':
                    if curr == 'comma':
                        ranges.append(range_str)
                        range_str = ""
                        after_colon = False
                    else:
                        range_str += char

                case 'colon':
                    if curr != 'digit':
                        valid = False
                        error_message = "Colons must be followed by digits (good 2:4 - bad 1:,10)"
                        break
                    else:
                        range_str += char

                case 'comma':
                    if curr != 'digit':
                        valid = False
                        error_message = "Commas must be followed by digits (good 1,2,9 - bad 2,,3)"
                        break
                    else:
                        range_str += char

        if valid:
            ranges.append(range_str)
            # self.list.insert(tk.END, input_str)
            self.add_ranges(ranges, input_str)
        else:
            tk.messagebox.showwarning(title="Invalid Column Group", message=error_message)
    
    def add_ranges(self, ranges, input_str):
        columns = []

        valid = True
        error_message = ""

        for range_str in ranges:
            if ":" in range_str:
                colon_ind = range_str.index(":")
                col_start = int(range_str[:colon_ind])
                col_end = int(range_str[colon_ind+1:])

                for i in range(min(col_start,col_end), max(col_start,col_end)+1):
                    if self.verify_index(i):
                        if i in columns:
                            valid = False
                            error_message = "Ranges may not inlude duplicate columns (good 2,4:6 - bad 3,2:7)"
                        else:
                            columns.append(i)
                    else:
                        valid = False
                        error_message = "One or more specified columns are out of bounds"
            else:
                if self.verify_index(int(range_str)):
                    if int(range_str) in columns:
                        valid = False
                        error_message = "Ranges may not inlude duplicate columns (good 2,4:6 - bad 3,2:7)"
                    else:
                        columns.append(int(range_str))
                else:
                    valid = False
                    error_message = "One or more specified columns are out of bounds"
        
        if (valid):
            self.list.insert(tk.END, input_str)
            self.controller.all_columns.append(columns)
            self.entry_text.set("")

            column_name = self.get_column_name(columns, input_str)
            
            self.name_list.insert(tk.END, column_name)
            self.controller.column_names.append(column_name)
            self.name_text.set("")
        else:
            tk.messagebox.showwarning(title="Invalid Column Group", message=error_message)
    
    def get_column_name(self, columns, input_str):
        input_name = self.name_text.get()
        if input_name == "":
            if (len(columns) == 1):
                return self.controller.df.columns[columns[0]]
            else:
                return "Avg "+input_str
        else:
            return input_name


    def verify_index(self, index):
        return self.controller.df.shape[1] > index


class Page3(Page_Template):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)

        self.visible_lines = []

        self.popup = None

        ttk.Label(self, text="Adjust Settings").grid(row=0, column=0, columnspan=4, pady=20)

        self.button_vis=ttk.Button(self, text="Visualize", command=self.visualize)

        self.settings = {
            "Slope Threshold" : [None, None, None, tk.DoubleVar(), 0.15, "The maximum magnitude of the line's slope that will considered flat (AKA rounded to zero). Increase to detect more peaks, decrease to detect less", 0, -1],
            "Zero Threshold" : [None, None, None, tk.DoubleVar(), 0.5, "The minimum y-value to be considered for a peak. Increase to stop detecting zero ranges between pogos, decrease to detect lower peaks that are missed", 0, -1],
            "Step" : [None, None, None, tk.IntVar(), 2, "The frequency at which points are sampled: check slope every [1] point, [2] points, [50] pionts? Increase to 'smooth' rough data, decrease to detect fine fluctuations. ", 1, 50]
        }
        
        vcmd = (self.register(self.valid_key), '%P')

        for index, (key, value) in enumerate(self.settings.items()):
            self.settings[key][0] = ttk.Entry(self, textvariable=self.settings[key][3], validate="key", validatecommand=vcmd)
            self.settings[key][0].grid(row=index+1, column=1, pady=10, padx=10, sticky="ew")
            self.settings[key][3].trace_add("write", self.update_global_parameters)
            self.reset(key)
            
            self.settings[key][1] = ttk.Button(self, text="↻", width=3, command=lambda k=key: self.reset(k))
            self.settings[key][1].grid(row=index+1, column=2, pady=10, padx=10)
            
            self.settings[key][2] = ttk.Button(self, text="?", width=3, command=lambda k=key: self.help(k))
            self.settings[key][2].grid(row=index+1, column=3, pady=10, padx=10)

            ttk.Label(self, text=key).grid(row=index+1, column=0, pady=10, padx=10)
        
        self.button_vis.grid(row=4, column=0, columnspan=4, padx=10, pady=10)
    
    def on_enter(self):
        self.gen_dfs()
        self.update_global_parameters()

    def on_exit(self):
        self.process()

    def gen_dfs(self):
        df_clean = self.controller.df.apply(pd.to_numeric, errors='coerce').dropna()
        df_clean *= 100
        
        self.controller.processed_df = []
        for i, group in enumerate(self.controller.all_columns):
            averaged = df_clean.iloc[:, group].mean(axis=1)
            new_df = pd.DataFrame({"Group "+str(i) : averaged})
            self.controller.processed_df.append(new_df)
    
    def valid_key(self, entry_text):
        if entry_text == "":
            return True
        allowed_chars = set("0123456789.")
        return all(c in allowed_chars for c in entry_text)

    def update_global_parameters(self, *args):
        self.button_vis.config(state='normal')
        self.controller.next_button.config(state='normal')

        for index, (key, value) in enumerate(self.settings.items()):
            try:
                field_value = value[3].get()
                lower_bound = value[6]
                upper_bound = value[7]

                range_met = (lower_bound == -1 or lower_bound <= field_value) and (upper_bound == -1 or upper_bound >= field_value)
                if (field_value != "" and range_met):
                    self.controller.parameters[key] = field_value
                else:
                    raise Exception("Invalid input")

            except:
                self.controller.parameters[key] = value[4]
                self.button_vis.config(state='disabled')
                self.controller.next_button.config(state='disabled')

    def reset(self, key):
        self.settings[key][3].set(self.settings[key][4])
    
    def help(self, key):
        tk.messagebox.showwarning(title="Help: "+key, message=self.settings[key][5])
    
    def process(self):
        self.controller.processed_data = []
        for df in self.controller.processed_df:

            self.controller.processed_data.append(process_data(df, 
                                                               change_sense=self.controller.parameters["Slope Threshold"], 
                                                               zero_threshold=self.controller.parameters["Zero Threshold"], 
                                                               step=self.controller.parameters["Step"]))

    def visualize(self):
        self.process()

        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
            self.popup = None

        self.popup = Toplevel()
        self.popup.title("Processed Data Preview")

        self.popup.visible_lines = []

        for i, df in enumerate(self.controller.processed_df):
            self.popup.visible_lines.append(tk.BooleanVar(value=True))
            cb = ttk.Checkbutton(self.popup, variable=self.popup.visible_lines[i], command=self.refresh)
            cb.pack(side="left", padx=10, pady=10)

        self.popup.fig, self.popup.group_refs = plot_processed_data(self.controller.processed_data)

        self.popup.canvas = FigureCanvasTkAgg(self.popup.fig, master=self.popup)
        self.popup.canvas.draw()
        self.popup.canvas.get_tk_widget().pack(padx=10, pady=10)

        ttk.Button(self.popup, text="Close", command=self.popup.destroy).pack(side="bottom", pady=10)
    
    def refresh(self):
        lines = []
        for val in self.popup.visible_lines:
            lines.append(val.get())
        
        for group in zip(lines, self.popup.group_refs):
            for object in group[1]:
                object.set_visible(group[0])

        self.popup.canvas.draw()

class Page4(Page_Template):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Choose Output Data").grid(row=0, column=0, columnspan=2, pady=20)

        self.checkboxes = []
        self.checkvars = []

        for i, text in enumerate(self.controller.options_names):
            ttk.Label(self, text=text).grid(sticky='E', row=i+1, column=0, padx=10, pady=10)
            
            self.checkvars.append(tk.BooleanVar(value=False))

            controller.stat_flags.append(False)

            cb = ttk.Checkbutton(self, variable=self.checkvars[i], command=self.update_stats)
            cb.grid(sticky='W', row=i+1, column=1, padx=10, pady=10)
            self.checkboxes.append(cb)

    def on_enter(self):
        self.update_stats()
    
    def update_stats(self):
        self.controller.next_button.config(state='disabled')
        for i, var in enumerate(self.checkvars):
            flag = var.get()
            self.controller.stat_flags[i] = flag
            if flag:
                self.controller.next_button.config(state='normal')


class Page5(Page_Template):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Download Data").grid(row=0, column=0, columnspan=2, pady=20)

        # the contents of the entry to watch for changes
        self.entry_text = tk.StringVar()
        self.entry_text.trace_add("write", self.update_path)

        # browse button
        ttk.Button(self, text="Browse", command=self.choose_location).grid(row=1, column=1, pady=10, padx=10)

        self.download = ttk.Button(self, text="Download", command=self.download_csv)
        self.download.grid(row=2, column=0, columnspan=2, pady=10, padx=10)
        
        # path display box
        self.display_box = ttk.Entry(self, textvariable=self.entry_text)
        self.display_box.grid(row=1, column=0, sticky="ew", pady=10, padx=10)
    
    def on_enter(self):
        self.entry_text.set(self.controller.save_file_path)
        self.controller.output_data = pd.DataFrame()
        
        for i, string in enumerate(self.controller.options_names):
            if self.controller.stat_flags[i]:
                for j, group in enumerate(self.controller.processed_data):
                    stat = find_stats(group[0], group[1], string)

                    column_name = "Group " + str(j)

                    self.controller.output_data[column_name + " " + string] = stat
    
    def choose_location(self):
        new_loc = filedialog.asksaveasfilename(title="Select a destination location",
                                                         filetypes=(("CSV files", "*.csv"),),
                                                         initialdir=self.controller.default_folder,
                                                         initialfile=self.controller.default_name,)
        if (new_loc != ""):
            self.entry_text.set(new_loc)

    def update_path(self, *args):
        self.controller.save_file_path = self.display_box.get()
        self.controller.defualt_folder = os.path.dirname(self.controller.save_file_path)
        self.controller.default_name = os.path.basename(self.controller.save_file_path)
    
    def download_csv(self):
        try:
            self.controller.output_data.to_csv(self.controller.save_file_path, index=False)
            tk.messagebox.showinfo(title="Download successful", message="The file was successfully saved to your computer in the specified location.")
        except:
            tk.messagebox.showwarning(title="Invalid file location", message="The output CSV file could not be saved at the specified location. Re-select a path and try again.")



if __name__ == "__main__":
    main()