def get_speed_ms(x1, y1, t1, x2, y2, t2):
    # Calibration based on your actual measurements
    M_PER_PX_X = 1.2 / 218  # ≈ 0.0055 m/px (length)
    M_PER_PX_Y = 0.7 / 131  # ≈ 0.0053 m/px (width)
    
    # Convert pixel movement to meters
    dist_x_m = (x2 - x1) * M_PER_PX_X
    dist_y_m = (y2 - y1) * M_PER_PX_Y
    
    # Pythagorean theorem on meter values
    total_dist_m = math.sqrt(dist_x_m**2 + dist_y_m**2)
    
    # Time difference
    dt = t2 - t1
    
    if dt > 0:
        return total_dist_m / dt
    return 0.0
