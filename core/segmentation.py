# -*- coding: utf-8 -*-
from collections import deque


def dilate(b):
    """Giãn nở 3x3 để nối các nét biên bị đứt."""
    h, w = len(b), len(b[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if b[y][x]:
                for j in range(max(0, y - 1), min(h, y + 2)):
                    for i in range(max(0, x - 1), min(w, x + 2)):
                        out[j][i] = 1
    return out


def find_regions(edge, min_area=150):
    """Tìm các vùng nằm trọn bên trong đường biên (bỏ qua nền chạm viền ảnh)."""
    h, w = len(edge), len(edge[0])
    seen = [[False] * w for _ in range(h)]
    regions = []
    for sy in range(h):
        for sx in range(w):
            if edge[sy][sx] or seen[sy][sx]:
                continue
            q = deque([(sx, sy)])
            seen[sy][sx] = True
            pix = []
            touch = False
            while q:
                x, y = q.popleft()
                pix.append((x, y))
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    touch = True
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and not edge[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if not touch and len(pix) >= min_area:
                xs = [p[0] for p in pix]
                ys = [p[1] for p in pix]
                regions.append({
                    "area": len(pix), "pix": pix,
                    "x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys),
                })
    return regions