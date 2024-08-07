import tkinter as tk
from modules.extension_tk import center_window
import requests
from tkinter import messagebox


class ProfileWin(tk.Toplevel):
    def __init__(self, parent, type_, session):
        super().__init__(parent)
        self.geometry(center_window(self, 500, 400))
        self.title(f"Список {type_} профилей")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.type_ = type_
        self.session = session
        self.gpon = None

        self.choise_gpon()

    def clear_childs(self):
        for widget in self.winfo_children():
            widget.destroy()

    def choise_gpon(self):
        container = tk.Frame(self)
        container.grid(row=0, column=0)
        tk.Label(container, text="Выберите нужный Gpon-блок").grid(row=0, column=0, columnspan=2)
        tk.Button(container, text="Пятиэтажка", width=15, command=self.etag_).grid(row=1, column=0)
        tk.Button(container, text="Гараж", width=15, command=self.garage_).grid(row=1, column=1)

    def insert_text(self, txt):
        self.clear_childs()
        text = tk.Text(self)
        text.grid(row=0, column=0, sticky="nsew")
        for pfl in txt:
            pfl_id = f"ID: {pfl['id']}".ljust(15)
            pfl_bind = f"Bind: {pfl['bind']}".ljust(15)
            pfl_name = f"Name: {pfl['name']}\n"
            str_ = pfl_id + pfl_bind + pfl_name
            text.insert(tk.END, str_)

    def etag_(self):
        self.clear_childs()
        self.gpon = "etag"
        tk.Label(self, text="Загрузка..").grid(row=0, column=0)
        self.update()
        self.request()

    def garage_(self):
        self.clear_childs()
        self.gpon = "garage"
        tk.Label(self, text="Загрузка..").grid(row=0, column=0)
        self.update()
        self.request()

    def request(self):
        try:
            url = f"http://{self.session['ip']}:{self.session['port']}/gpon/profile/{self.type_}"
            payload = {
                "login": self.session["login"],
                "passw": self.session["passw"],
                "gpon": self.gpon
            }

            response = requests.post(url, payload, timeout=3)
            if response.status_code == 200:
                resp = response.json()
                if "error" in resp:
                    messagebox.showerror("Error", resp["error"], parent=self)
                    self.destroy()
                    return

                self.insert_text(resp)
        except Exception as exc:
            messagebox.showerror("error", str(exc), parent=self)
            self.destroy()
