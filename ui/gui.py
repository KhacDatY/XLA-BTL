# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk

from config import KERNELS, VN_NAME
from core.io_utils import load_rgb
from pipeline import run_pipeline


class App:
    def __init__(self, root):
        self.root = root
        root.title("Nhận diện hình dạng - Xử lý ảnh")
        self.img = None
        self.result = None

        bar = tk.Frame(root)
        bar.pack(pady=6)
        tk.Button(bar, text="Mở ảnh", command=self.open_image).pack(side="left", padx=4)
        self.method = ttk.Combobox(bar, values=list(KERNELS), state="readonly", width=10)
        self.method.current(0)
        self.method.pack(side="left", padx=4)
        tk.Button(bar, text="Xử lý", command=self.process).pack(side="left", padx=4)
        tk.Button(bar, text="Lưu kết quả", command=self.save).pack(side="left", padx=4)

        panels = tk.Frame(root)
        panels.pack()
        self.labels = []
        for title in ("Ảnh xám", "Biên màu (Canny)", "Kết quả"):
            f = tk.Frame(panels)
            f.pack(side="left", padx=4)
            tk.Label(f, text=title).pack()
            lb = tk.Label(f)
            lb.pack()
            self.labels.append(lb)

        self.info = tk.Label(root, text="", justify="left", font=("Arial", 11))
        self.info.pack(pady=6)

    def show(self, idx, pil_img):
        tk_img = ImageTk.PhotoImage(pil_img)
        self.labels[idx].configure(image=tk_img)
        self.labels[idx].image = tk_img

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.img = load_rgb(path)
            self.show(2, self.img)

    def process(self):
        if self.img is None:
            messagebox.showwarning("Thiếu ảnh", "Hãy mở ảnh trước.")
            return
        self.info.config(text="Đang xử lý...")
        self.root.update()
        gimg, eimg, res, counts, skipped = run_pipeline(self.img, self.method.get())
        self.result = res
        self.show(0, gimg)
        self.show(1, eimg)
        self.show(2, res)
        lines = [f"{VN_NAME[k]}: {v}" for k, v in counts.items() if v > 0]
        txt = "Tìm thấy:  " + ("   |   ".join(lines) if lines else "không có hình nào")
        if skipped:
            txt += f"\n(Bỏ qua {skipped} vùng quá méo hoặc mất góc)"
        self.info.config(text=txt)

    def save(self):
        if self.result is None:
            messagebox.showwarning("Chưa có kết quả", "Hãy xử lý ảnh trước.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")],
        )
        if path:
            self.result.save(path)
            messagebox.showinfo("Đã lưu", path)