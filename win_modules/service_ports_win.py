import tkinter as tk
from tkinter import ttk, messagebox
import requests
from modules.extension_tk import center_window, BitmapButton, EntryWithMenu
from threading import Thread


def send_request(parent, url_path, payload, timeout=10, response_handle=True):
    try:
        url = f"http://{parent.session['ip']}:{parent.session['port']}/{url_path}"

        payload["login"] = parent.session["login"]
        payload["passw"] = parent.session["passw"]
        payload["gpon"] = parent.gpon

        response = requests.post(url=url, data=payload, timeout=timeout)

        if not response_handle:
            return

        if response.status_code == 200:
            json_obj = response.json()
            if "error" in json_obj:
                inf = "error"
                msg = json_obj[inf]
            elif "Failure" in json_obj:
                inf = "Failure"
                msg = json_obj[inf]
            elif "success" in json_obj:
                messagebox.showinfo("Успешно", json_obj["success"], parent=parent)
                return
            else:
                inf = "Неизвестный ответ"
                msg = "Сервер ответил необрабатываемым сообщением"

            messagebox.showerror(inf, msg, parent=parent)

        elif response.status_code == 401:
            raise ValueError("Ошибка авторизации\nВаш логин и пароль не действительны")
    except requests.exceptions.RequestException:
        messagebox.showerror("Ошибка HTTP", "Ошибка соединения с сервером. Сервер не отвечает.", parent=parent)
    except Exception as exc:
        messagebox.showerror("Ошибка", f"{exc}", parent=parent)


def send_save(parent, url_path):
    payload = {}
    url = f"http://{parent.session['ip']}:{parent.session['port']}/{url_path}"

    payload["login"] = parent.session["login"]
    payload["passw"] = parent.session["passw"]
    payload["gpon"] = parent.gpon
    try:
        requests.post(url=url, data=payload, timeout=10)
    except requests.exceptions.RequestException:
        pass


class SimpleLoadingWin(tk.Toplevel):
    def __init__(self, parent, text="Загрузка списка Service-ports..."):
        super().__init__(parent)
        self.geometry(center_window(self, 250, 100))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.resizable(False, False)
        self.title("Загрузка")
        self.grab_set()
        tk.Label(self, text=text).pack(fill="both", expand=1)


class ServicePortForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.session = parent.session
        self.gpon = parent.gpon
        self.geometry(center_window(self, 400, 250))
        self.title("Добавление Service-Port")
        self.grab_set()

        self.result = []

        self.columnconfigure(1, weight=1)

        tk.Label(self, text="Слот").grid(row=0, column=0)
        tk.Label(self, text="Порт").grid(row=1, column=0)
        tk.Label(self, text="ONT ID").grid(row=2, column=0)
        tk.Label(self, text="Service-Port").grid(row=3, column=0)
        tk.Label(self, text="VLAN").grid(row=4, column=0)
        tk.Label(self, text="GEM порт").grid(row=5, column=0)
        self.btn = tk.Button(self, text="Добавить Service-Port", command=self.simple_validate, width=20)
        self.btn.grid(row=6, column=0, columnspan=2, pady=10)

        self.slot = EntryWithMenu(self)
        self.port = EntryWithMenu(self)
        self.onu_id = EntryWithMenu(self)
        self.service_port = EntryWithMenu(self)
        self.vlan = EntryWithMenu(self)
        self.gem = EntryWithMenu(self)

        self.slot.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        self.port.grid(row=1, column=1, sticky="we", padx=5)
        self.onu_id.grid(row=2, column=1, sticky="we", padx=5, pady=2)
        self.service_port.grid(row=3, column=1, sticky="we", padx=5)
        self.vlan.grid(row=4, column=1, sticky="we", pady=2, padx=5)
        self.gem.grid(row=5, column=1, sticky="we", padx=5)

    def simple_validate(self):
        self.result = []

        slot = self.slot.get()
        port = self.port.get()
        onu_id = self.onu_id.get()
        srv_port = self.service_port.get()
        vlan = self.vlan.get()
        gem = self.gem.get()

        for c, data in enumerate((slot, port, onu_id, srv_port, vlan, gem)):
            if not data:
                messagebox.showwarning("Неверный формат", "Все поля должны быть заполнены",
                                       parent=self)
                return
            if c != 0:
                try:
                    int(data)
                except ValueError:
                    messagebox.showwarning("Неверный формат", "Все значения должны являться цифровыми или числовыми",
                                           parent=self)
                    return
            else:
                if "\\" in data:
                    data = data.replace("\\", "/")

            self.result.append(data)

        self.add_srv_port()

    def add_srv_port(self):
        payload = {
            "slot": self.result[0],
            "port": self.result[1],
            "onu_id": self.result[2],
            "service_port": self.result[3],
            "vlan": self.result[4],
            "gem": self.result[5],
        }
        self.btn.config(text="Загрузка..")
        self.update()
        send_request(self, payload=payload, url_path="add_service_port")
        self.btn.config(text="Добавить Service-Port")


class ServicePortsWin(tk.Toplevel):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.geometry(center_window(self, 800, 600))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.title("Service-Port Manager")

        self.session = session
        self.gpon = ""

        self.down_img = tk.PhotoImage(file="src/images/error.png")
        self.up_img = tk.PhotoImage(file="src/images/good.png")
        self.add_img = tk.PhotoImage(file="src/images/add.png")
        self.delete_img = tk.PhotoImage(file="src/images/cross.png")
        self.save_img = tk.PhotoImage(file="src/images/save.png")
        self.update_img = tk.PhotoImage(file="src/images/update2.png")

        self.btns_frame = tk.Frame(self)
        self.btns_frame.grid(row=0, column=0, sticky="we")
        BitmapButton(self.btns_frame, image=self.add_img, command=self.open_add).grid(row=0, column=0)
        BitmapButton(self.btns_frame, image=self.delete_img, command=self.open_del).grid(row=0, column=1)
        BitmapButton(self.btns_frame, image=self.save_img, command=self.save_command).grid(row=0, column=2)
        BitmapButton(self.btns_frame, image=self.update_img, command=self.get_service_port).grid(row=0, column=3)
        ttk.Separator(self.btns_frame, orient="vertical").grid(row=0, column=4, sticky="ns", padx=2)
        tk.Label(self.btns_frame, text="Показать:").grid(row=0, column=5)
        self.etag_btn = tk.Button(self.btns_frame, text="Пятиэтажка", width=15, command=lambda: self.get_service_port("etag"))
        self.garage_btn = tk.Button(self.btns_frame, text="Гараж", width=15, command=lambda: self.get_service_port("garage"))
        self.etag_btn.grid(row=0, column=6)
        self.garage_btn.grid(row=0, column=7)

        self.tree = ttk.Treeview(
            self, columns=('srv_port', 'ont_id', 'port', 'slot', 'vlan', 'state'),
            height=30, selectmode='browse', style='q.Treeview', takefocus=False
        )
        self.tree.column('#0', stretch=False, width=70)
        self.tree.column('ont_id', minwidth=100, anchor='w', width=20)
        self.tree.column('port', stretch=False, width=120, anchor='w', minwidth=20)
        self.tree.column('srv_port', width=20, anchor='w', minwidth=20)
        self.tree.column('slot', width=20, anchor='w', minwidth=20)
        self.tree.column('vlan', width=20, anchor='w', minwidth=20)
        self.tree.column('state', width=20, anchor='w', minwidth=20)

        sort_srv = self.sort_name_generator(0)
        self.tree.heading('srv_port', text='Service-Port', command=lambda: sort_srv.__next__())
        sort_ont_id = self.sort_name_generator(1)
        self.tree.heading('ont_id', text='ONT ID', command=lambda: sort_ont_id.__next__())
        sort_port = self.sort_name_generator(2)
        self.tree.heading('port', text='Port', command=lambda: sort_port.__next__())
        sort_slot = self.sort_name_generator(3)
        self.tree.heading('slot', text='Slot', command=lambda: sort_slot.__next__())
        sort_vlan = self.sort_name_generator(4)
        self.tree.heading('vlan', text='VLAN', command=lambda: sort_vlan.__next__())
        sort_state = self.sort_name_generator(5)
        self.tree.heading('state', text='State', command=lambda: sort_state.__next__())

        self.tree.grid(row=1, column=0, sticky="nsew")

        self.scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll.set,
                            xscrollcommand=self.scroll_x.set)

        self.scroll.grid(row=1, column=1, sticky="ns")
        self.scroll_x.grid(row=2, column=0, sticky="we")

        s = ttk.Style()
        s.configure('q.Treeview', rowheight=19)

    def open_add(self):
        if not self.gpon:
            messagebox.showwarning("Элемент не выбран", "Выберите Gpon-блок для добавления Service-port", parent=self)
            return
        ServicePortForm(self)

    def open_del(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Элемент не выбран", "Выберите Service-Port из списка", parent=self)
        else:
            values = self.tree.item(item[0])["values"]
            ask = messagebox.askyesno("Удаление", f"Удалить service-port #{values[0]}?", parent=self)
            if ask:
                load = SimpleLoadingWin(self, text="Удаление..")
                self.update()
                send_request(parent=self, url_path="del_service_port", payload={"service_port": values[0]})
                load.destroy()

    def get_service_port(self, gpon=None):

        if not gpon:
            if not self.gpon:
                messagebox.showwarning("Не выбран элемент", "Не выбран нужный Gpon-блок", parent=self)
                return
        else:
            self.gpon = gpon
        loading_win = SimpleLoadingWin(self)

        if self.gpon == "etag":
            self.etag_btn.config(state=tk.DISABLED)
            self.garage_btn.config(state=tk.NORMAL)
        else:
            self.etag_btn.config(state=tk.NORMAL)
            self.garage_btn.config(state=tk.DISABLED)

        self.tree.delete(*self.tree.get_children())
        self.update()

        try:
            url = f"http://{self.session['ip']}:{self.session['port']}/service_port_list"

            payload = {
                "login": self.session["login"],
                "passw": self.session["passw"],
                "gpon": self.gpon
            }

            response = requests.post(url=url, data=payload)
            if response.status_code == 200:
                loading_win.destroy()
                json_obj = response.json()
                if "error" in json_obj:
                    raise ValueError("Ошибка на стороне сервера\nНе удалось авторизоваться на Gpon-блоке")
                for srv_line in json_obj:
                    vals = (
                        srv_line["service_port"],
                        srv_line["onu_id"],
                        srv_line["port"],
                        srv_line["slot"],
                        srv_line["vlan"],
                        srv_line["state"],
                    )
                    if srv_line["state"] == "up":
                        self.tree.insert("", index=tk.END, values=vals, image=self.up_img)
                    else:
                        self.tree.insert("", index=tk.END, values=vals, image=self.down_img)
                return
        except requests.exceptions.RequestException:
            messagebox.showerror("Ошибка HTTP", "Ошибка соединения с сервером. Сервер не отвечает.", parent=self)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"{exc}", parent=self)

        self.destroy()

    def sort_name_generator(self, sort):
        """генератор для сортировки элементов в списке"""
        revers = False
        while True:
            sorted_iids = []
            all_iids = self.tree.get_children()

            for iid in all_iids:
                name = self.tree.item(item=iid)['values']
                sorted_iids.append([name[sort], iid])

            sorted_iids = sorted(sorted_iids, key=lambda s: s[0], reverse=revers)

            for count, i in enumerate(sorted_iids):
                name, iid = i
                self.tree.move(iid, '', count)

            if revers:
                revers = False
                self._change_trianle_heading(sort, '▲')
            else:
                self._change_trianle_heading(sort, '▼')
                revers = True
            yield

    def _change_trianle_heading(self, heading, symbol_utf):
        """изменить, переместить треугольник в списке, на кнопках сортировки"""
        self._delete_triangle_heading()  # убрать треугольник со всех кнопок
        if heading == 0:
            self.tree.heading('srv_port', text=f'Service-Port   {symbol_utf}')
        elif heading == 1:
            self.tree.heading('ont_id', text=f'ONT ID   {symbol_utf}')
        elif heading == 2:
            self.tree.heading('port', text=f'Port   {symbol_utf}')
        elif heading == 3:
            self.tree.heading('slot', text=f'Slot   {symbol_utf}')
        elif heading == 4:
            self.tree.heading('vlan', text=f'VLAN   {symbol_utf}')
        elif heading == 5:
            self.tree.heading('state', text=f'State   {symbol_utf}')

    def _delete_triangle_heading(self):
        """убрать всех треугольники сортировки с кнопок сортировки"""
        self.tree.heading('srv_port', text='Service-Port')
        self.tree.heading('ont_id', text='ONT ID')
        self.tree.heading('port', text='Port')
        self.tree.heading('slot', text='Slot')
        self.tree.heading('vlan', text='VLAN')
        self.tree.heading('state', text='State')

    def save_command(self):
        if not self.gpon:
            messagebox.showwarning("Элемент не выбран", "Выберите Gpon-блок для отправки команды", parent=self)
            return

        Thread(target=send_save, args=(self, "save")).start()
        messagebox.showinfo("Команда отправлена", "Команда </save> отправлена на Gpon блок", parent=self)

    def response_handler(self):
        pass
