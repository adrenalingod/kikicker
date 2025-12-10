import math

def compute_ball_metrics(prev_pos, curr_pos, prev_frame, curr_frame):
    """
    Computes speed and angle when coordinates are in centimeters.
    
    Args:
        prev_pos: (x1, y1) in centimeters
        curr_pos: (x2, y2) in centimeters
        prev_frame: int
        curr_frame: int
    
    Returns:
        (speed_m_s, angle_rad, distance_cm)
    """
    x1, y1 = prev_pos
    x2, y2 = curr_pos
    
    # Distance in centimeters
    dx = x2 - x1
    dy = y2 - y1
    distance_cm = math.hypot(dx, dy)
    
    # Convert to meters
    distance_m = distance_cm / 100.0
    
    # Time calculation
    fps = 120
    frame_diff = curr_frame - prev_frame
    time_s = frame_diff / fps if frame_diff > 0 else 0.0
    
    # Speed in m/s
    speed_m_s = distance_m / time_s if time_s > 0 else 0.0
    
    # Angle calculation
    angle_rad = math.atan2(dy, dx)
    if angle_rad < 0:
        angle_rad += 2 * math.pi
    
    return speed_m_s, angle_rad, distance_cm

# Your example
print(compute_ball_metrics((1000, 620), (30, 120), 20, 30))
