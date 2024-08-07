import tkinter as tk
from tkinter import ttk, messagebox
import requests
from threading import Thread
from modules.request_handler import ResponseHandler
from modules.extension_tk import endpoint_parser, port_parser, gpon_parser


class Tree(tk.Frame):
    def __init__(self, parent, session, endpoint_click_callback=None):
        super().__init__(parent, highlightbackground="red", relief="sunken", bd=1)

        self.style = ttk.Style()
        self.style.map('Treeview', foreground=self.fixed_map('foreground'), background=self.fixed_map('background'))
        # print(self.style.theme_names())
        # self.style.theme_use("winnative")

        self.click_call = endpoint_click_callback
        self.session = session
        self.parent = parent

        self.tree = ttk.Treeview(self, selectmode="browse")
        self.last_item = None

        self.tree.bind("<<TreeviewOpen>>", self.open_item)
        self.tree.bind("<Motion>", self.motion_event)
        self.tree.bind("<Leave>", self.motion_event)
        self.tree.bind("<<TreeviewSelect>>", self.click_endpoint)
        # self.tree.bind("<<TreeviewClose>>", self.close_item)
        self.tree.heading('#0', text='Huawei MA5608T (список портов)')
        self.tree.column('#0', width=370)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree.insert(parent="", iid="garage", index=tk.END, text=' Gpon блок Гараж', tags=("folder",))
        self.tree.insert(parent="", iid="etag", index=tk.END, text=' Gpon блок Пятиэтажка', tags=("folder",))

        self.tree.insert(parent="garage", iid="garage/0/0", index=tk.END, text=" Слот 0/0", tags=("folder",))
        self.tree.insert(parent="garage", iid="garage/0/1", index=tk.END, text=" Слот 0/1", tags=("folder",))

        self.tree.insert(parent="etag", iid="etag/0/1", index=tk.END, text=" Слот 0/1", tags=("folder",))

        for i in range(16):
            self.tree.insert(parent="etag/0/1", iid=f"etag/0/1/{i}", index=tk.END, text=f" Порт {i}", tags=("folder",))
            self.tree.insert(parent=f"etag/0/1/{i}", iid=f"etag/0/1/{i} .ont/-1", index=tk.END, text="...", tags=("loading",))

        for i in range(8):
            self.tree.insert(parent="garage/0/0", iid=f"garage/0/0/{i}", index=tk.END, text=f" Порт {i}", tags=("folder",))
            self.tree.insert(parent=f"garage/0/0/{i}", iid=f"garage/0/0/{i} .ont/-1", index=tk.END, text="...", tags=("loading",))

        for i in range(8):
            self.tree.insert(parent="garage/0/1", iid=f"garage/0/1/{i}", index=tk.END, text=f" Порт {i}", tags=("folder",))
            self.tree.insert(parent=f"garage/0/1/{i}", iid=f"garage/0/1/{i} .ont/-1", index=tk.END, text="...", tags=("loading",))

        self.loading_img = tk.PhotoImage(file="src/images/loading.png")
        self.user_img = tk.PhotoImage(file="src/images/user.png")
        self.folder_img = tk.PhotoImage(file="src/images/folder.png")
        self.error_img = tk.PhotoImage(file="src/images/error.png")
        self.empty_img = tk.PhotoImage(file="src/images/empty.png")
        self.tree.tag_configure("loading", image=self.loading_img)
        self.tree.tag_configure("folder", image=self.folder_img)
        self.tree.tag_configure("user", image=self.user_img)
        self.tree.tag_configure("error", image=self.error_img)
        self.tree.tag_configure("empty", image=self.empty_img)
        self.tree.tag_configure("offline", foreground="#808080")
        self.tree.tag_configure("focus", foreground="blue", font=("Segoe UI", 9, "underline"))

        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.scroll_y.set)

        self.scroll_y.grid(row=0, column=1, sticky="ns")

    def open_port(self, gpon, slot, port, onu_id):
        self.tree.see(f"{gpon}/{slot}/{port}")
        self.tree.selection_set(f"{gpon}/{slot}/{port}")
        self.tree.item(f"{gpon}/{slot}/{port}", open=True)
        self.open_item("search_call", params=(gpon, slot, port, onu_id))

    def after_click_endpoint(self, gpon, slot, port, onu_id):
        self.tree.selection_set(f"{gpon}/{slot}/{port}/{onu_id}.ont_endpoint")
        self.click_endpoint(None)

    def get_selection_port(self):
        item = self.tree.selection()
        if item:
            return port_parser(item[0])

    def get_selection_gpon(self):
        item = self.tree.selection()
        if item:
            return gpon_parser(item[0])

    def open_item(self, ev=None, params=None):
        item = self.tree.selection()[0]
        items = item.split("/")
        if len(items) == 4:
            gpon = items[0]
            slot = f"{items[1]}/{items[2]}"
            port = items[3]
            self.tree.delete(*self.tree.get_children(item))
            self.tree.insert(parent=f"{gpon}/{slot}/{port}", iid=f"{gpon}/{slot}/{port} .ont/-1", index=tk.END, text="Загрузка...", tags=("loading",))
            Thread(target=self.thread_execute, args=(item, gpon, slot, port, params), daemon=True).start()

    def fixed_map(self, option):
        return [elm for elm in self.style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]

    def click_endpoint(self, ev):
        item = self.tree.selection()
        if ".ont_endpoint" in item[0]:
            self.click_call(endpoint_parser(item[0]))

    def delete_endpoint(self, gpon, slot, port, ont_id):
        iid = f"{gpon}/{slot}/{port}/{ont_id}.ont_endpoint"
        try:
            self.tree.delete(iid)
        except tk.TclError:
            messagebox.showerror("Ошибка графической оболочки Tk", f"Не удалась удалить элемент <{iid}> в структруре Treeview", parent=self)

    def motion_event(self, ev):
        item = self.tree.identify_row(ev.y)

        if item != self.last_item:
            if self.last_item:
                try:
                    tags = self.tree.item(self.last_item)["tags"]
                    if "focus" in tags:
                        tags.remove("focus")
                        self["cursor"] = "arrow"
                        self.tree.item(self.last_item, tags=tags)
                except tk.TclError:
                    pass

            tags = self.tree.item(item)["tags"]
            if not "focus" in tags:
                try:
                    tags.append("focus")
                    self["cursor"] = "hand2"
                except AttributeError:
                    pass
                self.tree.item(item, tags=tags)
                self.last_item = item

    def after_insert(self, item, response, gpon, slot, port):
        handle = ResponseHandler(response=response, parent=self, show_success=False)
        if handle.get_data:
            for i in self.tree.get_children(item):
                if ".ont" in i:
                    self.tree.delete(i)
            for ont in handle.get_data:
                self.tree.insert(item, index=tk.END, text=" " + ont["name"], iid=f"{gpon}/{slot}/{port}/{ont['id']}.ont_endpoint", tags=("user", ont["state"]))
        else:
            self.tree.delete(*self.tree.get_children(item))
            self.tree.insert(item, index=tk.END, tags=("empty",), text=" Порт пуст")

    def thread_execute(self, item, gpon, slot, port, params):
        data = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "gpon": gpon,
            "port": port,
            "slot": slot
        }
        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/onu_list", data=data)
            self.after(10, lambda: self.after_insert(item, response, gpon, slot, port))
            if params:
                self.after(20, lambda: self.after_click_endpoint(*params))
        except requests.exceptions.RequestException as e:
            exc = str(e)
            self.after(10, lambda: self.connect_exception(exc, item))

    def connect_exception(self, exc, item):
        self.tree.delete(*self.tree.get_children(item))
        self.tree.insert(item, index=tk.END, tags=("error",), text=" Ошибка загрузки")
        messagebox.showerror("Ошибка соединения", f"{exc}", parent=self)



