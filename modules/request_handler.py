from tkinter import messagebox
from requests import exceptions


class ResponseHandler:
    def __init__(self, response, parent, show_success=True):
        self.result = None
        self.response = response
        self.status_code = response.status_code
        self.parent = parent
        self.show_success = show_success

        self.check_status_code()

    @property
    def get_data(self):
        return self.result

    def check_status_code(self):
        if self.status_200():
            if self.fail_handle():
                return
            elif self.error_handle():
                return
            elif self.success_handle():
                return
            try:
                self.result = self.response.json()
            except exceptions.JSONDecodeError:
                pass
        elif self.status_400():
            return
        elif self.status_401():
            return
        elif self.status_404():
            return
        elif self.status_500():
            return
        else:
            self.status_unhandled()
            return

    def status_200(self):
        if self.status_code == 200:
            return True

    def status_401(self):
        if self.status_code == 401:
            messagebox.showwarning("Запрос отклонён", "Сервер отклонил запрос, так как ваша сессия не действительна\n"
                                                      "<Status code: 401, Unathorized>", parent=self.parent)
            return True

    def status_400(self):
        if self.status_code == 400:
            messagebox.showwarning("Запрос отклонён", "Сервер отклонил запрос, так как он не был распознан\n"
                                                      "<Status code: 400, Bad Request>", parent=self.parent)
            return True

    def status_500(self):
        if self.status_code == 500:
            messagebox.showerror("Ошибка сервера", "Запрос не обработан из-за внутренней ошибки сервера\n"
                                                   "<Status code: 500, Internal Error>", parent=self.parent)
            return True

    def status_404(self):
        if self.status_code == 404:
            messagebox.showwarning("Запрос отклонён", "Данного пути запроса не существует\n"
                                                      "<Status code: 404, Not Found>", parent=self.parent)
            return True

    def status_unhandled(self):
        messagebox.showwarning("Ответ сервера не распознан", "Не удалось распознать ответ сервера\n"
                                                             "<Unhandled Response>", parent=self.parent)

    def fail_handle(self):
        if "Failure" in self.response.json():
            messagebox.showerror("Failure", "Gpon блок не обработал запрос:\n"
                                            f"{self.response.json()['Failure']}", parent=self.parent)
            return True

    def error_handle(self):
        if "error" in self.response.json():
            messagebox.showerror("Error", "Не удалось обработать запрос:\n"
                                          f"{self.response.json()['error']}", parent=self.parent)
            return True

    def success_handle(self):
        if "success" in self.response.json():
            if self.show_success:
                messagebox.showinfo("Success", "Запрос обработан\n"
                                               f"{self.response.json()['success']}", parent=self.parent)
            return True