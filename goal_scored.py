def check_goal_scored(curr_pos, pos_history, goal_latched):
    """
    pos_history: A list of the last 2 detected (x, y) tuples.
    """
    if goal_latched:
        return None, True

    GOAL_X_LINE = 68
    Y_MIN, Y_MAX = 103, 130

    # CASE 1: Ball is visible and past the line
    if curr_pos is not None:
        cx, cy = curr_pos
        if cx <= GOAL_X_LINE and Y_MIN <= cy <= Y_MAX:
            return "TEAM2", True

    # CASE 2: Ball disappears - Check Trajectory of last 2 points
    elif curr_pos is None and len(pos_history) == 2:
        pos1 = pos_history[0] # Older point
        pos2 = pos_history[1] # Most recent point
        
        # Calculate horizontal movement (delta x)
        dx = pos2[0] - pos1[0]
        
        # If moving LEFT (dx is negative) AND last seen near goal
        if dx < -5 and pos2[0] < 100 and Y_MIN <= pos2[1] <= Y_MAX:
            return "TEAM2", True

    return None, False
