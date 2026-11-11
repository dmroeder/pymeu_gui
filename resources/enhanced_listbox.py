import tkinter as tk
import tkinter.font as tkfont


class EnhancedListbox(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.items = []
        self.selected = None

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=2, relief="sunken")
        # self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure( scrollregion=self.canvas.bbox("all")))

        self.window = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        # self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))

    def insert(self, index, text, bold=False, fg=None):
        font = ("Arial", 10, "bold" if bold else "normal")

        label = tk.Label(self.frame, text=text, font=font, foreground=fg, anchor="w", padx=5, pady=2)

        label.pack(fill="x")
        label.bind("<Button-1>", lambda e, w=label: self.select(w))
        self.items.append(label)

    def select(self, widget):
        if self.selected:
            self.selected.configure(bg=self.frame.cget("bg"))

        self.selected = widget
        widget.configure(bg="#007fff")

    def delete(self, first, last=None):
        if last is None:
            last = first

        if last == tk.END:
            last = len(self.items) - 1

        for index in range(last, first - 1, -1):
            if 0 <= index < len(self.items):
                self.items[index].destroy()
                self.items.pop(index)

        self.selected = None

    def get(self, index):
        return self.items[index].cget("text")
