import requests
import pickle
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from modules.extension_tk import center_window
from modules.extension_tk import EntryWithMenu
import webbrowser
import winsound


class UpdateWin(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry(center_window(self, 285, 180))
        self.grab_set()
        self.iconphoto(False, tk.PhotoImage(file="src/images/warning24.png"))
        self.resizable(False, False)
        self.title("")
        winsound.PlaySound("SystemAsterisk", winsound.SND_ASYNC)

        self.canvas = tk.Canvas(self, height=120, width=100, highlightthickness=0)
        self.img = tk.PhotoImage(file="src/images/warn_update.png")
        self.image = self.canvas.create_image(0, 0, anchor='nw', image=self.img)
        self.canvas.grid(row=0, column=0)

        self.label = tk.Label(self, text="Данная версия\nпрограммы устарела", font=("Segoe UI", 12, "bold"))
        self.label.grid(row=0, column=1)

        tk.Label(self, text="Скачать более свежую версию:", anchor="w").grid(row=1, column=0, columnspan=2, sticky="w")
        lbl = tk.Label(
            self,
            text="http://s.deil-00.ru/web/applications/gpon_client.exe",
            anchor="w",
            font=("Segoe UI", 9, 'underline'),
            cursor="hand2",
            foreground="blue"
        )
        lbl.grid(row=2, column=0, columnspan=2, sticky="w")
        lbl.bind("<Button-1>", self.open_web)

    def open_web(self, ev):
        try:
            webbrowser.open(url="http://s.deil-00.ru/web/applications/gpon_client.exe")
        except webbrowser.Error:
            pass




class AuthForm(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(1, weight=1)

        self.login_label = ttk.Label(self, text="Логин:", width=15,)
        self.passw_label = ttk.Label(self, text="Пароль:", width=15,)
        self.server_label = ttk.Label(self, text="Сервер:", width=15,)
        self.login_entry = EntryWithMenu(self, width=40)
        self.passw_entry = EntryWithMenu(self, width=40, show="*")
        self.server_entry = EntryWithMenu(self, width=40)

        self.login_label.grid(row=0, column=0)
        self.passw_label.grid(row=1, column=0)
        self.server_label.grid(row=2, column=0)
        self.login_entry.grid(row=0, column=1, sticky="we", pady=8)
        self.passw_entry.grid(row=1, column=1, sticky="we")
        self.server_entry.grid(row=2, column=1, sticky="we", pady=8)

        self.put_entryes()  # подгрузить данные из файла

    def get_entryes(self):
        return self.validate()

    def put_entryes(self):
        with open(file="src/temp.pickle", mode="rb") as file:
            data = pickle.load(file)
            self.login_entry.insert(tk.END, data[0])
            self.server_entry.insert(tk.END, data[1] + ':' + data[2])

    def validate(self):
        login = self.login_entry.get()
        passw = self.passw_entry.get()
        server = self.server_entry.get()

        if not login or not passw or not server:
            messagebox.showwarning("Предупреждение", "Поля не могут оставаться пустыми", parent=self)
            return
        try:
            if ':' in server:
                ip, port = server.split(':', 1)
                return dict(ip=ip, port=port, login=login, passw=passw)
        except Exception:
            pass
        messagebox.showwarning("Предупреждение", "Введен некорректный IP адрес\nПример: 10.10.1.1:5000", parent=self)


class AuthWin(tk.Toplevel):
    def __init__(self, parent, width, height, title):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.resizable(False, False)
        self.iconphoto(False, tk.PhotoImage(file="src/images/key.png"))
        self.geometry(center_window(self, width, height))
        self.withdraw()  # изначально свёрнуто
        self.protocol("WM_DELETE_WINDOW", lambda: self.parent.destroy())
        self.bind('<KeyPress-Return>', lambda ev: self.connect())

        self.canvas = tk.Canvas(self, height=100, width=400, bg='red', highlightthickness=0)
        self.img = tk.PhotoImage(file="src/images/main.png")
        self.image = self.canvas.create_image(0, 0, anchor='nw', image=self.img)
        self.canvas.grid(row=0, column=0)

        self.auth_form = AuthForm(self)
        self.auth_form.grid(row=1, column=0, sticky='n', pady=10)

        self.connect_button = ttk.Button(self, text="Подключиться", command=self.connect)
        self.connect_button.grid(row=2, column=0, sticky='e', padx=30)

        self.get_session()

    def get_session(self):
        """Получить данные REST сессии"""
        self.parent.withdraw()  # свернуть родителя
        self.deiconify()

    def close_handler(self):
        """Обработчик закрытия окна"""
        self.protocol("WM_DELETE_WINDOW", None)
        self.parent.deiconify()
        self.destroy()

    def connect(self):
        """Подключиться к серверу"""
        data = self.auth_form.get_entryes()
        if data:
            try:
                response = requests.post(f"http://{data['ip']}:{data['port']}/auth", data, timeout=2)
                if response.status_code == 200:

                    if self.parent.firmware_version != response.json()["version"]:
                        UpdateWin(self)
                        return

                    with open(file="src/temp.pickle", mode="wb") as file:
                        pickle.dump([data["login"], data["ip"], data["port"]], file)

                    self.parent._session = data  # передать данные сессии родителю
                    self.close_handler()

                elif response.status_code == 401:
                    messagebox.showwarning("Авторизация", "Неверный логин или пароль", parent=self)
                else:
                    messagebox.showwarning("Ошибка", "Неизвестная ошибка подключения", parent=self)
            except requests.exceptions.RequestException:
                messagebox.showwarning("HTTP", "Сервер не отвечает", parent=self)

