# -*- coding: utf-8 -*-
import math


def boundary_points(pix):
    s = set(pix)
    return [
        (x, y) for (x, y) in pix
        if any((x + dx, y + dy) not in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    ]


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def dist_point_line(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    return abs(dx * (p[1] - a[1]) - dy * (p[0] - a[0])) / n


def rdp(points, eps):
    if len(points) < 3:
        return points
    a, b = points[0], points[-1]
    idx, dmax = 0, 0
    for i in range(1, len(points) - 1):
        d = dist_point_line(points[i], a, b)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = rdp(points[:idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [a, b]


def approx_polygon(hull, eps):
    n = len(hull)
    if n < 4:
        return hull
    a = hull[0]
    k = max(range(n), key=lambda i: (hull[i][0] - a[0]) ** 2 + (hull[i][1] - a[1]) ** 2)
    c1 = rdp(hull[:k + 1], eps)
    c2 = rdp(hull[k:] + [hull[0]], eps)
    return c1[:-1] + c2[:-1]


def poly_perimeter(poly):
    return sum(math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def poly_area(poly):
    s = 0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def ellipse_stats(pix, pts):
    n = len(pix)
    cx = sum(p[0] for p in pix) / n
    cy = sum(p[1] for p in pix) / n
    sxx = sum((p[0] - cx) ** 2 for p in pix) / n
    syy = sum((p[1] - cy) ** 2 for p in pix) / n
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pix) / n
    half = (sxx + syy) / 2
    root = math.sqrt(((sxx - syy) / 2) ** 2 + sxy ** 2)
    l1, l2 = half + root, half - root
    if l2 <= 1e-6 or not pts:
        return None
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ct, st = math.cos(th), math.sin(th)
    a, b = 2 * math.sqrt(l1), 2 * math.sqrt(l2)
    rs = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        u = (dx * ct + dy * st) / a
        v = (-dx * st + dy * ct) / b
        rs.append(math.hypot(u, v))
    mean = sum(rs) / len(rs)
    std = math.sqrt(sum((r - mean) ** 2 for r in rs) / len(rs))
    return std / mean, b / a, b