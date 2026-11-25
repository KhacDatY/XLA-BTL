# -*- coding: utf-8 -*-
import math
import random
from config import ANGLE_TOL, POLY_KEY, SQUARE_RATIO


def _circumcircle(p1, p2, p3):
    """Tính tâm (cx, cy) và bán kính R của đường tròn đi qua 3 điểm."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-6:
        return None
    u1 = x1 * x1 + y1 * y1
    u2 = x2 * x2 + y2 * y2
    u3 = x3 * x3 + y3 * y3
    cx = (u1 * (y2 - y3) + u2 * (y3 - y1) + u3 * (y1 - y2)) / d
    cy = (u1 * (x3 - x2) + u2 * (x1 - x3) + u3 * (x2 - x1)) / d
    r = math.hypot(cx - x1, cy - y1)
    return cx, cy, r


def _longest_continuous_arc(cx, cy, points, max_gap_deg=15.0):
    """
    Tính độ dài (độ) của cung tròn LIÊN TỤC dài nhất (không bị đứt quãng quá max_gap_deg).
    Giúp phân biệt cung tròn thật với 3-4 tiếp điểm rời rạc của hình vuông.
    """
    if len(points) < 2:
        return 0.0
    angles = sorted(math.degrees(math.atan2(y - cy, x - cx)) for x, y in points)
    n = len(angles)

    # Tìm các vị trí bị đứt quãng (khoảng trống > max_gap_deg)
    gaps = []
    for i in range(n):
        nxt = angles[(i + 1) % n] + (360.0 if i == n - 1 else 0.0)
        if nxt - angles[i] > max_gap_deg:
            gaps.append(i)

    if not gaps:
        return 360.0  # Khép kín hoàn toàn, không có khoảng hở nào

    # Tính độ dài từng đoạn cung liên tục nằm giữa 2 khoảng hở liên tiếp
    max_arc = 0.0
    for k in range(len(gaps)):
        start_idx = (gaps[k] + 1) % n
        end_idx = gaps[(k + 1) % len(gaps)]
        arc = angles[end_idx] - angles[start_idx]
        if arc < 0:
            arc += 360.0
        max_arc = max(max_arc, arc)
    return max_arc


def _circle_to_poly(cx, cy, r, steps=36):
    """Tạo đa giác 36 đỉnh để vẽ đường tròn khôi phục lên ảnh."""
    return [
        (cx + r * math.cos(2 * math.pi * i / steps),
         cy + r * math.sin(2 * math.pi * i / steps))
        for i in range(steps)
    ]


def fit_occluded_circle(pts, min_arc=95.0, min_cov=0.40, tol=1.5, iters=300):
    """
    Khớp đường tròn bị che khuất bằng RANSAC.
    Siết chặt tol=1.5 và yêu cầu cung tròn liên tục >= 95 độ để tránh khớp nhầm hình vuông.
    """
    n = len(pts)
    if n < 20:
        return None

    rng = random.Random(42)
    best_circle = None
    best_inliers = []

    for _ in range(iters):
        p1, p2, p3 = rng.sample(pts, 3)
        c = _circumcircle(p1, p2, p3)
        if c is None:
            continue
        cx, cy, r = c
        if r < 10 or r > 220:
            continue

        inliers = [p for p in pts if abs(math.hypot(p[0] - cx, p[1] - cy) - r) <= tol]
        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_circle = (cx, cy, r)

    if best_circle is None:
        return None

    cx, cy, r = best_circle
    circumference = 2 * math.pi * r
    coverage = len(best_inliers) / max(1.0, circumference)
    arc = _longest_continuous_arc(cx, cy, best_inliers)

    if arc >= min_arc and coverage >= min_cov:
        return _circle_to_poly(cx, cy, r)
    return None


def _line_from_2pts(p1, p2):
    """Phương trình đường thẳng chuẩn hóa ax + by + c = 0 (a^2 + b^2 = 1)."""
    a = p1[1] - p2[1]
    b = p2[0] - p1[0]
    norm = math.hypot(a, b)
    if norm < 1e-6:
        return None
    a, b = a / norm, b / norm
    c = -(a * p1[0] + b * p1[1])
    return a, b, c


def _intersect_lines(l1, l2):
    """Tìm giao điểm của 2 đường thẳng ax + by + c = 0."""
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-3:  # Song song hoặc gần song song
        return None
    x = (b1 * c2 - b2 * c1) / det
    y = (c1 * a2 - c2 * a1) / det
    return x, y


def _is_supporting_line(line, hull, tol=3.0):
    """
    Kiểm tra đường thẳng có phải là cạnh ngoài (đường tựa) của đa giác hay không:
    Toàn bộ đỉnh bao lồi phải nằm về một phía của đường thẳng.
    Trả về (True, line_đã_chuẩn_hóa_hướng) nếu đúng.
    """
    a, b, c = line
    dists = [a * x + b * y + c for x, y in hull]
    pos = sum(1 for d in dists if d > tol)
    neg = sum(1 for d in dists if d < -tol)
    if pos > 0 and neg > 0:
        return False, None  # Có điểm ở cả 2 phía -> đây là nét cắt lõm (che khuất)
    if neg > 0:
        # Đảo dấu để toàn bộ vùng luôn nằm về phía dương (>= 0)
        return True, (-a, -b, -c)
    return True, (a, b, c)


def fit_occluded_polygon(pts, hull, tol=2.2, min_inliers=14):
    """
    Khớp đa giác bị che khuất bằng RANSAC Line + lọc đường tựa + tìm giao điểm.
    Trả về (key, poly) hoặc (None, hull).
    """
    remaining = list(pts)
    rng = random.Random(42)
    supporting_lines = []

    # Trích xuất tối đa 8 đoạn thẳng chính bằng RANSAC
    for _ in range(8):
        if len(remaining) < min_inliers:
            break
        best_line = None
        best_inliers = []

        for _ in range(120):
            p1, p2 = rng.sample(remaining, 2)
            if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < 8:
                continue
            line = _line_from_2pts(p1, p2)
            if line is None:
                continue
            a, b, c = line
            inliers = [p for p in remaining if abs(a * p[0] + b * p[1] + c) <= tol]
            if len(inliers) > len(best_inliers):
                best_inliers = inliers
                best_line = line

        if len(best_inliers) < min_inliers:
            break

        # Loại bỏ các điểm đã khớp để tìm cạnh tiếp theo
        inlier_set = set(best_inliers)
        remaining = [p for p in remaining if p not in inlier_set]

        # Chỉ giữ lại cạnh ngoài (đường tựa), bỏ qua nét cắt che khuất
        ok, oriented = _is_supporting_line(best_line, hull)
        if ok:
            # Tránh thêm trùng 2 đường thẳng gần giống hệt nhau
            a, b, c = oriented
            is_dup = any(
                abs(a * la + b * lb) > 0.98 and abs(c - lc) < 8.0
                for la, lb, lc in supporting_lines
            )
            if not is_dup:
                supporting_lines.append(oriented)

    if len(supporting_lines) < 3:
        return None, hull

        # Xử lý riêng trường hợp chữ U: 3 cạnh (2 cạnh song song + 1 cạnh vuông góc)
        # -> Bổ sung cạnh thứ 4 song song với cạnh vuông góc đi qua điểm xa nhất của hull
    if len(supporting_lines) == 3:
        for i in range(3):
            l1, l2, l3 = supporting_lines[i], supporting_lines[(i + 1) % 3], supporting_lines[(i + 2) % 3]
            # Kiểm tra l1 và l2 có ngược hướng (song song) và l3 vuông góc với l1 không
            dot_12 = l1[0] * l2[0] + l1[1] * l2[1]
            dot_13 = abs(l1[0] * l3[0] + l1[1] * l3[1])
            if dot_12 < -0.95 and dot_13 < 0.2:
                # Dựng cạnh thứ 4 đối diện l3: pháp tuyến ngược dấu (-a3, -b3)
                a4, b4 = -l3[0], -l3[1]
                # Chọn c4 sao cho toàn bộ điểm hull nằm về phía dương (a4*x + b4*y + c4 >= 0)
                c4 = -min(a4 * x + b4 * y for x, y in hull)
                supporting_lines.append((a4, b4, c4))
                break

        # Sắp xếp các đường tựa theo góc pháp tuyến (ngược chiều kim đồng hồ)
    supporting_lines.sort(key=lambda l: math.atan2(l[1], l[0]))

    # Tìm giao điểm các cạnh liên tiếp để khôi phục đỉnh bị che khuất
    poly = []
    n = len(supporting_lines)
    for i in range(n):
        pt = _intersect_lines(supporting_lines[i], supporting_lines[(i + 1) % n])
        if pt is None:
            return None, hull
        poly.append(pt)

    # Phân loại đa giác đã khôi phục
    if n == 3:
        return "Tam giac", poly
    if n == 4:
        max_dev = 0.0
        for i in range(4):
            p_prev, p_curr, p_next = poly[i - 1], poly[i], poly[(i + 1) % 4]
            v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
            v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2) + 1e-9)
            ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
            max_dev = max(max_dev, abs(ang - 90))
        if max_dev > ANGLE_TOL:
            return "Tu giac", poly
        s = [math.dist(poly[i], poly[(i + 1) % 4]) for i in range(4)]
        w, h = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
        return ("Hinh vuong" if min(w, h) / max(w, h) >= SQUARE_RATIO else "Hinh chu nhat"), poly
    if n in POLY_KEY:
        return POLY_KEY[n], poly
    return None, hull


def classify_occluded(pts, hull):
    """Ưu tiên khớp hình tròn với điều kiện cung liên tục chặt, sau đó mới khớp đa giác."""
    circle_poly = fit_occluded_circle(pts)
    if circle_poly is not None:
        return "Hinh tron", circle_poly
    return fit_occluded_polygon(pts, hull)