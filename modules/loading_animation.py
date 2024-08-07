import tkinter as tk


class LoadingAnimation(tk.Frame):
    def __init__(self, parent, width, height):
        super().__init__(parent, width=width, height=height)
        self.img_animation = [tk.PhotoImage(file='src/images/loading.gif', format=f'gif -index {i}') for i in range(16)]
        self.canvas_anim = tk.Canvas(self)
        self.canvas_anim.place(x=int(width/2-60), y=int(height/2-60), width=120, height=120)
        self.count = 0
        self.animation_load()
        self.after_point = None

    def animation_load(self):
        self.count += 1
        if self.count == 16:
            self.count = 0
            for i in self.canvas_anim.find_all():
                self.canvas_anim.delete(i)
        self.canvas_anim.create_image(0, 0, anchor='nw', image=self.img_animation[self.count])

        self.after_point = self.after(50, self.animation_load)


if __name__ == "__main__":
    app = tk.Tk()
    frame = LoadingAnimation(app)
    frame.grid(row=0, column=0, sticky="nsew")

    app.mainloop()