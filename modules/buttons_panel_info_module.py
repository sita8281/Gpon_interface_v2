import tkinter as tk


class Buttons(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.delete_img = tk.PhotoImage(file="src/images/delete.png")
        self.ping_img = tk.PhotoImage(file="src/images/ping.png")
        self.mac_img = tk.PhotoImage(file="src/images/mac.png")

        self.delete_button = tk.Button(self, width=100, height=100, text="Удалить ONT", image=self.delete_img, compound="top")
        self.delete_button.grid(row=0, column=0, padx=10)
        self.ping_button = tk.Button(self, width=100, height=100, text="Оптический пинг", image=self.ping_img, compound="top")
        self.ping_button.grid(row=0, column=1)
        self.mac_button = tk.Button(self, width=100, height=100, text="Найти логин\nили MAC-адрес", image=self.mac_img, compound="top")
        self.mac_button.grid(row=0, column=2, padx=10)
