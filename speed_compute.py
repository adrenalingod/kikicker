import math

def get_speed_ms(x1, y1, t1, x2, y2, t2):
    # 1. Distance between coordinates in pixels
    pixel_dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # 2. Convert to meters (1.2m / 250px = 0.0048)
    dist_m = pixel_dist * 0.0048
    
    # 3. Time difference in seconds
    dt = t2 - t1
    
    # 4. Return the raw number in m/s
    if dt > 0:
        return dist_m / dt
    return 0.0
