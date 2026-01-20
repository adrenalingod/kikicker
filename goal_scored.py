# goalCheck.py

# ================= GOAL LINE DEFINITIONS =================
# These are FIELD COORDINATES (field_x, field_y)

# Right goal → TEAM 1
TEAM1_GOAL_LINE_X = 215
TEAM1_GOAL_Y_MIN = 150
TEAM1_GOAL_Y_MAX = 190

# Left goal → TEAM 2
TEAM2_GOAL_LINE_X = 55
TEAM2_GOAL_Y_MIN = 10
TEAM2_GOAL_Y_MAX = 30


def check_goal_scored(curr_pos, prev_pos, goal_latched):
    """
    Detects goal using line-crossing logic.

    Args:
        curr_pos (tuple): (field_x, field_y)
        prev_pos (tuple): (field_x, field_y)
        goal_latched (bool): prevents double scoring

    Returns:
        goal (str | None): "TEAM1", "TEAM2", or None
        goal_latched (bool)
    """

    # Cannot detect crossing without previous position
    if prev_pos is None:
        return None, goal_latched

    cx, cy = curr_pos
    px, py = prev_pos

    # Prevent double goal detection
    if goal_latched:
        return None, goal_latched

    # ---------------- TEAM 1 GOAL (Right side) ----------------
    if TEAM1_GOAL_Y_MIN <= cy <= TEAM1_GOAL_Y_MAX:
        if px < TEAM1_GOAL_LINE_X and cx >= TEAM1_GOAL_LINE_X:
            return "TEAM1", True

    # ---------------- TEAM 2 GOAL (Left side) -----------------
    if TEAM2_GOAL_Y_MIN <= cy <= TEAM2_GOAL_Y_MAX:
        if px > TEAM2_GOAL_LINE_X and cx <= TEAM2_GOAL_LINE_X:
            return "TEAM2", True

    return None, goal_latched
