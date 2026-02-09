import math

def get_speed_ms(x1, y1, t1, x2, y2, t2):
    """
    Calculate ball speed in meters per second based on two position measurements.
    
    This function converts pixel-based movement to real-world speed by:
    1. Applying calibration factors to convert pixels to meters
    2. Calculating Euclidean distance in real-world coordinates
    3. Dividing by time elapsed to get speed
    
    Args:
        x1 (float): Initial x-coordinate in pixels
        y1 (float): Initial y-coordinate in pixels
        t1 (float): Initial timestamp in seconds
        x2 (float): Final x-coordinate in pixels
        y2 (float): Final y-coordinate in pixels
        t2 (float): Final timestamp in seconds
    
    Returns:
        float: Speed in meters per second (m/s). Returns 0.0 if time difference is invalid.
    
    Calibration:
        Based on foosball table dimensions:
        - Table length: 1.2m spans 218 pixels
        - Table width: 0.7m spans 131 pixels
        
    Example:
        >>> # Ball moves from (100, 50) at t=0.0 to (150, 80) at t=0.5
        >>> speed = get_speed_ms(100, 50, 0.0, 150, 80, 0.5)
        >>> print(f"Ball speed: {speed:.2f} m/s")
    
    Note:
        Calibration values must be updated if camera position, zoom, or 
        table dimensions change.
    """
    
    # ========== CALIBRATION CONSTANTS ==========
    # These values map pixel distances to real-world meters
    # Measured from camera frame with ROI of 218x131 pixels
    
    # Horizontal calibration: table length (1.2m) / pixel width (218px)
    M_PER_PX_X = 1.2 / 218  # ≈ 0.0055 meters per pixel (length direction)
    
    # Vertical calibration: table width (0.7m) / pixel height (131px)
    M_PER_PX_Y = 0.7 / 131  # ≈ 0.0053 meters per pixel (width direction)
    
    # ===========================================
    
    # Step 1: Convert pixel displacement to real-world meters
    dist_x_m = (x2 - x1) * M_PER_PX_X  # Horizontal distance in meters
    dist_y_m = (y2 - y1) * M_PER_PX_Y  # Vertical distance in meters
    
    # Step 2: Calculate total Euclidean distance in meters using Pythagorean theorem
    # Important: Apply theorem AFTER converting to meters, not before
    total_dist_m = math.sqrt(dist_x_m**2 + dist_y_m**2)
    
    # Step 3: Calculate time elapsed
    dt = t2 - t1  # Time difference in seconds
    
    # Step 4: Calculate speed (distance / time)
    if dt > 0:
        return total_dist_m / dt  # Speed in m/s
    else:
        return 0.0  # Prevent division by zero or negative time
