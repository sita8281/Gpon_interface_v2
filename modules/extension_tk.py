from tkinter import ttk
import tkinter as tk


def endpoint_parser(string) -> tuple:
    splited_ = string.split("/")
    gpon = splited_[0]
    slot = splited_[1] + "/" + splited_[2]
    port = splited_[3]
    onu_id = splited_[4].split(".")[0]
    return gpon, slot, port, onu_id


def port_parser(string) -> tuple:
    try:
        splited_ = string.split("/")
        if len(splited_) > 4:
            return ()
        gpon = splited_[0]
        slot = splited_[1] + "/" + splited_[2]
        port = splited_[3]
        return gpon, slot, port
    except Exception:
        return ()


def gpon_parser(string):
    try:
        splited_ = string.split("/")
        gpon = splited_[0]
        if len(splited_) > 1:
            raise ValueError
        return gpon
    except Exception:
        return ()


def center_window(p, width, height):
    """
    :param p: Окно которое нужно разместить по центру
    :param width: Ширина окна
    :param height: Высота окна
    :return:
    """
    screen_width = p.winfo_screenwidth()
    screen_height = p.winfo_screenheight()
    win_width = width
    win_height = height
    x_coordinate = int((screen_width / 2) - (win_width / 2))
    y_coordinate = int((screen_height / 2) - (win_height / 2))
    return f'{win_width}x{win_height}+{x_coordinate}+{y_coordinate}'


def center_window_adaptive(p, width, height):
    """
        :param p: Окно которое нужно разместить по центру
        :param width: Ширина окна
        :param height: Высота окна
        :return:
        """
    screen_width = p.winfo_screenwidth()
    screen_height = p.winfo_screenheight()
    win_width = int(width*(screen_width / 1920))
    win_height = int(height*(screen_height / 1080))
    x_coordinate = int((screen_width / 2) - (win_width / 2))
    y_coordinate = int((screen_height / 2) - (win_height / 2))
    return f'{win_width}x{win_height}+{x_coordinate}+{y_coordinate}'


class BitmapButton(tk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config(relief="flat")
        self.bind("<Leave>", lambda ev: self.config(relief="flat"))
        self.bind("<Enter>", lambda ev: self.config(relief="raised"))


class EntryCopy(tk.Entry):
    """
    Обычный Entry виджет наследованный от ttk.Entry
    Добавлено простое меню: копировать
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Button-3>', self.open_menu)
        self.menu = tk.Menu(tearoff=0)
        self.menu.add_command(label='Копировать', command=self.copy)

    def open_menu(self, e):
        self.menu.post(e.x_root, e.y_root)

    def copy(self):
        try:
            if self.selection_present():
                f_sel = self.index('sel.first')
                l_sel = self.index('sel.last')
                self.clipboard_clear()
                get = self.get()
                self.clipboard_append(get[f_sel:l_sel])
                return f_sel, l_sel
        except (tk.TclError, Exception):
            pass


class EntryWithMenu(ttk.Entry):
    """
    Обычный Entry виджет наследованный от ttk.Entry
    Добавлено простое меню: копировать, вставить и вырезать
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Button-3>', self.open_menu)
        self.menu = tk.Menu(tearoff=0)
        self.menu.add_command(label='Копировать', command=self.copy)
        self.menu.add_command(label='Вставить', command=self.paste)
        self.menu.add_command(label='Вырезать', command=self.cut)

    def open_menu(self, e):
        self.menu.post(e.x_root, e.y_root)

    def copy(self):
        try:
            if self.selection_present():
                f_sel = self.index('sel.first')
                l_sel = self.index('sel.last')
                self.clipboard_clear()
                get = self.get()
                self.clipboard_append(get[f_sel:l_sel])
                return f_sel, l_sel
        except (tk.TclError, Exception):
            pass

    def paste(self):
        try:
            pst = self.clipboard_get()
            if pst:
                if self.selection_present():
                    f_sel = self.index('sel.first')
                    l_sel = self.index('sel.last')
                    self.delete(f_sel, l_sel)
                    self.insert(f_sel, pst)
                else:
                    indx = self.index('insert')
                    self.insert(indx, pst)
        except tk.TclError:
            pass

    def cut(self):
        sel = self.copy()
        if sel:
            self.delete(sel[0], sel[1])


class ScrolledView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.parent = parent
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.create_window(0, 0, window=self.scrolled_frame(), anchor="nw")

        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.grid(row=1, column=0, sticky="we")
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_y.grid(row=0, column=1, sticky="ns")

        self.canvas.config(xscrollcommand=self.adaptive_scroller_x, yscrollcommand=self.adaptive_scroller_y)
        # self.canvas.config(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        # self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)
        self.canvas.bind("<Leave>", self.mouse_leave)
        self.canvas.bind("<Enter>", self.mouse_enter)

        self._mouse_wheel_lock = True

    def mouse_leave(self, ev):
        self.canvas.unbind_all("<MouseWheel>")

    def mouse_enter(self, ev):
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)

    def mouse_wheel(self, ev):
        if self._mouse_wheel_lock:
            self.canvas.yview_scroll(int(-1*(ev.delta/120)), "units")

    def scrolled_frame(self):
        self.frame = tk.Frame(self.canvas, background="red", width=500, height=500)
        return self.frame

    @property
    def get_frame(self):
        return self.frame

    def adaptive_scroller_y(self, a, b):
        """Scroll_Y вызвает этот метод, при любом изменении размера виджета,
        или изменении количества находящихся в нём элементов.
        Нужен для авто-скрытия scroll-баров, когда в них нет нужды"""

        self.scroll_y.set(a, b)
        if float(b) == 1.0 and float(a) == 0.0:
            self.scroll_y.grid_remove()
            self._mouse_wheel_lock = False
        else:
            self.scroll_y.grid(row=0, column=1, sticky='ns')
            self._mouse_wheel_lock = True

    def adaptive_scroller_x(self, a, b):
        """Scroll_X вызвает этот метод, при любом изменении размера виджета,
        или изменении количества находящихся в нём элементов.
        Нужен для авто-скрытия scroll-баров, когда в них нет нужды"""

        self.scroll_x.set(a, b)
        if float(b) == 1.0 and float(a) == 0.0:
            self.scroll_x.grid_remove()
        else:
            self.scroll_x.grid(row=1, column=0, sticky='we')
