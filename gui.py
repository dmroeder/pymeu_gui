import os
import pylogix
import tkinter as tk

from pymeu import MEUtility
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

""" TODO:
Add logging
Add upload single
Add Download
Add file dropdowns maybe?
Add open upload directory
"""


class Window(tk.Frame):

    def __init__(self, main=None):
        tk.Frame.__init__(self, main)
        self.main = main

        current_path = os.path.dirname(__file__) + "\\upload"

        self.mer_file_var = tk.StringVar()
        self.ip_address_var = tk.StringVar()
        self.upload_path_var = tk.StringVar()
        self.overwrite_var = tk.IntVar()

        self.mer_file_var.set("")
        self.ip_address_var.set("192.168.1.11")
        self.upload_path_var.set(current_path)

        self.frame1 = ttk.LabelFrame(self.main, text="Settings")
        self.ip_label = ttk.Label(self.frame1, text="HMI IP Address:")
        self.ip_list = ttk.Combobox(self.frame1)

        self.frame2 = ttk.LabelFrame(self.main, text="Upload")
        self.upload_lbl = ttk.Label(self.frame2, text="Upload path:")
        self.upload_entry = ttk.Entry(self.frame2, textvariable=self.upload_path_var)
        self.mer_list = tk.Listbox(self.frame2)
        self.browse_button = ttk.Button(self.frame2, text="...", command=self.browse_upload_directory)
        self.upload_button = ttk.Button(self.frame2, text="Upload All", command=self.upload_all)

        self.overwrite_cb = ttk.Checkbutton(self.frame2, text="Overwrite existing files on upload?",
                                            variable=self.overwrite_var,
                                            onvalue=1, offvalue=0)

        self.init_window()
        self._find_panelview_ip()
        self._get_runtime_files()

    def init_window(self):
        """ Place all GUI items
        """
        self.frame1.pack(padx=5, pady=5, fill=tk.X)
        self.frame1.grid_columnconfigure(0, weight=0)
        self.frame1.grid_columnconfigure(1, weight=1)
        self.ip_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.ip_list.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)

        self.frame2.pack(padx=5, pady=5, fill=tk.X)
        self.frame2.grid_columnconfigure(0, weight=0)
        self.frame2.grid_columnconfigure(1, weight=1)
        self.upload_lbl.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.upload_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        self.mer_list.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        self.overwrite_cb.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.upload_button.grid(row=3, column=0, padx=5, pady=5)

    def _find_panelview_ip(self):
        """ Send list identity and save all HMI IP addresses
        that were discovered on the network to a list
        """
        hmis = []
        with pylogix.PLC() as comm:
            ret = comm.Discover()
            if ret.Value:
                for device in ret.Value:
                    if device.DeviceID == 24:
                        hmis.append(device.IPAddress)
        self.ip_list['values'] = hmis
        self.ip_list.current(0)

    def _get_runtime_files(self):
        """ Get the list of MER files that exist
        on the PanelView
        """
        self.mer_list.delete(0, tk.END)
        ip_address = self.ip_list.get()
        meu = MEUtility(ip_address)
        stuff = meu.get_terminal_info()
        for f in stuff.device.files:
            self.mer_list.insert('end', f)

    def browse_upload_directory(self):
        """ Select new upload directory
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.upload_path_var.set(folder_path)

    def upload_all(self):
        """ Upload all applications from the terminal
        """
        # ip_address = self.ip_address_var.get()
        ip_address = self.ip_list.get()
        upload_path = self.upload_path_var.get()
        overwrite = self.overwrite_var.get()
        try:
            meu = MEUtility(ip_address)
            stuff = meu.upload_all(upload_path, overwrite=overwrite)
            messagebox.showinfo("Information", "Upload complete")
        except Exception as e:
            messagebox.showerror("Error", "Something went wrong, {}".format(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("500x500")
    root.title("A Better Transfer Utility")
    root.resizable(False, False)
    app = Window(root)
    root.mainloop()
