import tkinter as tk
from tkinter import ttk


class DownPanel(tk.Frame):
    def __init__(self, parent, ip: str, port: str, user: str):
        super().__init__(parent)

        self.user = tk.Label(self, text=f"Текущий пользователь")
        self.user_ = tk.Label(self, text=user, relief="sunken", bd=1)
        self.sep = tk.Frame(self)
        self.ip = tk.Label(self, text=f"Сервер")
        self.ip_ = tk.Label(self, text=f"{ip}:{port}", relief="sunken", bd=1)

        self.user.grid(row=0, column=0)
        self.user_.grid(row=0, column=1, )
        self.sep.grid(row=0, column=2, sticky="ns", padx=10)
        self.ip.grid(row=0, column=3,)
        self.ip_.grid(row=0, column=4,)


