def check_goal_scored(curr_pos, goal_latched):
    """
    Goal triggered if ball passes x=68 (moving left) 
    within the y-range of 103 to 130.
    """

    if goal_latched:
        return None, True

    x, y = curr_pos

    # --------------------------------
    # LEFT GOAL ZONE
    # --------------------------------
    GOAL_THRESHOLD_X = 68
    GOAL_Y_MIN = 103
    GOAL_Y_MAX = 130

    # Logic: If x is 68 or smaller, and y is within the posts
    if x <= GOAL_THRESHOLD_X and GOAL_Y_MIN <= y <= GOAL_Y_MAX:
        return "TEAM2", True  

    return None, False
