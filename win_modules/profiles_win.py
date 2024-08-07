import tkinter as tk
from tkinter import ttk, messagebox
from modules.extension_tk import center_window, EntryWithMenu, BitmapButton
import requests


class ProfileWin(tk.Toplevel):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.geometry(center_window(self, 400, 250))
        self.title("Редактор профилей")
        self.session = session
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.main_frame = ProfileSettings(self, session)
        self.main_frame.grid(row=0, column=0, sticky="nsew")


class ProfileSettings(tk.Frame):
    def __init__(self, parent, session, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.profiles = []
        self.session = session
        self.get_values()
        self.columnconfigure(0, weight=1)

        self.btns_frame = tk.Frame(self)
        self.btns_frame.grid(row=0, column=0, sticky="we", padx=5, pady=2)

        self.cross_img = tk.PhotoImage(file="src/images/cross.png")
        self.add_img = tk.PhotoImage(file="src/images/add.png")
        self.update_img = tk.PhotoImage(file="src/images/update.png")

        self.add_button = BitmapButton(self.btns_frame, image=self.add_img, command=self.add_profile)
        self.add_button.grid(row=0, column=0)
        self.del_button = BitmapButton(self.btns_frame, image=self.cross_img, command=self.delete_profile)
        self.del_button.grid(row=0, column=1)
        self.update_button = BitmapButton(self.btns_frame, image=self.update_img, command=self.update_profiles)
        self.update_button.grid(row=0, column=2)

        self.info_frame = tk.Frame(self)
        self.info_frame.grid(row=1, column=0, sticky="we")
        self.info_frame.columnconfigure(1, weight=1)

        self.combobox = ttk.Combobox(self.info_frame, state="readonly")
        self.combobox.grid(row=0, column=0, columnspan=2, sticky="we", padx=20, pady=10)
        self.combobox.bind("<<ComboboxSelected>>", self.select_cbox)

        self.name_label = tk.Label(self.info_frame, text="Name:")
        self.name_entry = EntryWithMenu(self.info_frame)
        self.name_label.grid(row=1, column=0, sticky='e')
        self.name_entry.grid(row=1, column=1, sticky="we", padx=10, pady=2)

        self.vlan_label = tk.Label(self.info_frame, text="Vlan:")
        self.vlan_entry = EntryWithMenu(self.info_frame)
        self.vlan_label.grid(row=2, column=0, sticky='e')
        self.vlan_entry.grid(row=2, column=1, sticky="we", padx=10, pady=2)

        self.gem_label = tk.Label(self.info_frame, text="Gemport:")
        self.gem_entry = EntryWithMenu(self.info_frame)
        self.gem_label.grid(row=3, column=0, sticky='e')
        self.gem_entry.grid(row=3, column=1, sticky="we", padx=10, pady=2)

        self.srv_label = tk.Label(self.info_frame, text="Srv-profile:")
        self.srv_entry = EntryWithMenu(self.info_frame)
        self.srv_label.grid(row=4, column=0, sticky='e')
        self.srv_entry.grid(row=4, column=1, sticky="we", padx=10, pady=2)

        self.line_label = tk.Label(self.info_frame, text="Line-profile:")
        self.line_entry = EntryWithMenu(self.info_frame)
        self.line_label.grid(row=5, column=0, sticky='e')
        self.line_entry.grid(row=5, column=1, sticky="we", padx=10, pady=2)

        self.update_val()

    def update_profiles(self):
        self.update_val()
        self.clear_entryes()

    def get_values(self):
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"]
        }
        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/profile/get", data=payload)
            if response.status_code == 200:
                self.profiles = response.json()
        except Exception:
            messagebox.showerror("Ошибка", "Внутренняя ошибка запроса", parent=self)
            return

    def delete_profile(self):
        try:
            sel = self.combobox.selection_get()
        except Exception:
            messagebox.showwarning("Профиль не выбран", "Для удаления профиля выберите его из списка", parent=self)
            return
        payload = {
            "login": self.session["login"],
            "passw": self.session["passw"],
            "name": sel
        }
        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/profile/del", data=payload)
            if response.status_code == 200:
                if response.json() == "OK":
                    messagebox.showinfo("Профиль удалён", "Профиль успешно удалён с сервера", parent=self)
                    self.update_profiles()
                else:
                    messagebox.showwarning("Запрос не обработан", response.json(), parent=self)
            else:
                messagebox.showwarning("Запрос не обработан", response.json(), parent=self)
        except Exception:
            messagebox.showerror("Ошибка", "Внутренняя ошибка запроса", parent=self)
            return

    def add_profile(self):
        data = self.get_entryes()
        if not data:
            return
        payload = data
        payload["login"] = self.session["login"]
        payload["passw"] = self.session["passw"]

        try:
            response = requests.post(f"http://{self.session['ip']}:{self.session['port']}/profile/add", data=payload)
            if response.status_code == 200:
                if response.json() == "OK":
                    messagebox.showinfo("Запрос обработан", response.json(), parent=self)
                    self.update_profiles()
                else:
                    messagebox.showwarning("Запрос не обработан", response.json(), parent=self)
            else:
                messagebox.showwarning("Запрос не обработан", response.json(), parent=self)
        except Exception:
            messagebox.showerror("Ошибка", "Внутренняя ошибка запроса", parent=self)
            return

    def update_val(self):
        self.get_values()
        self.combobox.delete(0, tk.END)
        self.combobox.set("")
        combobox_values = []
        for val in self.profiles:
            combobox_values.append(val["name"])
        self.combobox.config(values=combobox_values)

        # self.combobox.set(combobox_values[0])

    def select_cbox(self, ev):
        sel_cbox = self.combobox.selection_get()
        for vals in self.profiles:
            if str(vals["name"]) == str(sel_cbox):
                self.insert_etryes(vals)
                return

    def insert_etryes(self, values):
        self.clear_entryes()
        self.name_entry.insert(tk.END, values["name"])
        self.vlan_entry.insert(tk.END, values["vlan"])
        self.gem_entry.insert(tk.END, values["gem"])
        self.srv_entry.insert(tk.END, values["srv"])
        self.line_entry.insert(tk.END, values["line"])

    def clear_entryes(self):
        self.name_entry.delete(0, tk.END)
        self.vlan_entry.delete(0, tk.END)
        self.gem_entry.delete(0, tk.END)
        self.srv_entry.delete(0, tk.END)
        self.line_entry.delete(0, tk.END)

    def get_entryes(self):
        name = self.name_entry.get()
        vlan = self.vlan_entry.get()
        gem = self.gem_entry.get()
        srv = self.srv_entry.get()
        line = self.line_entry.get()
        data = {"name": name, "vlan": vlan, "gem": gem, "srv": srv, "line": line}
        for i in data.values():
            if not i:
                messagebox.showwarning("Пустые поля", "Все поля должны быть заполнены", parent=self)
                return
        return {"name": name, "vlan": vlan, "gem": gem, "srv": srv, "line": line}

