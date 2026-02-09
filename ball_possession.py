import math

def get_ball_possession(bx, by):
    """
    Determine ball possession based on ball coordinates in a foosball table.
    
    Algorithm:
    1. Check if ball is inside any rod's zone (with margin)
    2. If inside a zone → assign to that team
    3. If outside all zones → assign to team with closest rod
    
    Args:
        bx (int): Ball x-coordinate in pixels
        by (int): Ball y-coordinate in pixels
    
    Returns:
        str: "WHITE" or "BLACK" indicating which team has possession
    
    Note:
        Coordinates are based on camera frame with origin at top-left.
        Rod zones are defined as rectangles with 5-pixel margin for tolerance.
    """
    
    # Margin around each rod zone for ball possession detection (in pixels)
    margin = 5
    
    # WHITE team rod positions (goalies, defenders, midfielders, attackers)
    # Each tuple is ((x1, y1), (x2, y2)) defining rectangle corners
    white_rods = [
        ((22, 6),    (13, 113)),   # Rod 1
        ((42, 113),  (49, 6)),     # Rod 2
        ((98, 118),  (94, 13)),    # Rod 3
        ((147, 122), (150, 12)),   # Rod 4
    ]
    
    # BLACK team rod positions (goalies, defenders, midfielders, attackers)
    black_rods = [
        ((177, 12),  (178, 124)),  # Rod 1
        ((201, 116), (201, 21)),   # Rod 2
        ((120, 119), (121, 12)),   # Rod 3
        ((67, 8),    (61, 118)),   # Rod 4
    ]
    
    def inside_rect(x, y, rect):
        """Check if point (x, y) is inside rectangle with margin."""
        (x1, y1), (x2, y2) = rect
        x_min = min(x1, x2) - margin
        x_max = max(x1, x2) + margin
        y_min = min(y1, y2) - margin
        y_max = max(y1, y2) + margin
        return x_min <= x <= x_max and y_min <= y <= y_max
    
    # Step 1: Check if ball is inside any WHITE rod zone
    for rect in white_rods:
        if inside_rect(bx, by, rect):
            return "WHITE"
    
    # Step 2: Check if ball is inside any BLACK rod zone
    for rect in black_rods:
        if inside_rect(bx, by, rect):
            return "BLACK"
    
    # Step 3: Ball is outside all zones → assign to closest rod's team
    def rect_center(rect):
        """Calculate center point of a rectangle."""
        (x1, y1), (x2, y2) = rect
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    # Calculate distances from ball to all rod centers
    white_distances = [
        math.hypot(bx - cx, by - cy) 
        for cx, cy in map(rect_center, white_rods)
    ]
    black_distances = [
        math.hypot(bx - cx, by - cy) 
        for cx, cy in map(rect_center, black_rods)
    ]
    
    # Find closest rod for each team
    min_white = min(white_distances)
    min_black = min(black_distances)
    
    # Assign possession to team with closest rod
    return "WHITE" if min_white <= min_black else "BLACK"
