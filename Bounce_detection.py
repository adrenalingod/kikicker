import math
from typing import Optional, Tuple, Dict


def normalize_angle(delta: float) -> float:
    while delta <= -math.pi:
        delta += 2 * math.pi
    while delta > math.pi:
        delta -= 2 * math.pi
    return delta


def compute_angle(
    prev_pos: Tuple[float, float],
    curr_pos: Tuple[float, float],
    min_displacement: float
) -> Optional[float]:
    dx = curr_pos[0] - prev_pos[0]
    dy = curr_pos[1] - prev_pos[1]

    if math.hypot(dx, dy) < min_displacement:
        return None

    return math.atan2(dy, dx)


def bounce_detector(
    prev_pos: Tuple[float, float],
    curr_pos: Tuple[float, float],
    prev_angle: Optional[float],
    angle_threshold_rad: float = 0.25,
    min_displacement: float = 5.0
) -> Tuple[Dict, Optional[float]]:
    curr_angle = compute_angle(prev_pos, curr_pos, min_displacement)

    if curr_angle is None or prev_angle is None:
        return {"bounce": False}, curr_angle

    delta = normalize_angle(curr_angle - prev_angle)

    if abs(delta) >= angle_threshold_rad:
        return {
            "bounce": True,
            "angle_change_deg": abs(math.degrees(delta))
        }, curr_angle

    return {"bounce": False}, curr_angle
