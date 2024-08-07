import tkinter as tk
from tkinter import messagebox
from modules.extension_tk import center_window
import winsound
from threading import Thread
import requests
import time


class WorkerPort(Thread):
    def __init__(self, session, window, data):
        super().__init__(daemon=True)

        self.session = session
        self.window = window
        self.data = data
        self.kill_flag = False

        self.current_speed = {"up": "0", "down": "0"}

        try:
            vlan = data[3]
        except IndexError:
            vlan = "1"

        self.payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": data[0],
            "slot": data[1],
            "port": data[2],
            "vlan": vlan
        }

    def run(self):
        while True:
            if self.kill_flag:
                return
            try:
                self.request()
            except Exception:
                pass

    def request(self):
        url = f"http://{self.session['ip']}:{self.session['port']}/traffic/port"
        response = requests.post(url=url, data=self.payload, timeout=6)

        if response.status_code == 200:
            resp = response.json()
            if "error" in resp:
                time.sleep(0.5)
                return
            self.current_speed = resp
        else:
            self.window.destroy()
            self.kill_flag = True
            return

    def kill(self):
        self.kill_flag = True


class WorkerVlan(WorkerPort):
    def request(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.data[0],
            "vlan": self.data[3]
        }

        url = f"http://{self.session['ip']}:{self.session['port']}/traffic/vlan"
        response = requests.post(url=url, data=payload, timeout=10)

        if response.status_code == 200:
            resp = response.json()
            if "error" in resp:
                time.sleep(0.5)
                return
            self.current_speed = resp
        else:
            self.window.destroy()
            self.kill_flag = True
            return


class CustomMsgBox(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry(center_window(self, 320, 210))
        self.grab_set()
        self.iconphoto(False, tk.PhotoImage(file="src/images/warning16.png"))
        self.resizable(False, False)
        self.title("Не выбран элемент")
        winsound.PlaySound("SystemAsterisk", winsound.SND_ASYNC)

        self.canvas = tk.Canvas(self, height=130, width=250, highlightthickness=0, relief="sunken", bd=2)
        self.img = tk.PhotoImage(file="src/images/example1.png")
        self.image = self.canvas.create_image(0, 0, anchor='nw', image=self.img)
        self.canvas.grid(row=0, column=0, pady=5)

        self.label = tk.Label(self, text="Выберите порт из главного списка (см. картинку выше)")
        self.label.grid(row=1, column=0)
        tk.Button(self, text="OK", width=12, command=self.destroy).grid(row=2, column=0, sticky="e", pady=5, padx=10)


class TrafficWin(tk.Toplevel):
    def __init__(self, parent, session, get_port_callback):
        super().__init__(parent)
        self.get_port = get_port_callback
        self.session = session
        self.iconphoto(False, tk.PhotoImage(file="src/images/speed16.png"))
        self.title("Загрузка портов и VLANs")

        self.thread = None

        self.geometry(center_window(self, 500, 400))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.close_window)
        if self.get_port:
            self.method_ask()
        else:
            self.update()
            window = CustomMsgBox(self)
            self.wait_window(window)
            self.destroy()

    def clear_childs(self):
        for child in self.winfo_children():
            child.destroy()

    def close_window(self):
        if self.thread:
            self.thread.kill()
        self.destroy()

    def method_ask(self):
        container = tk.Frame(self, width=350)
        container_vlan = tk.Frame(container)
        text_label = tk.Label(container, text="Выберите способ оторбажения скорости траффика")
        port_button = tk.Button(container, text="Скорость в VLAN", command=self.select_vlan)
        vlan_button = tk.Button(container, text="Скорость на порту", command=self.select_port)
        self.vlan_entry = tk.Entry(container_vlan, width=5, bd=2)
        vlan_label = tk.Label(container_vlan, text="VLAN ID")

        container.grid(row=0, column=0)
        text_label.grid(row=0, column=0, columnspan=2)
        port_button.grid(row=1, column=0)
        vlan_button.grid(row=1, column=1)
        container_vlan.grid(row=2, column=0, pady=2)
        self.vlan_entry.grid(row=0, column=1)
        vlan_label.grid(row=0, column=0)

    def show_traffic(self, vlan=None):
        # self.columnconfigure(0, weight=0)
        # self.rowconfigure(0, weight=0)

        container = tk.Frame(self)

        if self.get_port[0] == "etag":
            gpon = "Пятиэтажка"
        else:
            gpon = "Гараж"

        self.gpon_label = tk.Label(container, text=f"Gpon-блок: {gpon}")
        if not vlan:
            self.slot_label = tk.Label(container, text=f"Cлот: {self.get_port[1]}")
            self.port_label = tk.Label(container, text=f"Порт: {self.get_port[2]}")
            self.slot_label.grid(row=1, column=0)
            self.port_label.grid(row=2, column=0)
        else:
            self.vlan_label = tk.Label(container, text=f"VLAN ID: {vlan}")
            self.vlan_label.grid(row=1, column=0)

        self.label_up = tk.Label(container, text=f"Upload: ... Mb/s", font=("Segoe UI", 20, "bold"), foreground="Blue")
        self.label_down = tk.Label(container, text=f"Download: ... Mb/s", font=("Segoe UI", 20, "bold"), foreground="Red")

        container.grid(row=0, column=0)
        self.gpon_label.grid(row=0, column=0)

        tk.Frame(self).grid(row=3, column=0, pady=20)
        self.label_up.grid(row=4, column=0, sticky="w")
        self.label_down.grid(row=5, column=0, sticky="w")

    def vlan_validate(self, vlan):
        try:
            vl = int(vlan)
            if 0 < vl < 4096:
                return True
        except Exception:
            pass

    def select_port(self):
        print(self.get_port)
        self.clear_childs()
        self.thread = WorkerPort(session=self.session, window=self, data=self.get_port)
        self.thread.start()
        self.show_traffic()
        self.polling_thread()

    def select_vlan(self):
        data = self.vlan_entry.get()
        if data:
            if self.vlan_validate(data):
                self.clear_childs()

                self.thread = WorkerVlan(session=self.session, window=self, data=list(self.get_port) + [data])
                self.thread.start()
                self.show_traffic(vlan=data)
                self.polling_thread()

            else:
                messagebox.showwarning("Формат VLAN", "Допустимый диапазон VLAN ID: 1 - 4096", parent=self)
        else:
            messagebox.showwarning("Пустое поле", "Поле VLAN ID не должно оставаться пустым", parent=self)

    def polling_thread(self):
        down = round(float(self.thread.current_speed["down"]), 2)
        up = round(float(self.thread.current_speed["up"]), 2)
        self.after(500, self.polling_thread)
        self.label_up.config(text=f"Upload: {up} Mb/s", anchor="w")
        self.label_down.config(text=f"Download: {down} Mb/s", anchor="w")
