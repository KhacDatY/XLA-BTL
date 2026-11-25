# -*- coding: utf-8 -*-
MAX_SIZE = 400  # thu nhỏ ảnh để Python thuần chạy nhanh

KERNELS = {
    "Sobel": (
        [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],   # Gx
        [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],   # Gy
    ),
    "Prewitt": (
        [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]],
        [[-1, -1, -1], [0, 0, 0], [1, 1, 1]],
    ),
    "Laplacian": ([[0, 1, 0], [1, -4, 1], [0, 1, 0]], None),
}

# Ngưỡng kép Canny (Hysteresis) tính theo ngưỡng Otsu
HYST_HIGH_RATIO = 0.85   # T_high = Otsu * 0.85 (biên mạnh)
HYST_LOW_RATIO = 0.25    # T_low  = T_high * 0.25 (biên yếu giữa các hình chồng nhau)

# Các ngưỡng phân loại hình dạng
ANGLE_TOL = 12
SQUARE_RATIO = 0.85
MERGE_RATIO = 0.08
MIN_TURN = 22
SOLIDITY_MIN = 0.96
ELLIPSE_CV = 0.015
ELLIPSE_CV_PX = 0.4
CIRCLE_RATIO = 0.92
ELLIPSE_MIN_RATIO = 0.45

VN_NAME = {
    "Hinh tron": "Hình tròn",
    "Elip": "Elip",
    "Tam giac": "Tam giác",
    "Hinh vuong": "Hình vuông",
    "Hinh chu nhat": "Hình chữ nhật",
    "Tu giac": "Tứ giác",
    "Ngu giac": "Ngũ giác",
    "Luc giac": "Lục giác",
    "That giac": "Thất giác",
    "Bat giac": "Bát giác",
    "Cuu giac": "Cửu giác",
    "Thap giac": "Thập giác",
}

POLY_KEY = {
    5: "Ngu giac", 6: "Luc giac", 7: "That giac",
    8: "Bat giac", 9: "Cuu giac", 10: "Thap giac",
}

COLORS = {
    "Hinh tron": (220, 0, 0), "Elip": (200, 0, 100), "Tam giac": (0, 150, 0),
    "Hinh vuong": (0, 0, 255), "Hinh chu nhat": (255, 140, 0), "Tu giac": (150, 0, 150),
    "Ngu giac": (0, 150, 150), "Luc giac": (120, 120, 0), "That giac": (90, 60, 200),
    "Bat giac": (160, 80, 0), "Cuu giac": (0, 100, 160), "Thap giac": (100, 100, 100),
}