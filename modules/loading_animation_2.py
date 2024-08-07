import tkinter as tk


class LoadingAnimation(tk.Frame):
    def __init__(self, parent, width, height):
        super().__init__(parent, width=width, height=height)
        self.img_animation = [tk.PhotoImage(file='src/images/loading2.gif', format=f'gif -index {i}') for i in range(10)]
        self.canvas_anim = tk.Canvas(self)
        self.canvas_anim.place(x=int(width/2-22.5), y=int(height/2-22.5), width=45, height=45)
        self.count = 0
        self.animation_load()
        self.after_point = None

    def animation_load(self):
        for i in self.canvas_anim.find_all():
            self.canvas_anim.delete(i)
        self.count += 1
        if self.count > 9:
            self.count = 0
        self.canvas_anim.create_image(0, 0, anchor='nw', image=self.img_animation[self.count])

        if self.count == 8:
            self.after_point = self.after(500, self.animation_load)
        else:
            self.after_point = self.after(300, self.animation_load)


if __name__ == "__main__":
    app = tk.Tk()
    frame = LoadingAnimation(app, 50 ,50)
    frame.grid(row=0, column=0, sticky="nsew")

    app.mainloop()