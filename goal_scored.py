def check_goal_scored(curr_pos, prev_pos, goal_latched):
    """
    Goal detection using LINE-CROSSING + RECTANGLE
    Returns:
        goal (None | "TEAM_1" | "TEAM_2"),
        updated_goal_latched
    """

    if curr_pos is None or prev_pos is None:
        return None, goal_latched

    x_curr, y_curr = curr_pos
    x_prev, y_prev = prev_pos

    # -----------------------------
    # TEAM 1 GOAL (RIGHT SIDE)
    # -----------------------------
    TEAM1_X_MIN = 216
    TEAM1_X_MAX = 220
    TEAM1_Y_MIN = 157
    TEAM1_Y_MAX = 182

    # -----------------------------
    # TEAM 2 GOAL (LEFT SIDE)
    # -----------------------------
    TEAM2_X_MIN = 50
    TEAM2_X_MAX = 80
    TEAM2_Y_MIN = 15
    TEAM2_Y_MAX = 16

    # -----------------------------
    # Reset latch if ball leaves all goal areas
    # -----------------------------
    if not (
        (TEAM1_X_MIN <= x_curr <= TEAM1_X_MAX and TEAM1_Y_MIN <= y_curr <= TEAM1_Y_MAX) or
        (TEAM2_X_MIN <= x_curr <= TEAM2_X_MAX and TEAM2_Y_MIN <= y_curr <= TEAM2_Y_MAX)
    ):
        goal_latched = False

    if goal_latched:
        return None, goal_latched

    # -----------------------------
    # TEAM 1 SCORES (ball moves RIGHT into Team1 goal)
    # -----------------------------
    if (
        x_prev < TEAM1_X_MIN and
        TEAM1_X_MIN <= x_curr <= TEAM1_X_MAX and
        TEAM1_Y_MIN <= y_curr <= TEAM1_Y_MAX
    ):
        return "TEAM_1", True

    # -----------------------------
    # TEAM 2 SCORES (ball moves LEFT into Team2 goal)
    # -----------------------------
    if (
        x_prev > TEAM2_X_MAX and
        TEAM2_X_MIN <= x_curr <= TEAM2_X_MAX and
        TEAM2_Y_MIN <= y_curr <= TEAM2_Y_MAX
    ):
        return "TEAM_2", True

    return None, goal_latched
