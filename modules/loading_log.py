from modules.loading_animation_2 import LoadingAnimation
import tkinter as tk


class LoadingLog(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1)

        self.grid_row = 0

        self.loading = LoadingAnimation(self, 50, 50)
        self.loading.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        self.labels_frame = tk.Frame(self)
        self.labels_frame.grid(row=0, column=1, pady=10, sticky="nw")

    def insert_log(self, msg, fnt="normal", background=None, foreground=None):
        if self.grid_row == 13:
            self.clear_log()

        label = tk.Label(self.labels_frame, text=msg, background=background, foreground=foreground, font=("Segoe UI", 9, fnt))
        label.grid(row=self.grid_row, column=0, sticky="w")
        self.grid_row += 1



    def clear_log(self):
        self.grid_row = 0
        for widget in self.labels_frame.winfo_children():
            widget.destroy()
