import tkinter as tk
from tkinter import ttk
from threading import Thread
import requests
import time
from modules.extension_tk import center_window


class PingWin(tk.Toplevel):
    def __init__(self, parent, session, gpon, slot, port, onu_id, name):
        super().__init__(parent)
        self.geometry(center_window(self, 600, 600))

        self.grab_set()

        self.gpon = gpon
        self.slot = slot
        self.port = port
        self.onu_id = onu_id
        self.name = name

        self._session = session

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.style = ttk.Style()
        self.style.map('Treeview', foreground=self.fixed_map('foreground'), background=self.fixed_map('background'))

        self.tree = ttk.Treeview(self, show="headings", columns=("id", "name", "state"), height=20)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scrl = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scrl.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=self.scrl.set)

        self.tree.column('id', minwidth=30, stretch=False, anchor="center")
        self.tree.column('name', minwidth=200, anchor="center")
        self.tree.column('state', minwidth=30, stretch=False, anchor="center")
        self.tree.heading('id', text='ID запроса')
        self.tree.heading('name', text='Название ONT')
        self.tree.heading('state', text='Сигнал ONT')

        self.tree.tag_configure("offline", background="#FF0033", foreground="white")
        self.tree.tag_configure("online", background="#66ff00", foreground="black")

        self.stop_thread = False
        Thread(target=self.thread_ping, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self.stop_thread_)
        self.id_counter = 0

    def stop_thread_(self):
        self.destroy()
        self.stop_thread = not self.stop_thread

    def thread_ping(self):
        while True:
            try:
                response = requests.post(
                    f"http://{self._session['ip']}:{self._session['port']}/ping",
                    data={"login": self._session["login"],
                          "passw": self._session["passw"],
                          "gpon": self.gpon,
                          "slot": self.slot,
                          "port": self.port,
                          "onu_id": self.onu_id},
                    timeout=3
                )
                if self.stop_thread:
                    return
                if response.status_code == 200:
                    self.id_counter += 1
                    if self.id_counter == 1000:
                        self.after(500, self.destroy)
                        return
                    try:
                        data = response.json()
                        if data == "offline":
                            self.after(10, lambda: self.tree.insert("", index=tk.END, values=(str(self.id_counter), self.name, data), tags="offline"))
                            self.after(50, lambda: self.tree.yview("moveto", "1"))
                        else:
                            self.after(10, lambda: self.tree.insert("", index=tk.END, values=(str(self.id_counter), self.name, data), tags="online"))
                            self.after(50, lambda: self.tree.yview("moveto", "1"))
                    except requests.exceptions.JSONDecodeError:
                        time.sleep(1)
                    continue
                time.sleep(1)
            except requests.exceptions.RequestException:
                time.sleep(1)

    def fixed_map(self, option):
        return [elm for elm in self.style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]
