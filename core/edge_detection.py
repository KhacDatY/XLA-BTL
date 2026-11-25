# -*- coding: utf-8 -*-
import math
from collections import deque
from config import HYST_HIGH_RATIO, HYST_LOW_RATIO, KERNELS


def convolve3(m, k):
    """Tích chập 3x3, viền ngoài để bằng 0."""
    h, w = len(m), len(m[0])
    out = [[0] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            s = 0
            for j in range(3):
                row = m[y + j - 1]
                kj = k[j]
                for i in range(3):
                    s += row[x + i - 1] * kj[i]
            out[y][x] = s
    return out


def blur(channel):
    """Làm mờ trung bình 3x3 trên một kênh màu để giảm nhiễu."""
    box = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    c = convolve3(channel, box)
    return [[v // 9 for v in row] for row in c]


def _channel_gradient(ch, method):
    """Tính độ lớn gradient thô (chưa chuẩn hóa) cho 1 kênh."""
    kx, ky = KERNELS[method]
    gx = convolve3(ch, kx)
    h, w = len(ch), len(ch[0])
    if ky is None:  # Laplacian
        return [[abs(v) for v in row] for row in gx]
    gy = convolve3(ch, ky)
    return [
        [math.sqrt(gx[y][x] ** 2 + gy[y][x] ** 2) for x in range(w)]
        for y in range(h)
    ]


def color_edge_magnitude(r_ch, g_ch, b_ch, method):
    """
    Phát hiện biên trên ảnh màu RGB:
    Tính gradient độc lập trên 3 kênh R, G, B rồi lấy max(G_R, G_G, G_B).
    Giúp giữ lại biên giữa 2 hình khác màu nhưng cùng độ sáng.
    """
    mr = _channel_gradient(blur(r_ch), method)
    mg = _channel_gradient(blur(g_ch), method)
    mb = _channel_gradient(blur(b_ch), method)

    h, w = len(r_ch), len(r_ch[0])
    mag = [[0.0] * w for _ in range(h)]
    mx = 0.0
    for y in range(2, h - 2):
        for x in range(2, w - 2):
            v = max(mr[y][x], mg[y][x], mb[y][x])
            mag[y][x] = v
            if v > mx:
                mx = v

    if mx == 0:
        return [[0] * w for _ in range(h)]
    return [[int(v * 255 / mx) for v in row] for row in mag]


def otsu_threshold(m):
    """Tính ngưỡng Otsu tự động."""
    hist = [0] * 256
    for row in m:
        for v in row:
            hist[v] += 1
    total = sum(hist)
    sum_all = sum(i * hist[i] for i in range(256))
    sum_b = w_b = 0
    best_var, best_t = -1, 0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var, best_t = var, t
    return best_t


def hysteresis_threshold(mag):
    """
    Ngưỡng kép Canny (Hysteresis Thresholding):
    - Biên mạnh (>= t_high): chắc chắn giữ.
    - Biên yếu (t_low <= v < t_high): chỉ giữ nếu nối liền (8 hướng) với biên mạnh.
    """
    h, w = len(mag), len(mag[0])
    t_otsu = otsu_threshold(mag)
    t_high = max(20, int(t_otsu * HYST_HIGH_RATIO))
    t_low = max(8, int(t_high * HYST_LOW_RATIO))

    out = [[0] * w for _ in range(h)]
    q = deque()

    # Bước 1: Đánh dấu toàn bộ pixel biên mạnh làm hạt giống
    for y in range(h):
        for x in range(w):
            if mag[y][x] >= t_high:
                out[y][x] = 1
                q.append((x, y))

    # Bước 2: Lan truyền BFS 8 hướng sang các pixel biên yếu liền kề
    neighbors = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    while q:
        x, y = q.popleft()
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and out[ny][nx] == 0:
                if mag[ny][nx] >= t_low:
                    out[ny][nx] = 1
                    q.append((nx, ny))

    return out