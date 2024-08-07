import requests
import tkinter as tk
from tkinter import ttk


# s = {"login": "Artem", "passw": "123kl123kl", "ip": "10.1.1.2", "port": "5000"}
# payload = {"gpon": "garage", "slot": "0/0", "port": "3", "login": "Artem", "passw": "123kl123kl"}
#
# response = requests.post(f"http://{s['ip']}:{s['port']}/autofind", data=payload)
# print(response.text)


class ListUnit(tk.Frame):
    def __init__(self, parent, data=None, command=None):
        super().__init__(parent, background="grey70", relief="raised", width=490, height=80)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.command = command
        self.data = {
            "Checkcode": "",
            "F/S/P": "0/0/3",
            "Loid": "",
            "Number": "2",
            "Ont EquipmentID": "310M",
            "Ont SN": "4857544371A2DB67 (HWTC-71A2DB67)",
            "Ont SoftwareVersion": "V3R015C10S106",
            "Ont Version": "6A5.A",
            "Ont autofind time": "2023-11-26 03:26:18+03:00",
            "Password": "0x00000000000000000000",
            "VendorID": "HWTC",
            "port": "3",
            "slot": "0/0"
        }

        self.bind_all("<Leave>", self.leave)
        self.bind_all("<Enter>", self.enter)
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<ButtonRelease-1>", self.release)

        self.label_gpon = tk.Label(self, text="etag")
        self.label_slot = tk.Label(self, text=self.data["slot"])
        self.label_port = tk.Label(self, text=self.data["port"])
        self.label_ont_id = tk.Label(self, text=self.data["Number"])
        self.label_ont_sn = tk.Label(self, text=self.data["Ont SN"])
        self.label_ont_time = tk.Label(self, text=self.data["Ont autofind time"])
        self.label_ont_model = tk.Label(self, text=self.data["Ont EquipmentID"])
        #
        for row, widge in enumerate([self.label_gpon, self.label_slot, self.label_port,
                                      self.label_ont_id, self.label_ont_sn,
                                      self.label_ont_time, self.label_ont_model]):
            pass
            widge.grid(row=row, column=1)

    def leave(self, ev):
        self.config(bd=0)

    def enter(self, ev):
        self.config(bd=2)

    def press(self, ev):
        self.config(relief="sunken", bd=2)

    def release(self, ev):
        self.config(relief="raised", bd=2)


class OntFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._counter_row = 0

    def append(self):
        self._frame = ListUnit(self)
        self._frame.grid(row=self._counter_row, column=0, sticky="nsew", padx=2, pady=2)
        self._counter_row += 1


class CustomList(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, relief="sunken", bd=2)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.scrl_y = ttk.Scrollbar(self, orient="vertical")
        self.scrl_y.grid(row=0, column=1, sticky="ns")

        self.canvas = tk.Canvas(self, width=500, height=500, yscrollcommand=self.scrl_y.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrl_y.config(command=self.canvas.yview)

        self.ont_frame = OntFrame(self.canvas)
        self.canvas.create_window(0, 0, anchor="nw", window=self.ont_frame)

    def append(self):
        self.ont_frame.append()



app = tk.Tk()
app.rowconfigure(0, weight=1)
app.columnconfigure(0, weight=1)
lst = CustomList(app)
lst.append()
lst.grid(row=0, column=0, sticky="nsew", pady=20, padx=20)
app.mainloop()

