import tkinter as tk
from tkinter import ttk, messagebox
from modules.extension_tk import center_window
from modules.loading_animation import LoadingAnimation
import requests
from threading import Thread
import winsound


class CustomExc(Exception):
    pass


class Worker(Thread):
    def __init__(self, session, data, parent):
        super().__init__(daemon=True)
        self.kill_flag = False
        self.lst_ont = []
        self.result_lst = []
        self.errors = []
        self.session = session
        self.parent = parent

        self.gpon = data[0]
        self.slot = data[1]
        self.port = data[2]

    def kill(self):
        self.kill_flag = True

    def run(self):
        try:
            self.request_ont_list()
            self.request_ont_signal()
            self.parent.event_thread()
            print('thread fin')
        except CustomExc as exc:
            type_err, text = str(exc).split('\n', 1)
            self.parent.show_error(type_err, text)
        except Exception as exc:
            self.parent.show_error("Неизвестная ошибка", str(exc))

    def request_ont_list(self):
        payload = {"gpon": self.gpon, "slot": self.slot, "port": self.port}
        lst = self.request_base(url_path="onu_list", params=payload)
        if lst:
            self.lst_ont = lst

    def request_ont_signal(self):
        len_ = len(self.lst_ont)
        for c, ont in enumerate(self.lst_ont):
            if self.kill_flag:
                return
            if ont["state"] == "online":
                signal = self.request_base(
                    "ping",
                    params={"gpon": self.gpon, "slot": self.slot, "port": self.port, "onu_id": ont["id"]}
                )
                procent = int(100/len_ * c)
                self.parent.status.config(text=f"Состояние загрузки: {procent}%   ({ont['name']})")
                ont["signal"] = signal
                self.result_lst.append(ont)
            else:
                ont["signal"] = "offline"
                self.result_lst.append(ont)

    def request_base(self, url_path, params):
        params['login'] = self.session['login']
        params['passw'] = self.session['passw']

        url = f"http://{self.session['ip']}:{self.session['port']}/{url_path}"
        try:
            response = requests.post(url, data=params, timeout=5)
            if response.status_code == 200:
                resp = response.json()
                if "error" in resp:
                    raise CustomExc(f"Ошибка\n{resp['error']}")
                return resp

            else:
                raise CustomExc("HTTP Error\nResponse.StatusCode is not 200")
        except requests.RequestException as exc:
            raise CustomExc(f"HTTP Error\n{exc}")


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


class WorkerStatusWin(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry(center_window(self, 350, 150))
        self.title("Загрузка сигналов..")
        self.grab_set()
        self.resizable(False, False)

        self.parent = parent
        self.session = parent.session
        self.data = parent.data

        self.load = LoadingAnimation(self, width=120, height=120)
        self.load.grid(row=0, column=0, sticky="nw")

        tk.Label(self, text="Загрузка списка сигналов..", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="ns")
        self.status = tk.Label(self, text="Состояние загрузки: ?", anchor="w", width=50)
        self.status.grid(row=1, column=0, columnspan=2, sticky="w")

        self.protocol("WM_DELETE_WINDOW", self.close_win)
        self.bind("<<ThreadSuccess>>", self.thread_final)

        self.run()

    def run(self):
        self.thread = Worker(self.session, self.data, self)
        self.thread.start()

    def close_win(self):
        try:
            self.thread.kill()
        finally:
            self.destroy()

    def thread_final(self, ev):
        self.parent.insert_list(self.thread.result_lst)
        self.destroy()

    def show_error(self, type_err, text):
        messagebox.showerror(type_err, text, parent=self)
        self.destroy()

    def event_thread(self):
        self.event_generate("<<ThreadSuccess>>")


class SignalTableWin(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("Список сигналов")
        self.geometry(center_window(self, 800, 600))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.data = data
        self.session = parent.session

        if self.check_data():
            self.run_thread()

        self.tree = ttk.Treeview(
            self, columns=('signal', 'name', 'sn', 'ont_id', 'port', 'slot'),
            height=30, selectmode='browse', style='sig.Treeview', takefocus=False
        )
        self.tree.column('#0', stretch=False, width=70)
        self.tree.column('signal', minwidth=150, anchor='w', width=150)
        self.tree.column('name', width=150, anchor='w', minwidth=150)
        self.tree.column('sn', width=150, anchor='w', minwidth=150)
        self.tree.column('ont_id', stretch=False, width=120, anchor='w', minwidth=20)
        self.tree.column('port', width=20, anchor='w', minwidth=20)
        self.tree.column('slot', width=20, anchor='w', minwidth=20)

        sort_signal = self.sort_name_generator(0)
        self.tree.heading('signal', text='Rx Optical Power(dBm)', command=lambda: sort_signal.__next__())

        sort_name = self.sort_name_generator(1)
        self.tree.heading('name', text='Name', command=lambda: sort_name.__next__())

        sort_sn = self.sort_name_generator(2)
        self.tree.heading('sn', text='SN', command=lambda: sort_sn.__next__())

        sort_id = self.sort_name_generator(3)
        self.tree.heading('ont_id', text='ONT ID', command=lambda: sort_id.__next__())

        sort_port = self.sort_name_generator(4)
        self.tree.heading('port', text='Port', command=lambda: sort_port.__next__())

        sort_slot = self.sort_name_generator(5)
        self.tree.heading('slot', text='Slot', command=lambda: sort_slot.__next__())

        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll.set,
                            xscrollcommand=self.scroll_x.set)

        self.scroll.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="we")

        s = ttk.Style()
        s.configure('sig.Treeview', rowheight=48)

        self.img_signal1 = tk.PhotoImage(file="src/images/signal1.png")
        self.img_signal2 = tk.PhotoImage(file="src/images/signal2.png")
        self.img_signal3 = tk.PhotoImage(file="src/images/signal3.png")
        self.img_signal4 = tk.PhotoImage(file="src/images/signal4.png")
        self.img_signal_off = tk.PhotoImage(file="src/images/signal_off2.png")
        self.img_unknown = tk.PhotoImage(file="src/images/unknown.png")

    def insert_list(self, lst):
        for ont in lst:
            vals = (
                ont["signal"],
                ont["name"],
                ont["sn"],
                ont["id"],
                ont["port"],
                ont["slot"]
            )
            if ont["signal"] == "offline":
                img = self.img_signal_off
            elif float(ont["signal"]) >= -25.99:
                img = self.img_signal1
            elif -26 >= float(ont["signal"]) >= -27.99:
                img = self.img_signal2
            elif -28 >= float(ont["signal"]) >= -30.99:
                img = self.img_signal3
            elif -31.00 >= float(ont["signal"]):
                img = self.img_signal4
            else:
                img = self.img_unknown
            self.tree.insert("", index=tk.END, values=vals, image=img)

    def run_thread(self):
        WorkerStatusWin(self)

    def check_data(self):
        self.update()
        try:
            if not len(self.data) != 3:
                return True
        except (TypeError, KeyError, ValueError):
            pass
        win = CustomMsgBox(self)
        self.wait_window(win)
        self.after_idle(self.destroy)

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
            self.tree.heading('signal', text=f'Rx Optical Power(dBm)   {symbol_utf}')
        elif heading == 1:
            self.tree.heading('name', text=f'Name   {symbol_utf}')
        elif heading == 2:
            self.tree.heading('sn', text=f'SN   {symbol_utf}')
        elif heading == 3:
            self.tree.heading('ont_id', text=f'ONT ID   {symbol_utf}')
        elif heading == 4:
            self.tree.heading('port', text=f'Port   {symbol_utf}')
        elif heading == 5:
            self.tree.heading('slot', text=f'Slot   {symbol_utf}')

    def _delete_triangle_heading(self):
        """убрать всех треугольники сортировки с кнопок сортировки"""
        self.tree.heading('signal', text='Rx Optical Power(dBm)')
        self.tree.heading('ont_id', text='ONT ID')
        self.tree.heading('slot', text='Slot')
        self.tree.heading('port', text='Port')
        self.tree.heading('sn', text='SN')
        self.tree.heading('name', text='Name')



