import tkinter as tk
from tkinter import ttk
from modules.extension_tk import center_window, EntryCopy
from modules.loading_animation_2 import LoadingAnimation
from tkinter import messagebox
from threading import Thread
import requests


class SearchMacWin(tk.Toplevel):
    def __init__(self, parent, session, gpon, slot, port, onu_id, name):
        super().__init__(parent)
        self.geometry(center_window(self, 400, 300))
        # self.grab_set()
        self.title(f"Поиск MAC адреса - {name}")
        self.resizable(False, True)
        self.iconphoto(False, tk.PhotoImage(file="src/images/search.png"))

        self.session = session
        self.gpon = gpon
        self.slot = slot
        self.port = port
        self.onu_id = onu_id

        self.loading = LoadingAnimation(self, 50, 50)
        self.loading.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        self.grid_row = 0
        self.labels_frame = tk.Frame(self)
        self.labels_frame.grid(row=0, column=1, pady=10, sticky="nw")

        self._mouse_wheel_lock = True

    def mouse_leave(self, ev):
        self.canvas.unbind_all("<MouseWheel>")

    def mouse_enter(self, ev):
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)

    def mouse_wheel(self, ev):
        if self._mouse_wheel_lock:
            self.canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")

    def label_log(self, msg, state=None):
        label = tk.Label(self.labels_frame, text=msg)
        label.grid(row=self.grid_row, column=0, sticky="w")
        self.grid_row += 1

    def search(self):
        Thread(target=self.worker, daemon=True).start()

    def worker(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.gpon,
            "slot": self.slot,
            "port": self.port,
            "onu_id": self.onu_id,
        }
        self.after(10, lambda: self.label_log("Получение MAC адресов от сервера..."))
        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/mac/onu_id", data=payload)
        except requests.exceptions.RequestException:
            self.after(10, lambda: messagebox.showerror("Ошибка", "Внутренняя ошибка запроса"))
            self.after(10, self.destroy)
            return

        if response.status_code == 200:
            if response.json():
                self.mac_lst = response.json()
                self.after(10, self.view_mac)
                return
        self.after(10, lambda: messagebox.showwarning("MAC не найден", "Не удалось найти MAC адрес"))
        self.after(10, self.destroy)

    def view_mac(self):
        for child in self.winfo_children():
            child.destroy()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bd=0, highlightthickness=False)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.bind("<Leave>", self.mouse_leave)
        self.canvas.bind("<Enter>", self.mouse_enter)

        self.scrl_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrl_y.grid(row=0, column=1, sticky="ns")

        self.mac_frame = tk.Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.mac_frame, anchor='nw')
        self.canvas.config(yscrollcommand=self.scrl_y.set)

        self.user_img = tk.PhotoImage(file="src/images/user_carbon.png")

        for row, mac in enumerate(self.mac_lst):
            self.entry = EntryCopy(self.mac_frame, bd=2)
            self.get_login_btn = tk.Button(self.mac_frame, text="Логин", image=self.user_img, compound="right", command=self.button_command(mac, row))
            self.get_login_btn.grid(row=row, column=1, padx=2)
            self.entry.grid(row=row, column=0, pady=2, padx=15)
            self.entry.insert(tk.END, f"{mac}")

        self.after(200, lambda: self.canvas.config(scrollregion=self.mac_frame.bbox()))

    def button_command(self, mac, row):
        return lambda: self.get_login(mac, row)

    def get_login(self, mac, row):
        try:
            url = f"http://{self.session['ip']}:{self.session['port']}/pppoe"
            response = requests.post(url, data={"login": self.session["login"], "passw": self.session["passw"]}, timeout=3)
            if response.status_code == 200:
                res = response.json()
                if "error" in res:
                    messagebox.showerror("error", res["error"], parent=self)
                    return
                for login, mac_ in res:
                    if mac == mac_:
                        print(mac)
                        self.entry = EntryCopy(self.mac_frame, bd=2)
                        self.entry.grid(row=row, column=2, padx=5)
                        self.entry.insert(tk.END, login)
                        return
                else:
                    self.entry = EntryCopy(self.mac_frame, bd=2)
                    self.entry.grid(row=row, column=2, padx=5)
                    self.entry.insert(tk.END, "Логин не найден :(")
        except Exception:
            messagebox.showerror("Не удалось получить логин", "Внутренняя ошибка запроса", parent=self)





