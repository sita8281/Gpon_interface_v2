import tkinter as tk
from tkinter import messagebox
from modules.extension_tk import center_window
from modules.main_page import MainPage
from win_modules.auth_win import AuthWin
from win_modules.search_sn_win import SearchSnWin
from win_modules.auto_register_win import RegisterWin
from win_modules.service_ports_win import ServicePortsWin
from win_modules.mac_table_win import MacTableWin
from win_modules.signal_table_win import SignalTableWin
from win_modules.traffic_win import TrafficWin
from win_modules.profiles_gpon_win import ProfileWin
from modules.buttons_panel_main_module import Buttons
from modules.down_panel import DownPanel
import requests
from threading import Thread


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry(center_window(self, 1400, 800))
        self.minsize(width=850, height=750)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.title("Huawei Gpon Интерфейс")
        self.iconphoto(True, tk.PhotoImage(file="src/images/icon16.png"))

        self._session = {}
        self.firmware_version = 0.01
        self.wait_window(AuthWin(self, width=400, height=250, title="Подключение к серверу"))  # ожидание авторизации

        file_menu = tk.Menu(tearoff=0)
        file_menu.add_command(label="Сохранить изменения: Гараж", command=lambda: self.save_command("garage"))
        file_menu.add_command(label="Сохранить изменения: Пятиэтажка", command=lambda: self.save_command("etag"))
        file_menu.add_command(label="Config HTTP-Server", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Выйти", command=self.destroy)

        advanced_menu = tk.Menu(tearoff=0)
        advanced_menu.add_command(label="Показать список Srv-Profile", command=lambda: ProfileWin(self, "srv", self._session))
        advanced_menu.add_command(label="Показать список Line-Profile", command=lambda: ProfileWin(self, "line", self._session))

        self.left_panel = Buttons(self, self._session)
        self.left_panel.grid(row=0, column=0, sticky="ns")

        self.main_frame = MainPage(self, self._session)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.down_panel = DownPanel(
            self,
            ip=self._session["ip"],
            user=self._session["login"],
            port=self._session["port"]
        )
        self.down_panel.grid(row=1, column=0, columnspan=2, sticky="w")

        self._global_bind()

        menu = tk.Menu(tearoff=0)
        menu.add_cascade(label="Файл", menu=file_menu)
        menu.add_cascade(label="Line и Srv профили", menu=advanced_menu)
        self.config(menu=menu)

    def _global_bind(self):
        """Связь разных модулей и объектов"""
        self.left_panel.search_sn["command"] = lambda: SearchSnWin(self, self._session, self.main_frame.tree.open_port)
        self.left_panel.reg_ont["command"] = lambda: RegisterWin(self, self._session)
        self.left_panel.srv_settinggs["command"] = lambda: ServicePortsWin(self, self._session)
        self.left_panel.traffic["command"] = lambda: TrafficWin(self, self._session, self.main_frame.tree.get_selection_port())
        self.left_panel.mac_address["command"] = lambda: MacTableWin(self, self.main_frame.tree.get_selection_gpon())
        self.left_panel.signal["command"] = lambda: SignalTableWin(self, self.main_frame.tree.get_selection_port())

    @property
    def session(self):
        return self._session

    def send_save(self, gpon):
        payload = {}
        url = f"http://{self.session['ip']}:{self.session['port']}/save"

        payload["login"] = self.session["login"]
        payload["passw"] = self.session["passw"]
        payload["gpon"] = gpon
        try:
            requests.post(url=url, data=payload, timeout=10)
        except requests.exceptions.RequestException:
            pass

    def save_command(self, gpon):
        Thread(target=self.send_save, args=(gpon,)).start()
        messagebox.showinfo("Команда отправлена", "Команда </save> отправлена на Gpon блок", parent=self)


if __name__ == "__main__":
    app = App()
    app.mainloop()
