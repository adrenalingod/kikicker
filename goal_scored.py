import cv2

def check_goal_scored(curr_pos, pos_history, goal_latched):
    """
    Detect if a goal has been scored in a foosball game.
    
    Uses two detection methods:
    1. Direct detection: Ball is visible inside goal zone
    2. Trajectory detection: Ball disappeared near goal while moving toward it
    
    The function implements a "latch" mechanism to prevent duplicate goal 
    detection until the ball is reset for the next round.
    
    Args:
        curr_pos (tuple or None): Current ball position as (x, y) in pixels.
                                  None if ball is not currently detected.
        pos_history (list): List of recent ball positions, used for trajectory
                           analysis when ball disappears. Should contain last
                           2 positions as [(x1, y1), (x2, y2)].
        goal_latched (bool): Whether a goal has already been detected and not
                            yet reset. Prevents duplicate goal counting.
    
    Returns:
        tuple: (score_id, latched_status)
            - score_id (str or None): 
                * "White TEAM1" if white team scored
                * "Black TEAM2" if black team scored  
                * None if no goal detected
            - latched_status (bool): Updated latch state
                * True if goal was just scored or already latched
                * False if no goal detected
    
    Goal Zones (based on camera frame coordinates):
        - Black Goal (Left): x ≤ 7, y in [45, 75]
        - White Goal (Right): x ≥ 212, y in [50, 85]
    
    Trajectory Detection:
        Activates when ball disappears (curr_pos is None) near a goal while
        moving toward it. Requires:
        - Minimum horizontal velocity (|dx| > 2 pixels)
        - Ball within 20 pixels of goal entrance
        - Ball's y-coordinate within goal zone
    
    Example:
        >>> # Ball visible in left goal
        >>> score, latched = check_goal_scored((5, 60), [], False)
        >>> print(score)  # "Black TEAM2"
        
        >>> # Ball disappeared while moving right toward goal
        >>> history = [(180, 65), (195, 67)]
        >>> score, latched = check_goal_scored(None, history, False)
        >>> print(score)  # "White TEAM1"
        
        >>> # Goal already latched, prevent duplicate
        >>> score, latched = check_goal_scored((5, 60), [], True)
        >>> print(score)  # None
    
    Note:
        The latch must be reset externally (by setting goal_latched=False)
        when starting a new round after a goal is scored.
    """
    
    # Prevent duplicate goal detection if already latched
    if goal_latched:
        return None, True
    
    # ========== GOAL ZONE DEFINITIONS ==========
    # Coordinates are based on camera frame (origin at top-left)
    
    # Black Team Goal (Left Side of Field)
    # Zone: x ≤ 7, y between 45-75
    BLACK_GOAL_X = 7           # Maximum x-coordinate for left goal
    BLACK_GOAL_Y = (45, 75)    # Y-coordinate range (min, max)
    
    # White Team Goal (Right Side of Field)  
    # Zone: x ≥ 212, y between 50-85
    WHITE_GOAL_X = 212         # Minimum x-coordinate for right goal
    WHITE_GOAL_Y = (50, 85)    # Y-coordinate range (buffered for reliability)
    
    # Trajectory detection threshold
    TRAJECTORY_BUFFER = 20     # Pixels from goal to activate trajectory check
    MIN_VELOCITY = 2           # Minimum horizontal velocity (pixels) for trajectory
    
    # ===========================================
    
    # METHOD 1: DIRECT DETECTION (Ball Visible in Goal)
    if curr_pos is not None:
        cx, cy = curr_pos
        
        # Check if ball is in Black Goal (left side)
        if cx <= BLACK_GOAL_X and BLACK_GOAL_Y[0] <= cy <= BLACK_GOAL_Y[1]:
            return "Black TEAM2", True
        
        # Check if ball is in White Goal (right side)
        if cx >= WHITE_GOAL_X and WHITE_GOAL_Y[0] <= cy <= WHITE_GOAL_Y[1]:
            return "White TEAM1", True
    
    # METHOD 2: TRAJECTORY DETECTION (Ball Disappeared Near Goal)
    # Handles cases where ball is occluded or moves too fast to detect in goal
    elif curr_pos is None and len(pos_history) == 2:
        # Get last two known positions before ball disappeared
        (x1, y1) = pos_history[0]  # Earlier position
        (x2, y2) = pos_history[1]  # Last known position
        
        # Calculate horizontal velocity (direction and magnitude)
        dx = x2 - x1
        
        # Trajectory toward Black Goal (moving left)
        if (dx < -MIN_VELOCITY and 
            x2 < (BLACK_GOAL_X + TRAJECTORY_BUFFER) and 
            BLACK_GOAL_Y[0] <= y2 <= BLACK_GOAL_Y[1]):
            return "Black TEAM2", True
        
        # Trajectory toward White Goal (moving right)
        if (dx > MIN_VELOCITY and 
            x2 > (WHITE_GOAL_X - TRAJECTORY_BUFFER) and 
            WHITE_GOAL_Y[0] <= y2 <= WHITE_GOAL_Y[1]):
            return "White TEAM1", True
    
    # No goal detected
    return None, False
