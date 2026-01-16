def check_goal_scored(curr_pos, prev_pos, goal_latched):
    """
    Detects a valid goal event based on ball movement direction
    and entry into the goal region.

    Args:
        curr_pos (tuple): (x, y) current ball position in field coordinates
        prev_pos (tuple): (x, y) previous ball position in field coordinates
        goal_latched (bool): prevents multiple detections per shot

    Returns:
        (goal_scored: bool, updated_goal_latched: bool)
    """

    # Safety check
    if prev_pos is None or curr_pos is None:
        return False, goal_latched

    x_curr, y_curr = curr_pos
    x_prev, y_prev = prev_pos

    # Direction of movement
    dx = x_curr - x_prev

    # ---------- GOAL REGION (TUNE IN LAB) ----------
    LEFT_GOAL_X = 15
    RIGHT_GOAL_X = 370      # approx fw - 15 for 384 width
    GOAL_Y_MIN = 60
    GOAL_Y_MAX = 160
    # ----------------------------------------------

    # Must be inside vertical goal opening
    if not (GOAL_Y_MIN <= y_curr <= GOAL_Y_MAX):
        return False, goal_latched

    # LEFT GOAL (ball moving left)
    if x_curr <= LEFT_GOAL_X and dx < 0 and not goal_latched:
        return True, True

    # RIGHT GOAL (ball moving right)
    if x_curr >= RIGHT_GOAL_X and dx > 0 and not goal_latched:
        return True, True

    return False, goal_latched
