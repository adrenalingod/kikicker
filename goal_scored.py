def check_goal_scored(curr_pos, pos_history, goal_latched):
    """
    Returns (Score_ID, Latched_Status)
    0 = White Scored
    1 = Black Scored
    """
    if goal_latched:
        return None, True

    # --- GOAL DEFINITIONS ---
    # Black Goal (Left Side)
    L_X = 68
    L_Y = (103, 130)
    
    # White Goal (Right Side)
    R_X = 275
    R_Y = (113, 141)

    # 1. VISIBLE CHECK (Direct Detection)
    if curr_pos is not None:
        cx, cy = curr_pos
        # Check Left Goal (Black Scored)
        if cx <= L_X and L_Y[0] <= cy <= L_Y[1]:
            return 1, True
        # Check Right Goal (White Scored)
        if cx >= R_X and R_Y[0] <= cy <= R_Y[1]:
            return 0, True

    # 2. TRAJECTORY CHECK (Occlusion/Missing Ball)
    elif curr_pos is None and len(pos_history) == 2:
        (x1, y1) = pos_history[0] 
        (x2, y2) = pos_history[1] 
        dx = x2 - x1 

        # Moving LEFT toward Black Goal
        if dx < -2 and x2 < (L_X + 25) and L_Y[0] <= y2 <= L_Y[1]:
            return 1, True
            
        # Moving RIGHT toward White Goal
        if dx > 2 and x2 > (R_X - 25) and R_Y[0] <= y2 <= R_Y[1]:
            return 0, True

    return None, False
