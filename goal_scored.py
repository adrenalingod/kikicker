def check_goal_scored(curr_pos, goal_latched):
    """
    Vertical goal line detection at x = 66.
    If ball crosses/touches the line between y=103 and y=130 -> GOAL.
    """

    if goal_latched:
        return None, True

    x, y = curr_pos

    # --------------------------------
    # NEW LEFT TEAM GOAL REGION (Vertical)
    # Line: (66, 103) -> (66, 130)
    # --------------------------------
    GOAL_X = 66
    GOAL_Y_MIN = 103
    GOAL_Y_MAX = 130
    X_TOLERANCE = 2  # Allows for small detection gaps as the ball moves fast

    # Check if x is near 66 AND y is within the goal mouth height
    if (GOAL_X - X_TOLERANCE <= x <= GOAL_X + X_TOLERANCE and
        GOAL_Y_MIN <= y <= GOAL_Y_MAX):
        return "TEAM2", True  # Goal confirmed

    return None, False
