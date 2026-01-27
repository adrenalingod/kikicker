def check_goal_scored(curr_pos, prev_pos, goal_latched):
    if goal_latched:
        return None, True

    GOAL_X = 68
    Y_MIN, Y_MAX = 103, 130
    
    # SCENARIO A: The ball is visible and past the line
    if curr_pos is not None:
        cx, cy = curr_pos
        if cx <= GOAL_X and Y_MIN <= cy <= Y_MAX:
            return "TEAM2", True

    # SCENARIO B: The ball is GONE (Under player or in net)
    # If the last time we saw it, it was very close to the goal
    elif curr_pos is None and prev_pos is not None:
        px, py = prev_pos
        
        # If last seen within 15 pixels of the goal line and moving in
        if px < (GOAL_X + 15) and Y_MIN <= py <= Y_MAX:
            return "TEAM2", True

    return None, False
