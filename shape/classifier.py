# -*- coding: utf-8 -*-
import math
from shape.occlusion import classify_occluded
from config import (
    ANGLE_TOL, CIRCLE_RATIO, ELLIPSE_CV, ELLIPSE_CV_PX,
    ELLIPSE_MIN_RATIO, MERGE_RATIO, MIN_TURN, POLY_KEY,
    SOLIDITY_MIN, SQUARE_RATIO,
)
from shape.geometry import (
    approx_polygon, boundary_points, convex_hull,
    ellipse_stats, poly_area, poly_perimeter,
)


def classify(r):
    pix = r["pix"]
    pts = boundary_points(pix)
    hull = convex_hull(pts)
    if len(hull) < 3:
        return None, hull

    per = poly_perimeter(hull)
    hull_pixels = poly_area(hull) + per / 2 + 1
    if len(pix) / hull_pixels < SOLIDITY_MIN:
        # Vùng bị khuyết/lõm -> chuyển sang nhánh khớp hình bị che khuất (RANSAC)
        return classify_occluded(pts, hull)

    es = ellipse_stats(pix, pts)
    if es is not None and es[0] <= ELLIPSE_CV + ELLIPSE_CV_PX / es[2]:
        ratio = es[1]
        if ratio >= CIRCLE_RATIO:
            return "Hinh tron", hull
        if ratio >= ELLIPSE_MIN_RATIO:
            return "Elip", hull
        return None, hull

    poly = approx_polygon(hull, max(2.0, 0.03 * per))

    while len(poly) > 3:
        n = len(poly)
        turns = []
        for i in range(n):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
            h1 = math.atan2(b[1] - a[1], b[0] - a[0])
            h2 = math.atan2(c[1] - b[1], c[0] - b[0])
            d = abs(math.degrees(h2 - h1)) % 360
            turns.append(min(d, 360 - d))
        i = turns.index(min(turns))
        if turns[i] >= MIN_TURN:
            break
        poly = poly[:i] + poly[i + 1:]

    while len(poly) > 3:
        n = len(poly)
        sides = [math.dist(poly[i], poly[(i + 1) % n]) for i in range(n)]
        i = sides.index(min(sides))
        if sides[i] >= MERGE_RATIO * sum(sides):
            break
        j = (i + 1) % n
        mid = ((poly[i][0] + poly[j][0]) / 2, (poly[i][1] + poly[j][1]) / 2)
        poly = [mid if k == i else poly[k] for k in range(n) if k != j]

    n = len(poly)
    if n == 3:
        return "Tam giac", poly
    if n == 4:
        max_dev = 0
        for i in range(4):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % 4]
            v1 = (a[0] - b[0], a[1] - b[1])
            v2 = (c[0] - b[0], c[1] - b[1])
            cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2) + 1e-9)
            ang = math.degrees(math.acos(max(-1, min(1, cosang))))
            max_dev = max(max_dev, abs(ang - 90))
        if max_dev > ANGLE_TOL:
            return "Tu giac", poly
        s = [math.dist(poly[i], poly[(i + 1) % 4]) for i in range(4)]
        w, h = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
        return ("Hinh vuong" if min(w, h) / max(w, h) >= SQUARE_RATIO else "Hinh chu nhat"), poly
    if n in POLY_KEY:
        return POLY_KEY[n], poly
    return None, poly