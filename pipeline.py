# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
from config import COLORS, VN_NAME
from core.edge_detection import color_edge_magnitude, hysteresis_threshold
from core.io_utils import split_rgb, to_gray
from core.segmentation import dilate, find_regions
from shape.classifier import classify
from shape.geometry import poly_area


def get_font():
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "tahoma.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, 14), True
        except Exception:
            pass
    return ImageFont.load_default(), False


def _point_in_poly(x, y, poly):
    """Thuật toán Ray Casting kiểm tra điểm (x, y) có nằm trong đa giác poly không."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_inter = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-9)
            if x < x_inter:
                inside = not inside
    return inside


def _filter_intersections(detections):
    """
    Loại bỏ các vùng giao nhau (overlap artifacts):
    Nếu tâm của vùng A nằm bên trong >= 2 đa giác lớn hơn -> A là phần giao nhau -> bỏ.
    """
    kept = []
    for i, item in enumerate(detections):
        r, key, poly = item
        cx = sum(p[0] for p in r["pix"]) / len(r["pix"])
        cy = sum(p[1] for p in r["pix"]) / len(r["pix"])
        area_i = poly_area(poly)

        containers = 0
        for j, other in enumerate(detections):
            if i == j:
                continue
            other_poly = other[2]
            if poly_area(other_poly) > area_i * 1.15 and _point_in_poly(cx, cy, other_poly):
                containers += 1

        if containers < 2:
            kept.append(item)
    return kept


def run_pipeline(img, method):
    gray = to_gray(img)

    r_ch, g_ch, b_ch = split_rgb(img)
    mag = color_edge_magnitude(r_ch, g_ch, b_ch, method)
    binary = hysteresis_threshold(mag)

    binary = dilate(binary)
    if method == "Laplacian":
        binary = dilate(binary)

    regions = find_regions(binary)
    detections = []
    skipped = 0

    for r in regions:
        key, poly = classify(r)
        if key is None:
            skipped += 1
            continue
        detections.append((r, key, poly))

    # Lọc bỏ các vùng giao nhau bị đếm thừa
    detections = _filter_intersections(detections)

    result = img.copy()
    draw = ImageDraw.Draw(result)
    font, has_vn = get_font()
    counts = {k: 0 for k in VN_NAME}

    for r, key, poly in detections:
        counts[key] += 1
        col = COLORS[key]
        draw.line(poly + [poly[0]], fill=col, width=2)
        label = VN_NAME[key] if has_vn else key
        draw.text((r["x0"], max(0, r["y0"] - 18)), label, fill=col, font=font)

    gimg = Image.new("L", img.size)
    gimg.putdata([v for row in gray for v in row])
    eimg = Image.new("L", img.size)
    eimg.putdata([255 if v else 0 for row in binary for v in row])
    return gimg, eimg, result, counts, skipped