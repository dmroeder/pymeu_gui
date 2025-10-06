import configparser
import ipaddress
import logging
import os
import pylogix
import pymeu
import subprocess
import sys
import threading
import time
import tkinter as tk
import queue

from mer_tools import mer
from pathlib import Path
from pymeu import MEUtility
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk


__version_info__ = (0,8,0)
__version__ = '.'.join(str(x) for x in __version_info__)


class Window(tk.Frame):

    def __init__(self, main=None):
        tk.Frame.__init__(self, main)
        self.main = main

        self.product_codes = [
            13,   #PanelView Plus 700 CE
            14,   #PanelView Plus 700
            15,   #PanelView Plus 400
            16,   #PanelView Plus 600
            17,   #PanelView Plus 1000
            18,   #PanelView Plus 1250
            19,   #PanelView Plus 1500
            20,   #PanelView Plus 1000 CE
            21,   #PanelView Plus 1250 CE
            22,   #PanelView Plus 1500 CE
            40,   #PanelView Plus Compact 400
            42,   #PanelView Plus Compact 600
            44,   #PanelView Plus Compact 1000
            45,   #PanelView Plus 6 700
            46,   #PanelView Plus 6 700 CE
            47,   #PanelView Plus 6 1000
            48,   #PanelView Plus 6 1000 CE
            49,   #PanelView Plus 6 1250
            50,   #PanelView Plus 6 1250 CE
            51,   #PanelView Plus 6 1500
            52,   #PanelView Plus 6 1500 CE
            74,   #PanelView Plus 6 400
            75,   #PanelView Plus 6 400
            77,   #PanelView Plus 6 600
            78,   #PanelView Plus 6 600 Extended
            79,   #PanelView Plus 6 600 Extended
            81,   #PanelView Plus 7 Standard 600
            83,   #PanelView Plus 7 Standard 700
            85,   #PanelView Plus 7 Standard 900W
            87,   #PanelView Plus 7 Standard 1000
            89,   #PanelView Plus 7 Standard 1200W
            91,   #PanelView Plus 7 Standard 1500
            94,   #PanelView Plus 7 Performance 700
            96,   #PanelView Plus 7 Performance 900W
            98,   #PanelView Plus 7 Performance 1000
            100,  #PanelView Plus 7 Performance 1200W
            102,  #PanelView Plus 7 Performance 1500
            104,  #PanelView Plus 7 Performance 1900
            110,  #PanelView Plus 7 Performance 700W
            112,  #PanelView Plus 7 Performance 1000W
            114,  #PanelView Plus 7 Performance 1200W
            116,  #PanelView Plus 7 Performance 1500W
            118,  #PanelView Plus 7 Performance 1900W
            147,  #PanelView Plus 6 Compact 1000
            175,  #PanelView Plus 6 Compact 400
            177,  #PanelView Plus 6 Compact 600
            179,  #PanelView Plus 7 Standard 400W
            180,  #PanelView Plus 7 Standard 400W DLR
            181,  #PanelView Plus 7 Standard 600
            182,  #PanelView Plus 7 Standard 600 DLR
            183,  #PanelView Plus 7 Standard 700
            184,  #PanelView Plus 7 Standard 700 DLR
            185,  #PanelView Plus 7 Standard 900W
            186,  #PanelView Plus 7 Standard 900W DLR
            187,  #PanelView Plus 7 Standard 1000
            188,  #PanelView Plus 7 Standard 1000 DLR
            189,  #PanelView Plus 7 Standard 1200W
            190,  #PanelView Plus 7 Standard 1200W DLR
            191,  #PanelView Plus 7 Standard 1500
            192]  #PanelView Plus 7 Standard 1500 DLR

        self.log_file = "logjammin.log"
        logging.basicConfig(filename=self.log_file, filemode="w", format='%(asctime)s - %(message)s')
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        self.queue = queue.Queue()
        self.last_mer = ""
        self.window_width = "500"

        self.log.info("INIT - Starting pymeu_gui")
        self.log.info("INIT - pymeu_gui version {}".format(__version__))
        self.log.info("INIT - pylogix version {}".format(pylogix.__version__))
        self.log.info("INIT - pymeu version {}".format(pymeu.__version__))

        current_path = os.path.dirname(__file__)
        current_path = current_path.replace(os.sep, '/')

        # variables
        self.mer_file_var = tk.StringVar()
        self.ip_address_var = tk.StringVar()
        self.upload_path_var = tk.StringVar()
        self.download_file_var = tk.StringVar()

        self.overwrite_upload_var = tk.BooleanVar()
        self.overwrite_download_var = tk.BooleanVar()
        self.replace_comms_var = tk.BooleanVar()
        self.delete_logs_var = tk.BooleanVar()
        self.run_on_start_var = tk.BooleanVar()
        self.dark_theme_var = tk.BooleanVar()
        self.light_theme_var = tk.BooleanVar()
        self.discover_var = tk.BooleanVar()

        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self._create_new_config()
        self.config.read('config.ini')

        theme = self.config.get("general", "theme")
        tcl_file = self._get_file("resources/azure.tcl")
        self.tk.call("source", tcl_file)
        self.tk.call("set_theme", theme)

        try:
            # load config
            if theme == "dark":
                self.dark_theme_var.set(1)
            else:
                self.light_theme_var.set(1)
            self.overwrite_upload_var.set(self.config.get('general', 'overwrite_upload'))
            self.overwrite_download_var.set(self.config.get('general', 'overwrite_download'))
            self.replace_comms_var.set(self.config.get('general', 'replace_comms'))
            self.delete_logs_var.set(self.config.get('general', 'delete_logs'))
            self.run_on_start_var.set(self.config.get('general', 'run_at_start'))
            self.upload_path_var.set(self.config.get('general', 'upload_path'))
            self.discover_var.set(self.config.get('general', 'discover_on_init'))
            self.window_width = self.config.get('general', 'window_width')
            # set the default download path
            dir = self.config.get('general', 'last_download_dir')
            mer = self.config.get('general', 'last_download_mer')
            file_path = "{}\\{}".format(dir, mer)
            self.download_file_var.set(file_path)
        except:
            self.log.info("INIT - config file is corrupt, creating a new one")
            self._create_new_config()
            self.save_config()

        # settings frame
        self.frame1 = ttk.LabelFrame(self.main, text="Settings")
        self.ip_label = ttk.Label(self.frame1, text="HMI IP Address:")
        self.ip_list = ttk.Combobox(self.frame1)
        self.ip_list.bind("<<ComboboxSelected>>", self._get_runtime_files)
        self.discover_on_init_cb = ttk.Checkbutton(self.frame1, text="Discover on init?",
                                                   variable=self.discover_var,
                                                   onvalue=True, offvalue=False)
        self.canvas = tk.Canvas(self.frame1, width=10, height=10)
        self.connected = self.canvas.create_oval(0, 0, 10, 10, fill="red")

        # upload frame
        self.frame2 = ttk.LabelFrame(self.main, text="Upload MER")
        self.upload_label = ttk.Label(self.frame2, text="Upload path:")
        self.upload_entry = ttk.Entry(self.frame2, textvariable=self.upload_path_var)
        self.mer_list_label = ttk.Label(self.frame2, text="Files on terminal:")
        self.mer_list = tk.Listbox(self.frame2)
        self.upload_browse_button = ttk.Button(self.frame2, text="...", command=self.browse_upload_directory)
        self.upload_refresh_button = ttk.Button(self.frame2, text="Refresh", command=self._get_runtime_files)
        self.upload_button = ttk.Button(self.frame2, text="Upload Selected", command=self.upload)
        self.upload_all_button = ttk.Button(self.frame2, text="Upload All", command=self.upload_all)
        self.overwrite_upload_cb = ttk.Checkbutton(self.frame2, text="Overwrite existing files on upload?",
                                                   variable=self.overwrite_upload_var,
                                                   onvalue=True, offvalue=False)

        # download frame
        self.frame3 = ttk.LabelFrame(self.main, text="Download MER")
        self.download_label = ttk.Label(self.frame3, text="File to Download:")
        self.download_entry = ttk.Entry(self.frame3, textvariable=self.download_file_var)
        self.download_browse_button = ttk.Button(self.frame3, text="...", command=self.browse_download_file)
        self.download_button = ttk.Button(self.frame3, text="Download", command=self.download)
        self.overwrite_download_cb = ttk.Checkbutton(self.frame3, text="Overwrite file?",
                                                     variable=self.overwrite_download_var,
                                                     onvalue=True, offvalue=False)
        self.replace_comms_cb = ttk.Checkbutton(self.frame3, text="Replace communications? (hint, you should)",
                                                variable=self.replace_comms_var,
                                                onvalue=True, offvalue=False)
        self.delete_logs_cb = ttk.Checkbutton(self.frame3, text="Delete logs?",
                                              variable=self.delete_logs_var,
                                              onvalue=True, offval=False)
        self.run_on_start_cb = ttk.Checkbutton(self.frame3, text="Run at startup?",
                                               variable=self.run_on_start_var,
                                               onvalue=True, offvalue=False)

        self.stop_thread = threading.Event()
        # progress bar
        self.frame4 = ttk.LabelFrame(self.main, text = "Transfer Progress")
        self.progress_bar = ttk.Progressbar(self.frame4,
                                            orient='horizontal',
                                            mode='determinate')

        self.init_window()
        if self.discover_var.get():
            self._find_panelview_ip()
            self._get_runtime_files()
            self.check_queue()
            self.connection_thread()

        self.main.update_idletasks()
        window_height = self.main.winfo_height()
        try:
            geometry = "{}x{}".format(self.window_width, window_height)
            self.main.geometry(geometry)
        except:
            self.log.info("GUI - Failed to set window geometry")

    def init_window(self):
        """ Place all GUI items
        """
        # create a menu
        menu = tk.Menu(self.main)
        self.main.config(menu=menu)

        # Add file dropdown with exit
        f = tk.Menu(menu)
        f.add_command(label="Get Terminal Info", command=self._get_terminal_info)
        f.add_command(label="Open log file", command=self.open_log)
        f.add_command(label="Save defaults", command=self.save_config)
        f.add_separator()
        f.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=f)

        # Add edit dropdown menu
        f = tk.Menu(menu)
        f.add_checkbutton(label="Dark theme", onvalue=1, offvalue=0,
                          variable=self.dark_theme_var, command=self.set_dark_theme)
        f.add_checkbutton(label="Light theme", onvalue=1, offvalue=0,
                          variable=self.light_theme_var, command=self.set_light_theme)

        menu.add_cascade(label="Edit", menu=f)

        # settings frame
        self.frame1.pack(padx=5, pady=10, fill=tk.X)
        self.frame1.grid_columnconfigure(0, weight=0)
        self.frame1.grid_columnconfigure(1, weight=1)
        self.ip_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.ip_list.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)
        self.discover_on_init_cb.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.canvas.grid(row=0, column=3)

        # upload frame
        self.frame2.pack(padx=5, pady=10, fill=tk.X)
        self.frame2.grid_columnconfigure(0, weight=0)
        self.frame2.grid_columnconfigure(1, weight=1)
        self.upload_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.upload_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.E+tk.W)
        self.upload_browse_button.grid(row=0, column=4, padx=5, pady=5, sticky=tk.E)
        self.mer_list_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W)
        self.mer_list.grid(row=2, column=0, columnspan=5, padx=5, pady=5, sticky=tk.W+tk.E)
        self.overwrite_upload_cb.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.upload_refresh_button.grid(row=3, column=2, padx=5, pady=5)
        self.upload_button.grid(row=3, column=3, padx=5, pady=5)
        self.upload_all_button.grid(row=3, column=4, padx=5, pady=5, sticky=tk.W)

        # download frame
        self.frame3.pack(padx=5, pady=10, fill=tk.X)
        self.frame3.grid_columnconfigure(0, weight=0)
        self.frame3.grid_columnconfigure(1, weight=1)
        self.download_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.download_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        self.download_browse_button.grid(row=0, column=3, padx=5, pady=5)
        self.overwrite_download_cb.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.replace_comms_cb.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.delete_logs_cb.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.run_on_start_cb.grid(row=3, column=1, columnspan=2, padx=5, pady=6, sticky=tk.W)
        self.download_button.grid(row=3, column=3, padx=5, pady=5)

        # progress bar
        self.frame4.pack(padx=5, pady=10, fill=tk.X)
        self.frame4.grid_columnconfigure(0, weight=0)
        self.frame4.grid_columnconfigure(1, weight=1)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=10)

    def _get_file(self, file_name):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, file_name)
        else:
            return file_name

    def _find_panelview_ip(self):
        """ Send list identity and save all HMI IP addresses
        that were discovered on the network to a list
        """
        hmis = []
        with pylogix.PLC() as comm:
            ret = comm.Discover()
            if ret.Value:
                for device in ret.Value:
                    if device.DeviceID == 24 and device.ProductCode in self.product_codes:
                        hmis.append(device.IPAddress)
        if hmis:
            self.ip_list['values'] = hmis
            self.ip_list.current(0)

    def _get_runtime_files(self, event=None):
        """ Get the list of MER files that exist
        on the PanelView
        """
        self.mer_list.delete(0, tk.END)
        ip_address = self.ip_list.get()
        if ip_address:
            try:
                meu = MEUtility(ip_address)
                stuff = meu.get_terminal_info()
                temp = stuff.device.startup_mer_file
                if temp.endswith(".mer"):
                    running_file = temp
                else:
                    running_file = None
            except:
                running_file = None
                self.log.info("GUI - Failed to fetch MER names")
                return

            for f in stuff.device.files:
                if f == running_file:
                    self.mer_list.insert('end', ">{}".format(f))
                else:
                    self.mer_list.insert('end', f)

    def _create_new_config(self):
        """ Create a new configuration file
        """
        my_docs = os.path.join(os.getenv("USERPROFILE"), "Documents")
        my_docs = my_docs.replace(os.sep, '/')
        self.log.info("GUI - No config file found, creating new one")
        self.config['general'] = {'theme':'dark',
                                  'delete_logs':'False',
                                  'run_at_start':'False',
                                  'replace_comms':'False',
                                  'overwrite_download':'False',
                                  'overwrite_upload':'False',
                                  'upload_path':my_docs,
                                  'discover_on_init':'True',
                                  'window_width':'500',
                                  'last_download_dir':'C:\\Users\\Public\\Public Documents\\RSView Enterprise\\ME\\Runtime',
                                  'last_download_mer':""}

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

        # set the default download path
        dir = self.config.get('general', 'last_download_dir')
        mer = self.config.get('general', 'last_download_mer')
        file_path = "{}\\{}".format(dir, mer)
        self.download_file_var.set(file_path)

    def _get_terminal_info(self):
        """ Log the terminal info
        """
        ip_address = self.ip_list.get()
        meu = MEUtility(ip_address, ignore_terminal_valid=True)
        try:
            response = meu.get_terminal_info()
            for item in response.device.log:
                self.log.info("GUI - Terminal Info: {}".format(item))
            self.log.info("GUI - Terminal firmware: {}".format(response.device.me_version))
            self.log.info("GUI - Helper version: {}".format(response.device.helper_version))
            self.log.info("GUI - Product Code:{}".format(response.device.product_code))
            self.log.info("GUI - {}".format(response.device.product_name))
            messagebox.showinfo("Complete", "See log file for terminal details")
        except Exception as e:
            self.log.info("GUI - Failed to get terminal info, {}".format(e))
            messagebox.showerror("Failed", "Could not get terminal info, see log file")

    def connection_thread(self):
        """ Thread to get the IP from the UI
        """
        def worker():
            while True:
                path_copy = self.ip_list.get()
                time.sleep(4)
                self.queue.put(path_copy)
        threading.Thread(target=worker, daemon=True).start()

    def check_queue(self):
        """ Receive data from the PanelView check thread
        """
        try:
            while True:
                value = self.queue.get_nowait()
                self.check_panelview_connection(value)
        except queue.Empty:
            pass
        self.after(100, self.check_queue)

    def check_panelview_connection(self, value):
        """ Check to see if a PanelView is found at the user entered path
        """
        ip_address, route = self.convert_route(value)
        if ip_address:
            with pylogix.PLC(ip_address) as comm:
                comm.SocketTimeout = 1
                if route:
                    comm.Route = route
                try:
                    ret = comm.GetDeviceProperties()
                    if ret.Status == "Success" and ret.Value.DeviceID == 24:
                        self.canvas.itemconfig(self.connected, fill="green")
                    else:
                        self.canvas.itemconfig(self.connected, fill="red")
                except:
                    self.canvas.itemconfig(self.connected, fill="red")
        else:
            self.canvas.itemconfig(self.connected, fill="red")

    def convert_route(self, value):
        """ Convert the user entered network path to an
        IP address and route that pylogix will understand
        """
        route_path = value
        path_array = route_path.split(",")

        # validate IP address
        try:
            ipaddress.ip_address(path_array[0])
            ip_address = path_array[0]
        except:
            ip_address = None
        path_array.pop(0)

        # validate route is 2 segments
        if path_array:
            if len(path_array) > 0 and len(path_array) % 2 == 0:
                route = path_array
            else:
                route = None
        else:
            route = None

        # convert route integer segments
        if route:
            updated_route = []
            for segment in route:
                try:
                    updated_route.append(int(segment))
                except:
                    updated_route.append(segment)
            updated_route = [updated_route[i:i + 2] for i in range(0, len(updated_route), 2)]
        else:
            updated_route = route

        return ip_address, updated_route

    def browse_upload_directory(self):
        """ Select new upload directory
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.upload_path_var.set(folder_path)

    def progress_callback(self, description: str, total_bytes: int, current_bytes: int):
        progress = 100* current_bytes / total_bytes
        self.progress_bar["value"] = progress
        root.update_idletasks()

    def upload(self):
        """ Upload all applications from the terminal
        """
        if not os.path.isdir(self.upload_path_var.get()):
            messagebox.showerror("Error", "Please choose a directory to upload to.")
            return
        indexes = self.mer_list.curselection()
        if indexes:
            selected = indexes[0]
            item = self.mer_list.get(selected)
            if item.startswith(">"):
                item = item[1:]
            try:
                ip_address = self.ip_list.get()
                upload_path = self.upload_path_var.get() + "/" + item
                overwrite = self.overwrite_upload_var.get()
                meu = MEUtility(ip_address)
                stuff = meu.upload(upload_path, self.progress_callback, overwrite=overwrite)
                messagebox.showinfo("Information", "Uploading {} complete".format(item))
            except Exception as e:
                messagebox.showerror("Error", "Failed to upload {}".format(e))
        else:
            messagebox.showinfo("Information", "No MER was selected")

        self.progress_bar["value"] = 0

    def upload_all(self):
        """ Upload all applications from the terminal
        """
        if not os.path.isdir(self.upload_path_var.get()):
            messagebox.showerror("Error", "Please choose a directory to upload to.")
            return

        ip_address = self.ip_list.get()
        upload_path = self.upload_path_var.get()
        overwrite = self.overwrite_upload_var.get()
        try:
            meu = MEUtility(ip_address)
            stuff = meu.upload_all(upload_path, self.progress_callback, overwrite=overwrite)
            messagebox.showinfo("Information", "Upload complete")
        except Exception as e:
            messagebox.showerror("Error", "Something went wrong, {}".format(e))
        
        self.progress_bar["value"] = 0

    def browse_download_file(self):
        """ Open system file picker
        """
        filetypes = [('MER files', '*.mer')]
        init_dir = self.config.get('general', 'last_download_dir')
        file_name = filedialog.askopenfilename(filetypes=filetypes, initialdir=init_dir)
        if file_name:
            self.download_file_var.set(file_name)

            m = mer(file_name)
            file_version = m.get_version()[1:]
            file_version = int(file_version.split(".")[0])
            self.log.info("GUI - MER selected for download is version {}".format(file_version))
        else:
            self.log.info("GUI - No MER file selected")

    def download(self):
        """ Download MER file to PanelView
        """
        ip_address = self.ip_list.get()
        mer_path = self.download_entry.get()
        overwrite = self.overwrite_download_var.get()
        replace_comms = self.replace_comms_var.get()
        delete_logs = self.delete_logs_var.get()
        run_at_start = self.run_on_start_var.get()

        if ip_address == "":
            messagebox.showwarning("Uh-oh", "No IP address was entered")
            return
        if mer_path == "":
            messagebox.showwarning("Uh-oh", "No MER file was selected to download")
            return
        try:
            # get MER file version
            m = mer(mer_path)
            file_version = m.get_version()[1:]
            file_version = int(file_version.split(".")[0])
            meu = MEUtility(ip_address)
            terminal_info = meu.get_terminal_info()
            terminal_version = terminal_info.device.me_version
            terminal_version = int(terminal_version.split(".")[0])

            self.log.info("GUI - file_version {}, terminal_version {}".format(file_version, terminal_version))

            protection_status = m.get_protection()
            if protection_status[0] >= 1:
                messagebox.showwarning("Warning", "Your mer file was set to never allow conversion.  Anyone who uploads this won't be allowed to restore it.")

            if file_version > terminal_version:
                messagebox.showwarning("Abort!", "Your MER file version ({}) is newer than the terminal firmware ({})".format(
                    file_version, terminal_info.device.version_major))
                return
            stuff = meu.download(mer_path,
                                 self.progress_callback, 
                                 overwrite=overwrite,
                                 delete_logx=delete_logs,
                                 replace_comms=replace_comms,
                                 run_at_starupt=run_at_start)
            messagebox.showinfo("Success", "Download complete!")
            # update config
            self.config.set('general', 'last_download_dir', os.path.dirname(mer_path))
            self.config.set('general', 'last_download_mer', os.path.basename(mer_path))
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            messagebox.showerror("Error", "Failed to download MER, {}".format(e))
        
        self.progress_bar["value"] = 0

    def set_dark_theme(self):
        """ Switch the current theme to dark,
        update the drop down menu
        """
        self.tk.call("set_theme", "dark")
        self.dark_theme_var.set(1)
        self.light_theme_var.set(0)

    def set_light_theme(self):
        """ Switch the current theme to light,
        update the drop down menu
        """
        self.tk.call("set_theme", "light")
        self.dark_theme_var.set(0)
        self.light_theme_var.set(1)

    def open_log(self):
        """ Open the log file in a text editor
        """
        subprocess.Popen(["notepad", self.log_file])

    def save_config(self):
        """ Save the current settings to the config file
        """
        if self.main.winfo_width() == 1:
            w = self.window_width
        else:
            w = self.main.winfo_width()
        if self.dark_theme_var.get():
            self.config.set('general', 'theme', 'dark')
        else:
            self.config.set('general', 'theme', 'light')
        self.config.set('general', 'overwrite_upload', str(self.overwrite_upload_var.get()))
        self.config.set('general', 'overwrite_download', str(self.overwrite_download_var.get()))
        self.config.set('general', 'replace_comms', str(self.replace_comms_var.get()))
        self.config.set('general', 'delete_logs', str(self.delete_logs_var.get()))
        self.config.set('general', 'run_at_start', str(self.run_on_start_var.get()))
        self.config.set('general', 'upload_path', str(self.upload_path_var.get()))
        self.config.set('general', 'discover_on_init', str(self.discover_var.get()))
        self.config.set('general', 'window_width', str(w))

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def close(self):
        """ Exit app
        """
        self.stop_thread.set()
        self.log.info("GUI - User exit requested")
        sys.exit()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("A Better Transfer Utility? Maybe? v{}".format(__version__))
    root.resizable(True, False)
    app = Window(root)
    root.mainloop()
