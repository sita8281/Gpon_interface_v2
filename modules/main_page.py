import tkinter as tk
from tkinter import ttk, messagebox
from modules.tree_module import Tree
from modules.info_module import InfoScrolled
from modules.buttons_panel_info_module import Buttons
from win_modules.ping_win import PingWin
from win_modules.delete_win import DeleteWin
from win_modules.search_mac_win import SearchMacWin


class MainPage(tk.Frame):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.parent = parent
        self.session = session
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.paned_window = tk.PanedWindow(self, orient='horizontal')
        self.group_frame = tk.Frame(self.paned_window)
        self.group_frame.columnconfigure(0, weight=1)
        self.group_frame.rowconfigure(0, weight=1)
        self.info_frame = InfoScrolled(self.group_frame)
        self.info_frame.get_frame.session = self.session

        self.buttons_panel = Buttons(self.group_frame)
        self.buttons_panel.grid(row=1, column=0, sticky="w", pady=10)
        self.buttons_panel.ping_button["command"] = self.run_ping
        self.buttons_panel.delete_button["command"] = self.del_ont
        self.buttons_panel.mac_button["command"] = self.mac_ont

        self.tree = Tree(self.paned_window, self.session, endpoint_click_callback=self.view_info)  # свзязь двух объектов
        self.info_frame.grid(row=0, column=0, sticky="nsew")
        self.paned_window.add(self.tree)
        self.paned_window.add(self.group_frame)
        self.paned_window.grid(row=0, column=0, sticky="nsew")

    def view_info(self, endpoint):
        self.info_frame.get_frame.get_info(endpoint)

    def run_ping(self):
        data = self.info_frame.get_frame.get_data()
        if data:
            PingWin(self, self.session, *data)
        else:
            messagebox.showwarning("Не выбрана ONT", "Для запуска пинга, выберите из списка нужную ONT", parent=self)

    def del_ont(self):
        data = self.info_frame.get_frame.get_data()
        if data:
            ask = messagebox.askyesno("Удаление ONT", f"""Вы действительно хотите удалить "{data[4]}"?""")
            if ask:
                del_win = DeleteWin(self, self.session, *data)
                del_win.delete()
        else:
            messagebox.showwarning("Не выбрана ONT", "Выберите из списка ONT, которую нужно удалить", parent=self)

    def mac_ont(self):
        data = self.info_frame.get_frame.get_data()
        if data:
            srch_win = SearchMacWin(self, self.session, *data)
            srch_win.search()
        else:
            messagebox.showwarning("Не выбрана ONT", "Выберите из списка ONT, MAC которой нужно найти", parent=self)





