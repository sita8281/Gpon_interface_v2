import threading
import tkinter as tk
from threading import Thread
import requests
from modules.extension_tk import ScrolledView, EntryCopy
from modules.loading_animation import LoadingAnimation


class Info(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bd=2, width=800, height=600)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.parent = parent
        self.session = None
        self.ont_desc = None
        self.args_lst = None

        self.optical_info = tk.Frame(self, relief="sunken", bd=2)
        self.optical_info.columnconfigure(0, weight=1)
        self.optical_info.grid(row=0, column=0, sticky="nsew")
        self.label_optical = tk.Label(self.optical_info, text="Оптическая информация", background="#4682B4", font=("Segoe UI", 10, "bold"), foreground="white", bd=1, relief="sunken")
        self.label_optical.grid(row=0, column=0, sticky="we", columnspan=2)

        self.main_info = tk.Frame(self, relief="sunken", bd=2)
        self.main_info.columnconfigure(0, weight=1)
        self.main_info.grid(row=0, column=1, sticky="nsew", padx=5)
        self.label_info = tk.Label(self.main_info, text="Основная информация", background="#4682B4", font=("Segoe UI", 10, "bold"), foreground="white", bd=1, relief="sunken")
        self.label_info.grid(row=0, column=0, sticky="we", columnspan=2)

        self.last_thread = None
        self.last_thread_2 = None

        self.entry_pass()

    def clear_frames(self):
        for child in self.optical_info.winfo_children()[1:]:
            child.destroy()
        for child in self.main_info.winfo_children()[1:]:
            child.destroy()

    def get_info(self, args):
        self.args_lst = args
        self.clear_frames()
        loading_optical = LoadingAnimation(self.optical_info, width=400, height=600)
        loading_optical.grid(row=2, column=0)
        loading_info = LoadingAnimation(self.main_info, width=400, height=600)
        loading_info.grid(row=2, column=0)
        args_lst = list(args)
        th = Thread(target=self.request_info, args=args_lst + [loading_info], daemon=True)
        th2 = Thread(target=self.request_optical, args=args_lst + [loading_optical], daemon=True)
        th.start()
        th2.start()
        self.last_thread = th.ident
        self.last_thread_2 = th2.ident

    def request_info(self, gpon, slot, port, onu_id, loading_object):
        try:
            response = requests.post(
                f"http://{self.session['ip']}:{self.session['port']}/onu_optical_info",
                data={"login": self.session["login"],
                      "passw": self.session["passw"],
                      "gpon": gpon,
                      "slot": slot,
                      "port": port,
                      "iid": onu_id},
                timeout=5
            )
        except requests.exceptions.RequestException:
            response = None

        if threading.current_thread().ident == self.last_thread:
            self.after(10, lambda: self.response_optical(response, loading_object))

    def request_optical(self, gpon, slot, port, onu_id, loading_object):
        try:
            response = requests.post(
                f"http://{self.session['ip']}:{self.session['port']}/onu_info",
                data={"login": self.session["login"],
                      "passw": self.session["passw"],
                      "gpon": gpon,
                      "slot": slot,
                      "port": port,
                      "iid": onu_id},
                timeout=5
            )
        except requests.exceptions.RequestException:
            response = None

        if threading.current_thread().ident == self.last_thread_2:
            self.after(10, lambda: self.response_info(response, loading_object))

    def response_optical(self, response, loading_obj):
        loading_obj.destroy()
        if response:
            if response.status_code == 200:
                info = response.json()
                if not info:
                    self.entry_pass("optical")
                for c, inf in enumerate(info.items(), start=1):
                    label = tk.Label(self.optical_info, text=inf[0] + "  ", anchor='w')
                    entry = EntryCopy(self.optical_info, width=30)
                    entry.insert(tk.END, inf[1])
                    # entry['state'] = "readonly"
                    label.grid(row=c, column=0, sticky='w')
                    entry.grid(row=c, column=1)

                    if inf[0] == "Rx optical power(dBm)":
                        label["font"] = ("Segoe UI", 9, "bold")
                        if float(inf[1]) >= -27:
                            entry["background"] = "#ADFF2F"
                        elif -27 > float(inf[1]) >= -30:
                            entry["background"] = "#FFD700"
                        elif -30 > float(inf[1]) >= -50:
                            entry["background"] = "#FF0000"
                            label["foreground"] = "white"
                return
        err_label = tk.Label(self.optical_info, text="Сервер не ответил на запрос", font=("Segoe UI", 14, "bold"), foreground="red")
        err_label.grid(row=3, column=0)

    def response_info(self, response, loading_obj):
        loading_obj.destroy()
        if response:
            if response.status_code == 200:
                info = response.json()
                for c, inf in enumerate(info.items(), start=1):
                    if inf[0] == "Description":
                        self.ont_desc = inf[1]
                    label = tk.Label(self.main_info, text=inf[0] + "  ", anchor='w')
                    entry = EntryCopy(self.main_info, width=45,)
                    entry.insert(tk.END, inf[1])

                    label.grid(row=c, column=0, sticky='w')
                    entry.grid(row=c, column=1)

                    if inf[0] == "Description":
                        label['font'] = ("Segoe UI", 9, "bold")
                    if inf[0] == "ONT online duration":
                        label['font'] = ("Segoe UI", 9, "bold")
                    if inf[0] == "SN":
                        label['font'] = ("Segoe UI", 9, "bold")
                    if inf[0] == "Run state":
                        label['font'] = ("Segoe UI", 9, "bold")
                        if inf[1] == "online":
                            entry["background"] = "#66ff00"
                        elif inf[1] == "offline":
                            entry["background"] = "#FF0033"
                            entry["foreground"] = "white"
                return
        err_label = tk.Label(self.main_info, text="Сервер не ответил на запрос", font=("Segoe UI", 14, "bold"), foreground="red")
        err_label.grid(row=3, column=0)

    def entry_pass(self, frame=None):
        optical = ['CATV Rx optical power(dBm)', 'CATV Rx power alarm threshold(dBm)', 'Date Code',
                   'Encapsulation Type', 'Laser bias current(mA)', 'Module sub-type', 'Module type',
                   'OLT Rx ONT optical power(dBm)', 'ONU NNI port ID', 'Optical power precision(dBm)',
                   'Rx optical power(dBm)', 'Rx power current alarm threshold(dBm)',
                   'Rx power current warning threshold(dBm)', 'Supply voltage alarm threshold(V)',
                   'Supply voltage warning threshold(V)', 'Temperature alarm threshold(C)',
                   'Temperature warning threshold(C)', 'Temperature(C)', 'Tx bias current alarm threshold(mA)',
                   'Tx bias current warning threshold(mA)', 'Tx optical power(dBm)',
                   'Tx power current alarm threshold(dBm)', 'Tx power current warning threshold(dBm)', 'Used type',
                   'Vendor PN', 'Vendor SN', 'Vendor name', 'Vendor rev', 'Voltage(V)']

        info = ['Authentic type', 'CPU occupation', 'Config state', 'Control flag', 'DBA type', 'Description', 'F/S/P',
                'Interoperability-mode', 'Isolation state', 'Last down cause', 'Last down time', 'Last dying gasp time',
                'Last up time', 'Management mode', 'Match state', 'Memory occupation', 'ONT IP 0 address/mask',
                'ONT battery state', 'ONT distance(m)', 'ONT online duration', 'ONT-ID', 'Run state', 'SN',
                'Software work mode', 'Temperature', 'Type C support']

        if frame == "optical":
            for c, opt in enumerate(optical, start=1):
                label = tk.Label(self.optical_info, text=opt + "  ", anchor='w')
                entry = EntryCopy(self.optical_info, width=30)
                # entry['state'] = "readonly"
                label.grid(row=c, column=0, sticky='w')
                entry.grid(row=c, column=1)
        elif frame == "info":
            for c, inf in enumerate(info, start=1):
                label = tk.Label(self.main_info, text=inf + "  ", anchor='w')
                entry = EntryCopy(self.main_info, width=45)
                # entry['state'] = "readonly"
                label.grid(row=c, column=0, sticky='w')
                entry.grid(row=c, column=1)
        else:

            for c, inf in enumerate(info, start=1):
                label = tk.Label(self.main_info, text=inf + "  ", anchor='w')
                entry = EntryCopy(self.main_info, width=45)
                # entry['state'] = "readonly"
                label.grid(row=c, column=0, sticky='w')
                entry.grid(row=c, column=1)

            for c, opt in enumerate(optical, start=1):
                label = tk.Label(self.optical_info, text=opt + "  ", anchor='w')
                entry = EntryCopy(self.optical_info, width=30)
                # entry['state'] = "readonly"
                label.grid(row=c, column=0, sticky='w')
                entry.grid(row=c, column=1)

    def get_data(self):
        if self.args_lst and self.ont_desc:
            gpon = self.args_lst[0]
            slot = self.args_lst[1]
            port = self.args_lst[2]
            onu_id = self.args_lst[3]
            return gpon, slot, port, onu_id, self.ont_desc


class InfoScrolled(ScrolledView):
    def scrolled_frame(self):
        self.frame = Info(self.canvas)
        self.canvas.config(scrollregion=(0, 0, 850, 650))
        return self.frame
