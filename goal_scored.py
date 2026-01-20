def check_goal_scored(curr_pos, prev_pos, goal_latched):
    """
    Line-crossing goal detection for LEFT TEAM.
    Goal line: (50,13) -> (79,13)
    Uses FIELD coordinates (pixels).
    """

    if prev_pos is None or goal_latched:
        return None, goal_latched

    x, y = curr_pos
    px, py = prev_pos

    # --------------------------------
    # LEFT TEAM GOAL LINE (HORIZONTAL)
    # --------------------------------
    GOAL_Y = 13
    GOAL_X_MIN = 50
    GOAL_X_MAX = 79

    # Check X range (ball must be inside goal mouth)
    if GOAL_X_MIN <= x <= GOAL_X_MAX:

        # Check Y crossing (ball moves from field into goal)
        # Assumption: field is BELOW the goal (y increases downward)
        if py > GOAL_Y and y <= GOAL_Y:
            return "TEAM2", True   # Left team scored

    return None, goal_latched
