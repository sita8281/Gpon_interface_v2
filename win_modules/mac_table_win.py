import tkinter as tk
from tkinter import ttk, messagebox
from modules.extension_tk import center_window, EntryWithMenu
import requests
import winsound


class LoadingLite(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry(center_window(self, 250, 150))
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grab_set()
        self.title("Загрузка..")
        tk.Label(self, text="Загрузка списка MAC-адресов...\n\nпроцесс может занять до 30 сек").grid(row=0, column=0)


class CustomMsgBox(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry(center_window(self, 360, 250))
        self.grab_set()
        self.iconphoto(False, tk.PhotoImage(file="src/images/warning16.png"))
        self.resizable(False, False)
        self.title("Не выбран элемент")
        winsound.PlaySound("SystemAsterisk", winsound.SND_ASYNC)

        self.canvas = tk.Canvas(self, height=160, width=250, highlightthickness=0, relief="sunken", bd=2)
        self.img = tk.PhotoImage(file="src/images/example0.png")
        self.image = self.canvas.create_image(0, 0, anchor='nw', image=self.img)
        self.canvas.grid(row=0, column=0, pady=5)

        self.label = tk.Label(self, text="Выберите GPON-блок из главного списка (см. картинку выше)")
        self.label.grid(row=1, column=0)

        tk.Button(self, text="OK", width=12, command=self.destroy).grid(row=2, column=0, sticky="e", pady=5, padx=10)


class MacTableWin(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.geometry(center_window(self, 800, 600))
        self.title("")

        self.session = parent.session
        self.gpon = data
        self.parent = parent

        self.tree = ttk.Treeview(
            self, columns=('srv_port', 'ont_id', 'port', 'slot', 'vlan', 'mac'),
            height=30, selectmode='browse', style='q.Treeview', takefocus=False
        )
        self.tree.column('#0', stretch=False, width=70)
        self.tree.column('ont_id', minwidth=100, anchor='w', width=20)
        self.tree.column('port', stretch=False, width=120, anchor='w', minwidth=20)
        self.tree.column('srv_port', width=20, anchor='w', minwidth=20)
        self.tree.column('slot', width=20, anchor='w', minwidth=20)
        self.tree.column('vlan', width=20, anchor='w', minwidth=20)
        self.tree.column('mac', width=100, anchor='w', minwidth=100)

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
        self.tree.heading('mac', text='MAC', command=lambda: sort_state.__next__())

        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll.set,
                            xscrollcommand=self.scroll_x.set)

        self.scroll.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="we")

        s = ttk.Style()
        s.configure('q.Treeview', rowheight=19)

        self.group_frame = tk.Frame(self)
        self.search_entry = EntryWithMenu(self.group_frame)
        self.search_btn = tk.Button(self.group_frame, text="Найти", width=10, command=self.search_port)

        self.search_entry.grid(row=0, column=0, padx=5, pady=2)
        self.search_btn.grid(row=0, column=1)
        self.group_frame.grid(row=2, column=0)

        self.mac_img = tk.PhotoImage(file="src/images/file16.png")

        self.check_data()
        self.update()
        self.get_mac_all()

    def check_data(self):
        self.update()
        if not self.gpon:
            win = CustomMsgBox(self)
            self.wait_window(win)
            # self.after_idle(self.destroy)
            return
        if self.gpon == "etag":
            self.title("Выбранный GPON-блок: Пятиэтажка")
        elif self.gpon == "garage":
            self.title("Выбранный GPON-блок: Гараж")

    def search_port(self):
        mac = self.search_entry.get()

        for item in self.tree.get_children():
            if mac == self.tree.item(item)["values"][5]:
                self.tree.see(item)
                self.tree.selection_set(item)
                return
        messagebox.showwarning("Элемент не найден", "Не удалось найти MAC-адрес", parent=self)

    def get_mac_all(self):
        payload = {}
        try:
            url = f"http://{self.session['ip']}:{self.session['port']}/mac/all"

            payload["login"] = self.session["login"]
            payload["passw"] = self.session["passw"]
            payload["gpon"] = self.gpon

            load = LoadingLite(self)
            self.update()
            response = requests.post(url=url, data=payload, timeout=30)
            load.destroy()

            if response.status_code == 200:
                json_obj = response.json()
                if "error" in json_obj:
                    inf = "error"
                    msg = json_obj[inf]
                    messagebox.showerror(inf, msg, parent=self)
                elif json_obj:
                    self.insert_macs(json_obj)
                    return
                else:
                    inf = "Неизвестный ответ"
                    msg = "Сервер ответил необрабатываемым сообщением"
                    messagebox.showerror(inf, msg, parent=self)
                self.destroy()

            elif response.status_code == 401:
                raise ValueError("Ошибка авторизации\nВаш логин и пароль не действительны")
        except requests.exceptions.RequestException as exc:
            s = str(exc)
            messagebox.showerror("Ошибка HTTP", f"{exc}", parent=self)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"{exc}", parent=self)
        self.destroy()

    def insert_macs(self, lst):
        for elem in lst:
            vals = (
                elem["srv"],
                elem["ont_id"],
                elem["port"],
                elem["slot"],
                elem["vlan"],
                elem["mac"]
            )
            self.tree.insert("", index=tk.END, values=vals, image=self.mac_img)

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
            self.tree.heading('mac', text=f'MAC   {symbol_utf}')

    def _delete_triangle_heading(self):
        """убрать всех треугольники сортировки с кнопок сортировки"""
        self.tree.heading('srv_port', text='Service-Port')
        self.tree.heading('ont_id', text='ONT ID')
        self.tree.heading('port', text='Port')
        self.tree.heading('slot', text='Slot')
        self.tree.heading('vlan', text='VLAN')
        self.tree.heading('mac', text='MAC')