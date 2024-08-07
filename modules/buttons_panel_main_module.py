import tkinter as tk
from win_modules.profiles_win import ProfileWin


class PanelButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            width=100,
            height=100,
            compound="top",
            background="#808080",
            activebackground="#808080",
            activeforeground="white",
            bd=1,
            relief="flat",
            foreground="white",
            **kwargs
        )

        self.bind("<Enter>", self.mouse_enter)
        self.bind("<Leave>", self.mouse_leave)

    def mouse_leave(self, ev):
        self["relief"] = "flat"
        # self["font"] = ("Segoe UI", 9, "")

    def mouse_enter(self, ev):
        self["relief"] = "raised"
        # self["font"] = ("Segoe UI", 9, "underline")


class Buttons(tk.Frame):
    def __init__(self, parent, session):
        super().__init__(parent, background="#808080")

        self.session = session

        self.user_reg_img = tk.PhotoImage(file="src/images/user_reg.png")
        self.srv_img = tk.PhotoImage(file="src/images/srv_settings.png")
        self.mac_img = tk.PhotoImage(file="src/images/mac_table.png")
        self.sn_img = tk.PhotoImage(file="src/images/sn.png")
        self.settings_img = tk.PhotoImage(file="src/images/settings.png")
        self.speed_img = tk.PhotoImage(file="src/images/speed.png")
        self.signal_img = tk.PhotoImage(file="src/images/signal.png")

        self.reg_ont = PanelButton(self, image=self.user_reg_img, text="Автопоиск и\nрегистрация ONT")
        self.reg_ont.grid(row=0, column=0, padx=2)
        self.srv_settinggs = PanelButton(self, image=self.srv_img, text="Service-Ports\nManager")
        self.srv_settinggs.grid(row=1, column=0, padx=2)
        self.traffic = PanelButton(self, image=self.speed_img, text="Загрузка портов\nи VLANs")
        self.traffic.grid(row=2, column=0, padx=2)
        self.search_sn = PanelButton(self, image=self.sn_img, text="Поиск по SN")
        self.search_sn.grid(row=3, column=0, padx=2)
        self.settings_sn = PanelButton(self, image=self.settings_img, text="Настройка\n VLAN-профилей",
                                       command=lambda: ProfileWin(self, self.session))
        self.settings_sn.grid(row=4, column=0, padx=2)
        self.mac_address = PanelButton(self, image=self.mac_img, text="Таблица\nMAC-Адресов")
        self.mac_address.grid(row=5, column=0, padx=2)
        self.signal = PanelButton(self, image=self.signal_img, text="Таблица уровней\nсигналов ONT")
        self.signal.grid(row=6, column=0, padx=2)


