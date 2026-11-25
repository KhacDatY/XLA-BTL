# -*- coding: utf-8 -*-
from PIL import Image
from config import MAX_SIZE


def load_rgb(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_SIZE, MAX_SIZE))
    return img


def split_rgb(img):
    """Tách ảnh RGB thành 3 ma trận 2 chiều R, G, B."""
    w, h = img.size
    px = img.load()
    r_ch = [[0] * w for _ in range(h)]
    g_ch = [[0] * w for _ in range(h)]
    b_ch = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            r_ch[y][x] = r
            g_ch[y][x] = g
            b_ch[y][x] = b
    return r_ch, g_ch, b_ch


def to_gray(img):
    """Chuyển ảnh xám (dùng để hiển thị ở khung Ảnh xám)."""
    w, h = img.size
    px = img.load()
    gray = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            gray[y][x] = int(0.299 * r + 0.587 * g + 0.114 * b)
    return gray