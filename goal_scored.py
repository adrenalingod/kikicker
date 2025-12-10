def check_for_goal_event(curr_pos, prev_pos):
    """
    Checks if the current ball position (curr_pos) is in the goal 
    AND if its velocity (calculated using prev_pos) is pointing inward.
    
    This function implements the "angle pierces goal region" requirement.
    The final score confirmation (ball disappearance) must be handled 
    by the external main loop's state management (using a flag).

    :param curr_pos: (x, y) tuple (Current ball coordinate in pixels)
    :param prev_pos: (x, y) tuple (Previous ball coordinate in pixels)
    :return: (Boolean goal_scored, String goal_side)
    """
    
    # ----------------------------------------------------
    # PIXEL CONSTANTS (DEFINE THESE ACCURATELY based on your camera setup)
    # Assuming a 1280x720 pixel space for example:
    # ----------------------------------------------------
    X_GOAL_A_LINE = 10     # X-boundary for the back of the left goal
    X_GOAL_B_LINE = 1270   # X-boundary for the back of the right goal
    Y_MIN = 100            # Top Y-boundary of the goal opening
    Y_MAX = 620            # Bottom Y-boundary of the goal opening
    MIN_VELOCITY_X = 5     # Minimum speed (pixels/frame) for a scoring shot (prevents slow drift/jitter)

    # Ensure positions are valid tuples before proceeding
    if prev_pos is None or curr_pos is None:
        return False, "NO_GOAL"

    x_curr, y_curr = curr_pos
    x_prev, y_prev = prev_pos

    # 1. Calculate Velocity Vector (dx is the horizontal direction/speed)
    dx = x_curr - x_prev

    # 2. Check Vertical Limits (Is the ball in the goal's height?)
    is_in_goal_height = (Y_MIN <= y_curr <= Y_MAX)
    if not is_in_goal_height:
        return False, "NO_GOAL"

    # 3. Check for Goal A (Left) - Position AND Angle Pierces
    # Ball must be past the line AND moving LEFT (dx must be negative)
    if x_curr <= X_GOAL_A_LINE:
        if dx < -MIN_VELOCITY_X: 
            return True, "GOAL_A" # Potential Goal Flag
        # Past the line but not moving inward (e.g., bouncing out or stopped)
        return False, "NO_GOAL" 

    # 4. Check for Goal B (Right) - Position AND Angle Pierces
    # Ball must be past the line AND moving RIGHT (dx must be positive)
    elif x_curr >= X_GOAL_B_LINE:
        if dx > MIN_VELOCITY_X:
            return True, "GOAL_B" # Potential Goal Flag
        # Past the line but not moving inward 
        return False, "NO_GOAL"
    
    # 5. Ball is in the field of play
    return False, "NO_GOAL"

# --- Example Test Usage (using the assumed constants) ---
# Goal B: Past the line (1275) and moving right (dx > 5)
print(f"Test 1 (Goal B Shot): {check_for_goal_event((1275, 400), (1260, 400))}") 

# No Goal: Past the line (5) but moving right (dx > -5) - e.g., bounced out
print(f"Test 2 (Bounce Out): {check_for_goal_event((5, 400), (8, 400))}")

# No Goal: Correct direction but outside vertical height
print(f"Test 3 (Too High): {check_for_goal_event((1275, 50), (1260, 50))}")
