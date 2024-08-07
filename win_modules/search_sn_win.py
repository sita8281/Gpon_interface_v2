import tkinter as tk
from tkinter import ttk, StringVar, messagebox
from modules.extension_tk import center_window, EntryWithMenu
from modules.loading_log import LoadingLog
from threading import Thread
import requests


class Worker(Thread):
    def __init__(self, window, gpon, sn):
        super().__init__(daemon=True)

        self.window = window
        self.session = window.session
        self.gpon = gpon
        self.sn = sn
        self.slot = ""
        self.port = ""
        self.onu_id = ""

        self.kill_flag = False
        self.status = "ok"
        self.finded = False

        self.ports_pool = {
            "etag": {"0/1": [str(i) for i in range(16)]},
            "garage": {"0/0": [str(i) for i in range(8)], "0/1": [str(i) for i in range(8)]}
        }

    def run(self):
        self.send_requests()

    def send_requests(self):
        slots = self.ports_pool[self.gpon]

        for slot in slots:
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
                    response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/onu_list", data=payload)
                    # print(response.status_code)
                    # print(response.text)

                    self.slot = slot
                    self.port = port
                    if self.check_find_sn(response.json()):
                        return
                except Exception:
                    self.status = "error"
                    return

    def check_find_sn(self, lst):
        for ont in lst:
            if ont["sn"] == self.sn:
                self.onu_id = ont["id"]
                self.finded = True
                self.status = "ok"
                self.window.th_success = True
                return True


class MainFrame(tk.Frame):
    def __init__(self, parent, session, command):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)

        self.session = session
        self.command = command
        self.variable = StringVar(value="etag")
        self.sn = ""

        self.name_label = tk.Label(self, text="Утилита поиска по S/N", font=("Segoe UI", 9, "bold"),
                                   background="#ADD8E6", relief="raised", bd='2')
        self.etag_rbutton = ttk.Radiobutton(self, text="Пятиэтажка", variable=self.variable, value="etag")
        self.garage_rbutton = ttk.Radiobutton(self, text="Гараж", variable=self.variable, value="garage")
        self.all_rbutton = ttk.Radiobutton(self, text="Все", variable=self.variable, value="all")
        self.sn_entry = EntryWithMenu(self)
        self.run_search_button = tk.Button(self, text="Начать поиск", command=self.button_press)

        self.name_label.grid(row=0, column=0, sticky="we", pady=5)
        self.etag_rbutton.grid(row=1, column=0)
        self.garage_rbutton.grid(row=2, column=0, pady=5)
        self.all_rbutton.grid(row=3, column=0)
        self.sn_entry.grid(row=4, column=0, sticky="we", padx=20)
        self.run_search_button.grid(row=5, column=0, pady=5)

    def button_press(self):
        sn = self.sn_entry.get()
        if not self.validate_entry(sn):
            messagebox.showwarning(
                "Неправильный SN",
                "Нарушен формат SN-номера:\n"
                "- Длина SN должна ровняться 16 символам\n"
                "- И содержать только HEX символы",
                parent=self
            )
            return

        self.command(self.sn, self.variable.get())

    def validate_entry(self, sn):
        if not sn:
            return
        if len(sn) != 16:
            return
        self.sn = sn.upper()
        return True


class SuccessFrame(tk.Frame):
    def __init__(self, parent, command, gpon, slot, port, onu_id):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.callb = command
        self.parent = parent

        self.gpon = gpon
        self.slot = slot
        self.port = port
        self.onu_id = onu_id

        self.th_success = False

        self.check_img = tk.PhotoImage(file="src/images/success.png")
        self.image_canvas = tk.Canvas(self, width=150, height=150)
        self.image_canvas.create_image(0, 0, anchor="nw", image=self.check_img)
        self.image_canvas.grid(row=1, column=0, sticky="nsew")

        self.button = tk.Button(self, text="Показать ONT", command=self.press, width=20, height=2)
        self.button.grid(row=1, column=1, padx=50, sticky="we")

        keys = ("Gpon блок", "Слот", "Порт", "ID ONT")
        for c, info_row in enumerate((self.gpon, self.slot, self.port, self.onu_id)):
            tk.Label(self, text=keys[c] + ":", font=("Segoe UI", 9, 'bold')).grid(row=c+2, column=0, sticky="e")
            tk.Label(self, text=info_row, font=("Segoe UI", 9)).grid(row=c+2, column=1, sticky="w")

    def press(self):
        if callable(self.callb):
            self.callb(self.gpon, self.slot, self.port, self.onu_id)
        self.parent.destroy()


class SearchSnWin(tk.Toplevel):
    def __init__(self, parent, session, open_method):
        super().__init__(parent)
        self.geometry(center_window(self, 400, 300))
        self.resizable(False, False)
        self.title("Поиск ONT по SN")
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.grab_set()
        self.iconphoto(False, tk.PhotoImage(file="src/images/search.png"))

        self.session = session
        self.open_method = open_method

        self.loading_frame = None
        self.main_frame = MainFrame(self, self.session, command=self.run_search)
        self.main_frame.pack(fill="both", expand=1)

        self.th_success = False

        self.thread_1 = None
        self.thread_2 = None
        self.kill_thread_checker = False

    def run_search(self, sn, gpon):
        self.show_loading()

        if gpon == "all":
            self.thread_1 = Worker(self, "etag", sn)
            self.thread_2 = Worker(self, "garage", sn)
            self.loading_frame.insert_log(msg=f"Поток поиска на <Gpon блоке: Etag> запущен.")
            self.loading_frame.insert_log(msg=f"Поток поиска на <Gpon блоке: Garage> запущен.")
            self.thread_1.start()
            self.thread_2.start()
        else:
            self.thread_1 = Worker(self, gpon, sn)
            self.thread_1.start()
            self.loading_frame.insert_log(msg=f"Поток поиска на <Gpon блоке: {gpon}> запущен.")

        self.loading_frame.insert_log(msg=f"Процесс выполняется...")

        self.threads_checker()

    def threads_checker(self):
        if self.kill_thread_checker:
            return

        if self.thread_1:
            if not self.thread_1.is_alive():
                self.result_thread(self.thread_1)

        if self.thread_2:
            if not self.thread_2.is_alive():
                self.result_thread(self.thread_2)

        self.after(200, self.threads_checker)

    def result_thread(self, thread):
        if thread.status == "ok":
            if thread.finded:
                self.success_frame = SuccessFrame(
                    self,
                    self.open_method,
                    thread.gpon,
                    thread.slot,
                    thread.port,
                    thread.onu_id
                )
                self.success_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                self.geometry(center_window(self, 400, 250))
                self.kill_thread_checker = True
                # self.close_window()
                return
            else:
                if not self.thread_1 or not self.thread_2:
                    messagebox.showwarning("SN не найден", "Не удалось найти SN на GPON блоке/блоках", parent=self)
        elif thread.status == "error":
            messagebox.showerror("Ошибка поиска", "Из за внутренней ошибки не удалось найти SN", parent=self)

        if self.thread_1 and self.thread_2:
            if not self.thread_1.is_alive() and not self.thread_1.finded:
                if not self.thread_2.is_alive() and not self.thread_2.finded:
                    self.kill_thread_checker = True
                    messagebox.showwarning("SN не найден", "Не удалось найти SN на GPON блоке/блоках", parent=self)
                    self.close_window()
        else:
            self.kill_thread_checker = True
            self.close_window()

    def show_loading(self):
        for child in self.winfo_children():
            child.destroy()
        self.loading_frame = LoadingLog(self)
        self.loading_frame.grid(row=0, column=0, sticky="nsew")

    def close_window(self):
        if self.thread_1:
            self.thread_1.kill_flag = True
        if self.thread_2:
            self.thread_2.kill_flag = True

        self.destroy()
