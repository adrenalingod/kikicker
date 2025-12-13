import math
from typing import Optional, Tuple


class BounceDetector:
    def __init__(self, angle_threshold_rad: float = 0.25, min_displacement: float = 5.0):
        """
        :param angle_threshold_rad: Minimum angular change (radians) to detect bounce
        :param min_displacement: Minimum pixel displacement to avoid noise
        """
        self.angle_threshold = angle_threshold_rad
        self.min_displacement = min_displacement
        self._prev_angle: Optional[float] = None

    @staticmethod
    def _normalize_angle(delta: float) -> float:
        """Normalize angle difference to [-pi, pi]."""
        while delta <= -math.pi:
            delta += 2 * math.pi
        while delta > math.pi:
            delta -= 2 * math.pi
        return delta

    def _compute_angle(self, prev_pos: Tuple[float, float],
                       curr_pos: Tuple[float, float]) -> Optional[float]:
        """Compute motion angle between two positions."""
        dx = curr_pos[0] - prev_pos[0]
        dy = curr_pos[1] - prev_pos[1]

        if math.hypot(dx, dy) < self.min_displacement:
            return None

        return math.atan2(dy, dx)

    def update(self, prev_pos: Tuple[float, float],
               curr_pos: Tuple[float, float]) -> dict:
        """
        Update detector with new position.

        :returns: Dictionary with bounce status and angle change (degrees)
        """
        curr_angle = self._compute_angle(prev_pos, curr_pos)

        if curr_angle is None or self._prev_angle is None:
            self._prev_angle = curr_angle
            return {"bounce": False}

        delta = self._normalize_angle(curr_angle - self._prev_angle)
        self._prev_angle = curr_angle

        if abs(delta) >= self.angle_threshold:
            return {
                "bounce": True,
                "angle_change_deg": abs(math.degrees(delta))
            }

        return {"bounce": False}
