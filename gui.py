import os
import tkinter as tk

from pymeu import MEUtility
from tkinter import messagebox
from tkinter import ttk


class Window(tk.Frame):

    def __init__(self, main=None):
        tk.Frame.__init__(self, main)
        self.main = main

        self.mer_file = tk.StringVar()
        self.mer_file.set("")

        self.ip_address = tk.StringVar()
        self.ip_address.set("192.168.1.11")

        self.overwrite_var = tk.IntVar()

        current_path = os.path.dirname(__file__) + "\\upload"
        self.upload_path = tk.StringVar()
        self.upload_path.set(current_path)

        self.frame1 = ttk.LabelFrame(self.main, text="Settings")
        self.ip_label = ttk.Label(self.frame1, text="HMI IP Address:")
        self.ip_entry = ttk.Entry(self.frame1, textvariable=self.ip_address)
        self.overwrite_cb = ttk.Checkbutton(self.frame1, text="Overwrite existing files on upload?",
                                            variable=self.overwrite_var,
                                            onvalue=1, offvalue=0)
        
        self.frame2 = ttk.LabelFrame(self.main, text="Upload")
        self.upload_lbl = ttk.Label(self.frame2, text="Upload path:")
        self.upload_entry = ttk.Entry(self.frame2, textvariable=self.upload_path)
        self.upload_button = ttk.Button(self.frame2, text="Upload All", command=self.upload_all)

        self.meu = MEUtility(self.ip_address.get())

        self.init_window()

    def init_window(self):
        """ Place all GUI items
        """
        self.frame1.pack(padx=5, pady=5, fill=tk.X)
        self.frame1.grid_columnconfigure(0, weight=0)
        self.frame1.grid_columnconfigure(1, weight=1)
        self.ip_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)
        self.overwrite_cb.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        self.frame2.pack(padx=5, pady=5, fill=tk.X)
        self.frame2.grid_columnconfigure(0, weight=0)
        self.frame2.grid_columnconfigure(1, weight=1)
        self.upload_lbl.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.upload_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E+tk.W)
        self.upload_button.grid(row=1, column=0, padx=5, pady=5)

    def upload_all(self):
        """ Upload all applications from the terminal
        """
        ip_address = self.ip_address.get()
        upload_path = self.upload_path.get()
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
