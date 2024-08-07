import tkinter
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from modules.extension_tk import center_window, EntryWithMenu
from modules.loading_log import LoadingLog
from threading import Thread
import requests
import re
from typing import Literal


class WorkerAutofind(Thread):
    def __init__(self, window, gpon):
        super().__init__(daemon=True)

        self.window = window
        self.session = window.session
        self.find_lst = []
        self.error = False
        self.kill_flag = False
        self.gpon = gpon

        self.ports_pool = {
            "etag": {"0/1": [str(i) for i in range(16)]},
            "garage": {"0/0": [str(i)for i in range(8)], "0/1": [str(i) for i in range(8)]}
        }

    def run(self):
        self.send_requests()

    def send_requests(self):
        slots = self.ports_pool[self.gpon]
        self.window.load.insert_log(msg=f"Сканирование Gpon блока запущено...")
        for slot in slots:
            self.window.load.clear_log()
            self.window.load.insert_log(msg=f"Проверка портов на слоте: {slot}...", fnt="bold")
            for port in slots[slot]:
                payload = {
                    "login": self.session["login"],
                    "passw": self.session["passw"],
                    "gpon": self.gpon,
                    "slot": slot,
                    "port": port
                }
                if self.kill_flag:
                    return
                try:
                    while True:
                        response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/autofind",
                                                 data=payload)

                        resp = response.json()
                        if "error" in resp:
                            self.window.load.insert_log(msg=f"Не удалось просканировать порт {port}", foreground="red")
                            self.window.load.insert_log(msg=f"Повторная попытка..")
                            continue
                        self.find_lst += resp
                        print(resp, port)
                        if resp:
                            self.window.load.insert_log(msg=f"Порт {port} просканирован (найдены ONT)", background="#ADFF2F")
                            # return
                        else:
                            self.window.load.insert_log(msg=f"Порт {port} просканирован")
                        break

                except Exception:
                    self.error = True
                    return


class WorkerReg(Thread):
    def __init__(self, window, gpon, name, profile, ont_type: [Literal["hg8245", "hg8310"]], selection_ont):
        super().__init__(daemon=True)

        self.session = window.session
        self.window = window
        self.gpon = gpon
        self.name = name
        self.profile = profile
        self.ont_type = ont_type
        self.sel_ont = selection_ont

        self.service_port = ""

    def run(self):
        try:
            service_port = self.free_service_port()
            pfl = self.get_profile_data()
            ont_id = self.reg_ont(pfl)
            self.reg_service_port(pfl_data=pfl, ont_id=ont_id, service_port=service_port)
            self.reg_native_vlan(pfl_data=pfl, ont_id=ont_id)
        except tkinter.TclError:
            return

        messagebox.showinfo(
            "Регистрация завершена",
            "ONT успешно зарегистрирована\n\n"
            f"ONT ID: {ont_id}\nService port: {service_port}\nVLAN: {pfl['vlan']}\n"
            f"Name: {self.name}\nModel: {self.ont_type}",
            parent=self.window
        )
        self.window.destroy()

    def free_service_port(self):
        self.window.load.insert_log(msg="Поиск свободного service-port..")
        try:
            self.session["gpon"] = self.gpon
            url = f"http://{self.session['ip']}:{self.session['port']}/next_free_index"
            payload = {"login": self.session["login"], "passw": self.session["passw"], "gpon": self.gpon}

            response = requests.post(url=url, data=payload)
            r = response.json()

            if "Next valid free service virtual port ID" in r:
                self.window.load.insert_log(
                    msg=f"Найденный свободный service-port:"
                        f" {r['Next valid free service virtual port ID']}"
                )
                return r["Next valid free service virtual port ID"]
        except Exception:
            pass
        messagebox.showerror(
            "ОШИБКА", "Не удалось завершить операцию поиска service-port\nПроцесс прерван.",
            parent=self.window
        )
        self.window.destroy()

    @property
    def normalize_sn(self):
        return self.sel_ont[0].split(' ')[0].strip()

    def reg_ont(self, pfl_data):
        error = ""
        self.window.load.insert_log(msg="Регистрация ONT..")
        try:
            self.session["gpon"] = self.gpon
            url = f"http://{self.session['ip']}:{self.session['port']}/register"
            payload = {
                "login": self.session["login"],
                "passw": self.session["passw"],
                "gpon": self.gpon,
                "slot": self.sel_ont[3],
                "port": self.sel_ont[4],
                "name": self.name,
                "sn": self.normalize_sn,
                "srv_profile": pfl_data["srv"],
                "line_profile": pfl_data["line"]
            }

            response = requests.post(url=url, data=payload)
            if response.status_code == 200:
                data = response.json()
                if "success" in data:
                    self.window.load.insert_log(msg=f"ONT успешно зарегистрирована на порту: {self.sel_ont[4]}")
                    return data["onu_id"]
                elif "Failure" in data:
                    error = data["Failure"]
                elif "error" in data:
                    error = data["error"]

                if error == "SN already exists":
                    error = f'Серийный номер уже прописан на Gpon блоке\nИ привязан к другой ONT\n\nSN: {self.normalize_sn}'

        except requests.exceptions.RequestException:
            error = "Ошибка соединения или протокола HTTP\nПопробуйте повторить процесс."
        except Exception:
            error = "Низкоуровневая ошибка программы.\nПроцесс прерван."
        messagebox.showerror("ОШИБКА", error,
                             parent=self.window)
        self.window.destroy()
        return

    def reg_service_port(self, pfl_data, ont_id, service_port):
        error = ""
        self.window.load.insert_log(msg="Добавление service-port..")
        try:
            self.session["gpon"] = self.gpon
            url = f"http://{self.session['ip']}:{self.session['port']}/add_service_port"
            payload = {
                "login": self.session["login"],
                "passw": self.session["passw"],
                "gpon": self.gpon,
                "slot": self.sel_ont[3],
                "port": self.sel_ont[4],
                "onu_id": ont_id,
                "gem": pfl_data["gem"],
                "vlan": pfl_data["vlan"],
                "service_port": service_port,
            }

            response = requests.post(url=url, data=payload)
            if response.status_code == 200:
                data = response.json()
                if "success" in data:
                    self.window.load.insert_log(
                        msg=f"Service-port {service_port} успешно добавлен, vlan: {pfl_data['vlan']}"
                    )
                    return
                elif "Failure" in data:
                    error = data["Failure"]
                elif "error" in data:
                    error = data["error"]


        except requests.exceptions.RequestException:
            error = "Ошибка соединения или протокола HTTP\nПопробуйте повторить процесс."
        except Exception:
            error = "Низкоуровневая ошибка программы.\nПроцесс прерван."
        messagebox.showerror("ОШИБКА", error,
                             parent=self.window)
        self.window.destroy()
        return

    def get_profile_data(self):
        self.window.load.insert_log(msg=f"Загрузка данных профиля: {self.profile}..")
        try:
            url = f"http://{self.session['ip']}:{self.session['port']}/profile/get"
            payload = {"login": self.session["login"], "passw": self.session["passw"]}

            response = requests.post(url=url, data=payload)
            pfls = response.json()

            for pfl in pfls:
                if pfl["name"] == self.profile:
                    self.window.load.insert_log(
                        msg=f"vlan={pfl['vlan']}"
                            f" gem={pfl['gem']}"
                            f" srv-profile={pfl['srv']}"
                            f" line-profile={pfl['line']}"
                    )
                    return pfl

        except Exception:
            pass
        messagebox.showerror("ОШИБКА", "Не удалось загрузить vlan-ПРОФИЛЬ с сервера\nПроцесс прерван.",
                             parent=self.window)
        self.window.destroy()
        return

    def reg_native_vlan(self, pfl_data, ont_id):
        print(self.ont_type)
        if self.ont_type != "hg8310":
            return
        error = ""
        self.window.load.insert_log(msg="Привязка Native-Vlan (Untagged)...")
        try:
            self.session["gpon"] = self.gpon
            url = f"http://{self.session['ip']}:{self.session['port']}/native_vlan"
            payload = {
                "login": self.session["login"],
                "passw": self.session["passw"],
                "gpon": self.gpon,
                "slot": self.sel_ont[3],
                "port": self.sel_ont[4],
                "vlan": pfl_data["vlan"],
                "onu_id": ont_id
            }

            response = requests.post(url=url, data=payload)
            if response.status_code == 200:
                data = response.json()
                if "success" in data:
                    self.window.load.insert_log(msg=f"Native-Vlan {pfl_data['vlan']} успешно привязан")
                    return
                elif "error" in data:
                    error = data["error"]

        except requests.exceptions.RequestException:
            error = "Ошибка соединения или протокола HTTP\nПопробуйте повторить процесс."
        except Exception:
            error = "Низкоуровневая ошибка программы.\nПроцесс прерван."
        messagebox.showerror("ОШИБКА", error,
                             parent=self.window)
        self.window.destroy()
        return


class RegisterWin(tk.Toplevel):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.session = session
        self.geometry(center_window(self, 400, 300))
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.grab_set()
        self.title("Регистрация ONT")
        # self.grab_release()

        self.hg_8310_img = tk.PhotoImage(file="src/images/hg8310.png")
        self.hg_8245_img = tk.PhotoImage(file="src/images/hg8245.png")
        self.unknown = tk.PhotoImage(file="src/images/unknown.png")
        s = ttk.Style()
        s.configure('q.Treeview', rowheight=50)

        self.choise_gpon()
        self.load = None
        self.check_thread_kill = False
        self.thread = None
        self.current_ont = None
        self.gpon = None
        self.selection_ont = None

    def user_close_window(self):
        ask = messagebox.askyesno(
            "Прерывание регистрации",
            "Вы уверены что хотите прервать регистрацию?"
            "Данное действие может привести к сбою",
            parent=self
        )
        if ask:
            self.close_window()

    def close_window(self):
        if self.thread:
            self.thread.kill_flag = True
        self.destroy()

    def clear_childs(self):
        for child in self.winfo_children():
            child.destroy()

    def run_autofind(self, gpon):
        self.clear_childs()
        self.show_loading()
        self.thread = WorkerAutofind(self, gpon)
        self.thread.start()
        self.autofind_check_thread()
        self.title("Поиск незарегистрированных ONT")

    def autofind_check_thread(self):
        if self.thread.is_alive():
            self.after(200, self.autofind_check_thread)
            return
        self.clear_childs()
        self.show_list(self.thread.find_lst, self.thread.gpon)

        self.gpon = self.thread.gpon

    def show_list(self, lst, gpon):
        unkown = False
        self.title("Список незарегистрированных ONT")
        self.geometry(center_window(self, 800, 400))
        self.lst = ttk.Treeview(self, selectmode="browse", columns=('sn', 'model', 'gpon', 'slot', 'port', 'ontid'),
                                height=20, style='q.Treeview')

        self.lst.column('#0', stretch=False, width=100)
        self.lst.column('sn', width=200)
        self.lst.column('model', width=100)
        self.lst.column('gpon', width=50)
        self.lst.column('slot', width=50)
        self.lst.column('port', width=50)
        self.lst.column('ontid', width=50)

        self.lst.heading('sn', text="SN")
        self.lst.heading('model', text="Model")
        self.lst.heading('gpon', text="Gpon")
        self.lst.heading('slot', text="Slot")
        self.lst.heading('port', text="Port")
        self.lst.heading('ontid', text="Number")

        self.lst.grid(row=0, column=0, sticky="nsew")

        current_ont = None

        for ont in lst:
            print(ont["Ont EquipmentID"])
            if ont["Ont EquipmentID"].find("310") != -1:
                img = self.hg_8310_img
                self.current_ont = "hg8310"
            elif ont["Ont EquipmentID"].find("245") != -1:
                img = self.hg_8245_img
                self.current_ont = "hg8245"
            else:
                img = self.unknown
                self.current_ont = "?"
            self.lst.insert("", index=tk.END, values=(
                ont["Ont SN"],
                ont["Ont EquipmentID"],
                gpon,
                ont["slot"],
                ont["port"],
                ont["Number"],
                self.current_ont
            ), image=img
            )

        self.button_reg = tk.Button(self, text="Зарегистрировать", command=self.click_reg_button)
        self.button_reg.grid(row=1, column=0, pady=5)

    def click_reg_button(self):
        try:
            item = self.lst.item(self.lst.selection()[0])['values'][6]
            self.selection_ont = self.lst.item(self.lst.selection()[0])['values']
        except IndexError:
            messagebox.showwarning("Не выбран элемент", "Для регистрации выберите нужную ONT из списка",
                                   parent=self)
            return
        if item == "?":
            messagebox.showwarning(
                "Неизвестный тип ONT",
                "В программе не существуют инструкций\nдля регистрации данного типа ONT",
                parent=self
            )
            ask = messagebox.askokcancel("Зарегистрировать как Hg8245",
                                         "Зарегистрировать как стандартную модель ONT Hg8245?",
                                         parent=self)
            if ask:
                self.current_ont = "hg8245"
            else:
                return
        elif self.current_ont:
            pass

        self.clear_childs()
        self.show_reg_params()

    def show_reg_params(self):
        self.geometry(center_window(self, 400, 300))
        self.title("Параметры регистрации")

        frame = tk.Frame(self, width=300)
        frame.grid(column=0, row=0)

        profile_names = [i["name"] for i in self.load_cbox_data()]

        label_name = tk.Label(frame, text="Название:", anchor="w")
        self.entry_name = EntryWithMenu(frame, width=40)
        label_cbox = tk.Label(frame, text="Профиль vlan:", anchor="w")
        self.cbox = ttk.Combobox(frame, values=profile_names, width=38, state="readonly")
        button_reg = tk.Button(frame, text="Продолжить", width=30, height=2, command=self.btn_click_reg)

        label_name.grid(row=0, column=0)
        self.entry_name.grid(row=0, column=1, pady=2)
        label_cbox.grid(row=1, column=0)
        self.cbox.grid(row=1, column=1)
        button_reg.grid(row=2, column=0, columnspan=2, pady=5)

    def btn_click_reg(self):
        name = self.entry_name.get()
        profile = self.cbox.get()
        if not name:
            messagebox.showwarning("Пустое поле ввода",
                                   "Поле ввода названия не должно оставаться пустым",
                                   parent=self)
            return
        if not self.validate_name(name):
            messagebox.showwarning("Некорректное название",
                                   "Допустимые символы для названия: A-Z, a-z, 0-9, (, ), -, _, /, и пробел",
                                   parent=self)
            return

        if not profile:
            messagebox.showwarning("Не выбран профиль",
                                   "Выберите необходимый профиль регистрации",
                                   parent=self)
            return

        self.clear_childs()
        self.show_loading()
        self.title("Регистрация...")
        WorkerReg(self, self.gpon, name, profile, self.current_ont, self.selection_ont).start()
        self.protocol("WM_DELETE_WINDOW", self.user_close_window)

    def load_cbox_data(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"]
        }
        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/profile/get",
                                     data=payload)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        messagebox.showerror("ОШИБКА", "Не удалось загрузить данные профилей с сервера", parent=self)
        self.destroy()

    @staticmethod
    def validate_name(name):
        for i in name:
            if not re.search(r"[a-zA-Z0-9\-\s_()/.?]", i):
                return False
        return True

    def choise_gpon(self):
        self.button_garage = tk.Button(self, text="Авто-поиск на\nGpon Гараж", width=20,
                                       command=lambda: self.run_autofind("garage"))
        self.button_garage.pack(pady=20)
        self.button_etag = tk.Button(self, text="Авто-поиск на\nGpon Пятиэтажка", width=20,
                                     command=lambda: self.run_autofind("etag"))
        self.button_etag.pack()

    def show_loading(self):
        self.load = LoadingLog(self)
        self.load.grid(row=0, column=0, sticky="nsew")



