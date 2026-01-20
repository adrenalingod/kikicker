def check_goal_scored(curr_pos, goal_latched):
    """
    Simple position-based goal detection.
    If ball is inside goal line region → GOAL.
    Uses FIELD coordinates (pixels).
    """

    if goal_latched:
        return None, True

    x, y = curr_pos

    # --------------------------------
    # LEFT TEAM GOAL REGION
    # Line: (50,13) -> (79,13)
    # --------------------------------
    GOAL_X_MIN = 50
    GOAL_X_MAX = 79
    GOAL_Y = 13
    Y_TOLERANCE = 2   # +/- pixels

    if (GOAL_X_MIN <= x <= GOAL_X_MAX and
        GOAL_Y - Y_TOLERANCE <= y <= GOAL_Y + Y_TOLERANCE):
        return "TEAM2", True   # Left team scored

    return None, False
