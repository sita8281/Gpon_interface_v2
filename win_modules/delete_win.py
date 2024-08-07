import tkinter as tk
from threading import Thread
import requests
from modules.extension_tk import center_window
from modules.loading_animation_2 import LoadingAnimation
from tkinter import messagebox


class DeleteWin(tk.Toplevel):
    def __init__(self, parent, session, gpon, slot, port, onu_id, name):
        super().__init__(parent)
        self.geometry(center_window(self, 400, 300))
        self.grab_set()
        self.title(f"Удаление - {name}")
        self.resizable(False, False)

        self.session = session
        self.gpon = gpon
        self.slot = slot
        self.port = port
        self.onu_id = onu_id

        self.loading = LoadingAnimation(self, 50, 50)
        self.loading.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        self.grid_row = 0
        self.labels_frame = tk.Frame(self)
        self.labels_frame.grid(row=0, column=1, pady=10, sticky="n")

    def label_log(self, msg, state=None):
        if state == "success":
            messagebox.showinfo("Успешно", msg, parent=self)
            self.destroy()
        elif state == "error":
            messagebox.showerror("Ошибка", msg, parent=self)
            self.destroy()
        elif state == "warning":
            messagebox.showwarning("Предупреждение", msg, parent=self)
            self.destroy()
        else:
            label = tk.Label(self.labels_frame, text=msg)
            label.grid(row=self.grid_row, column=0, sticky="w")
            self.grid_row += 1

    def delete(self):
        Thread(target=self.worker, daemon=True).start()

    def worker(self):
        trouble = False
        try:
            srv_port = self.search_srv_port()
            if srv_port:
                self.after(10, lambda: self.label_log(f"Сервис порт найден: {srv_port}"))

                if not self.delete_srv_port(srv_port):
                    trouble = True
            else:
                trouble = True
                self.after(10, lambda: self.label_log("Не удалось найти service-port"))

            if self.delete_onu():
                self.save_config()
                if trouble:
                    self.after(10, lambda: self.label_log(msg="Удаление произведено частично\nONT удалена успешно\n"
                                                              "Service-port не был удалён\n"
                                                              "Возможно его не существовало", state="warning"))
                else:
                    self.after(10, lambda: self.label_log(msg="Удаление успешно завершено\n"
                                                              "Обновите список ONT", state="success"))
            else:
                self.after(10, lambda: self.label_log(msg="Не удалось удалить ONT\n"
                                                          "Возможно её уже не существует", state="error"))
        except requests.exceptions.RequestException:
            self.after(10, lambda: self.label_log(msg="Ошибка протокола\nhttp -> requests -> server", state="error"))

    def search_srv_port(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.gpon,
            "slot": self.slot,
            "port": self.port,
            "onu_id": self.onu_id,
        }
        self.after(10, lambda: self.label_log("Получение списка service-ports от сервера..."))
        response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/service_port_list", data=payload)
        self.after(10, lambda: self.label_log("Поиск service-port привязанного к ONT..."))
        if response.status_code == 200:
            for srv_data in response.json():
                if srv_data["onu_id"] != self.onu_id:
                    continue
                if srv_data["port"] != self.port:
                    continue
                if srv_data["slot"] != self.slot:
                    continue
                return srv_data["service_port"]

    def delete_srv_port(self, srv_port):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.gpon,
            "service_port": srv_port,
        }
        self.after(10, lambda: self.label_log("Удаление service-port..."))
        response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/del_service_port", data=payload)
        if response.status_code == 200:
            if "success" in response.json():
                self.after(10, lambda: self.label_log("Service-port успешно удалён"))
                return True
        self.after(10, lambda: self.label_log("Не удалось удалить service-port"))

    def delete_onu(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.gpon,
            "slot": self.slot,
            "port": self.port,
            "onu_id": self.onu_id,
        }
        self.after(10, lambda: self.label_log("Удаление ONT..."))
        response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/delete", data=payload)
        if response.status_code == 200:
            if "success" in response.json():
                self.after(10, lambda: self.label_log("ONT удалена успешно"))
                return True
        self.after(10, lambda: self.label_log(msg="Не удалось удалить ONT"))

    def save_config(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": self.gpon
        }
        self.after(10, lambda: self.label_log("Сохранение конфигурации..."))
        try:
            requests.post(f"http://{self.session['ip']}:{self.session['port']}/save", data=payload, timeout=2)
        except requests.exceptions.RequestException:
            pass
