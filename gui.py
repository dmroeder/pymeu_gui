import os
import pylogix
import sys
import tkinter as tk

from mer_tools import mer
from pymeu import MEUtility
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

""" TODO:
Add logging
Add file dropdowns maybe?
Add open upload directory
"""


class Window(tk.Frame):

    def __init__(self, main=None):
        tk.Frame.__init__(self, main)
        self.main = main

        current_path = os.path.dirname(__file__)
        current_path = current_path.replace(os.sep, '/')

        tcl_file = self._get_file("resources/azure.tcl")
        self.tk.call("source", tcl_file)
        self.tk.call("set_theme", "dark")

        # variables
        self.mer_file_var = tk.StringVar()
        self.ip_address_var = tk.StringVar()
        self.upload_path_var = tk.StringVar()
        self.download_file_var = tk.StringVar()
        self.overwrite_upload_var = tk.IntVar()
        self.overwrite_download_var = tk.IntVar()
        self.replace_comms_var = tk.IntVar()
        self.delete_logs_var = tk.IntVar()
        self.run_on_start_var = tk.IntVar()

        self.upload_path_var.set(current_path)
        self.overwrite_download_var.set(1)

        # settings frame
        self.frame1 = ttk.LabelFrame(self.main, text="Settings")
        self.ip_label = ttk.Label(self.frame1, text="HMI IP Address:")
        self.ip_list = ttk.Combobox(self.frame1)
        self.ip_list.bind("<<ComboboxSelected>>", self._get_runtime_files)

        # upload frame
        self.frame2 = ttk.LabelFrame(self.main, text="Upload MER")
        self.upload_label = ttk.Label(self.frame2, text="Upload path:")
        self.upload_entry = ttk.Entry(self.frame2, textvariable=self.upload_path_var)
        self.mer_list = tk.Listbox(self.frame2)
        self.upload_browse_button = ttk.Button(self.frame2, text="...", command=self.browse_upload_directory)
        self.upload_button = ttk.Button(self.frame2, text="Upload Selected", command=self.upload)
        self.upload_all_button = ttk.Button(self.frame2, text="Upload All", command=self.upload_all)
        self.overwrite_upload_cb = ttk.Checkbutton(self.frame2, text="Overwrite existing files on upload?",
                                                   variable=self.overwrite_upload_var,
                                                   onvalue=1, offvalue=0)

        # download frame
        self.frame3 = ttk.LabelFrame(self.main, text="Download MER")
        self.download_label = ttk.Label(self.frame3, text="File to Download:")
        self.download_entry = ttk.Entry(self.frame3, textvariable=self.download_file_var)
        self.download_browse_button = ttk.Button(self.frame3, text="...", command=self.browse_download_file)
        self.download_button = ttk.Button(self.frame3, text="Download", command=self.download)
        self.overwrite_download_cb = ttk.Checkbutton(self.frame3, text="Overwrite file?",
                                                     variable=self.overwrite_download_var,
                                                     onvalue=1, offvalue=0)
        self.replace_comms_cb = ttk.Checkbutton(self.frame3, text="Replace communications? (hint, you should)",
                                                variable=self.replace_comms_var,
                                                onvalue=1, offvalue=0)
        self.delete_logs_cb = ttk.Checkbutton(self.frame3, text="Delete logs?",
                                              variable=self.delete_logs_var,
                                              onvalue=1, offval=0)
        self.run_on_start_cb = ttk.Checkbutton(self.frame3, text="Run at startup?",
                                               variable=self.run_on_start_var,
                                               onvalue=1, offvalue=0)

        self.init_window()
        self._find_panelview_ip()
        self._get_runtime_files()

    def init_window(self):
        """ Place all GUI items
        """

        # settings frame
        self.frame1.pack(padx=5, pady=10, fill=tk.X)
        self.frame1.grid_columnconfigure(0, weight=0)
        self.frame1.grid_columnconfigure(1, weight=1)
        self.ip_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.ip_list.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)

        # upload frame
        self.frame2.pack(padx=5, pady=10, fill=tk.X)
        self.frame2.grid_columnconfigure(0, weight=0)
        self.frame2.grid_columnconfigure(1, weight=1)
        self.upload_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.E)
        self.upload_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.E+tk.W)
        self.upload_browse_button.grid(row=0, column=3, padx=5, pady=5)
        self.mer_list.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W+tk.E)
        self.overwrite_upload_cb.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.upload_button.grid(row=2, column=2, padx=5, pady=5)
        self.upload_all_button.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)

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
                    if device.DeviceID == 24:
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
            try:
                ip_address = self.ip_list.get()
                upload_path = self.upload_path_var.get() + "/" + item
                overwrite = self.overwrite_upload_var.get()
                meu = MEUtility(ip_address)
                stuff = meu.upload(upload_path, overwrite=overwrite)
                messagebox.showinfo("Information", "Uploading {} complete".format(item))
            except Exception as e:
                messagebox.showerror("Error", "Failed to upload {}".format(e))
        else:
            messagebox.showinfo("Information", "No MER was selected")

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
            stuff = meu.upload_all(upload_path, overwrite=overwrite)
            messagebox.showinfo("Information", "Upload complete")
        except Exception as e:
            messagebox.showerror("Error", "Something went wrong, {}".format(e))

    def browse_download_file(self):
        """ Open system file picker
        """
        filetypes = [('MER files', '*.mer')]
        file_name = filedialog.askopenfilename(filetypes=filetypes)
        self.download_file_var.set(file_name)

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
            terminal_version = int(terminal_info.device.version_major)

            protection_status = m.get_protection()
            if protection_status[0] >= 1:
                messagebox.showwarning("Warning", "Your mer file was set to never allow conversion.  Anyone who uploads this won't be allowed to restore it.")

            if file_version > terminal_version:
                messagebox.showwarning("Abort!", "Your MER file version ({}) is newer than the terminal firmware ({})".format(
                    file_version, terminal_info.device.version_major))
                return
            stuff = meu.download(mer_path, overwrite=overwrite,
                                 delete_logx=delete_logs,
                                 replace_comms=replace_comms,
                                 run_at_starupt=run_at_start)
            messagebox.showinfo("Success", "Download complete!")
        except Exception as e:
            messagebox.showerror("Error", "Failed to download MER, {}".format(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("620x600")
    root.title("A Better Transfer Utility? Maybe?")
    root.resizable(False, False)
    app = Window(root)
    root.mainloop()
