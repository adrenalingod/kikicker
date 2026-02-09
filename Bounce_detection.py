"""
Bounce Detection Module for Foosball Ball Tracking
Implements precise velocity-based bounce detection with strict duplicate prevention
Pure function-based implementation using state dictionary
"""

import math
from collections import deque
from typing import Optional, Tuple, Dict, List


# ============================================================================
# Helper Functions
# ============================================================================

def _calculate_velocity(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> Tuple[float, float, float]:
    """
    Calculate velocity vector between two positions.
    
    Args:
        pos1: Previous position (x, y)
        pos2: Current position (x, y)
    
    Returns:
        Tuple of (dx, dy, magnitude)
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    magnitude = math.hypot(dx, dy)
    return dx, dy, magnitude


def _calculate_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """
    Calculate Euclidean distance between two positions.
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
    
    Returns:
        Distance in pixels
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.hypot(dx, dy)


def _is_near_boundary(
    x: int, 
    y: int, 
    field_width: int, 
    field_height: int, 
    boundary_margin: int
) -> Tuple[bool, bool]:
    """
    Check if position is near boundary or corner.
    
    Args:
        x: X coordinate
        y: Y coordinate
        field_width: Width of playfield
        field_height: Height of playfield
        boundary_margin: Distance from edge to consider as boundary
    
    Returns:
        Tuple of (near_boundary, in_corner)
    """
    near_left = x <= boundary_margin
    near_right = x >= field_width - boundary_margin
    near_top = y <= boundary_margin
    near_bottom = y >= field_height - boundary_margin
    
    near_boundary = near_left or near_right or near_top or near_bottom
    in_corner = (near_left or near_right) and (near_top or near_bottom)
    
    return near_boundary, in_corner


def _calculate_angle_change(
    vel1: Tuple[float, float, float], 
    vel2: Tuple[float, float, float]
) -> float:
    """
    Calculate angle change between two velocity vectors.
    
    Args:
        vel1: First velocity (dx, dy, magnitude)
        vel2: Second velocity (dx, dy, magnitude)
    
    Returns:
        Angle change in radians
    """
    dx1, dy1, mag1 = vel1
    dx2, dy2, mag2 = vel2
    
    if mag1 < 0.1 or mag2 < 0.1:
        return 0.0
    
    # Dot product for angle calculation
    dot = dx1 * dx2 + dy1 * dy2
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    angle = math.acos(cos_angle)
    
    return angle


def _find_precise_bounce_location(
    position_history: deque, 
    velocity_history: deque
) -> Tuple[int, int]:
    """
    Determine the most likely bounce location from recent history.
    Uses the position where velocity change was maximum.
    
    Args:
        position_history: Deque of recent positions
        velocity_history: Deque of recent velocities
    
    Returns:
        Coordinates (x, y) of bounce location
    """
    if len(velocity_history) < 2:
        return position_history[-1]
    
    # Find position with maximum velocity change
    max_change_idx = 0
    max_change = 0.0
    
    vel_list = list(velocity_history)
    for i in range(len(vel_list) - 1):
        change = abs(vel_list[i + 1][2] - vel_list[i][2])
        if change > max_change:
            max_change = change
            max_change_idx = i + 1
    
    # Return position corresponding to max velocity change
    # Look back in position history to find the exact frame
    bounce_idx = min(max_change_idx, len(position_history) - 1)
    return position_history[bounce_idx]


# ============================================================================
# Main Bounce Detection Function
# ============================================================================

def detect_bounce(
    current_x: int,
    current_y: int,
    field_width: int,
    field_height: int,
    state: Dict,
    velocity_threshold: float = 25.0,
    angle_threshold: float = 50.0,
    boundary_margin: int = 25,
    min_frames_between: int = 8,
    min_frames_boundary: int = 4,
    history_size: int = 15,
    min_bounce_distance: int = 15
) -> Optional[Tuple[int, int]]:
    """
    Detect ball bounces based on velocity changes and trajectory analysis.
    
    This function maintains state across calls using the provided state dictionary.
    It tracks:
    - Previous position: Ball location in last frame
    - Current position: Ball location in this frame  
    - Bounce position: Exact location where bounce occurred
    - Complete position history for trajectory analysis
    
    A bounce is detected when:
    1. Significant velocity magnitude change occurs (sudden deceleration/acceleration)
    2. Direction change exceeds threshold (ball changes trajectory)
    3. Ball is near playfield boundaries (wall/rod collision)
    
    Duplicate Prevention:
    - Bounces at the same location (within min_bounce_distance) are ignored
    - Minimum frame lockout prevents rapid re-detection
    - Only reports unique bounce locations
    
    Args:
        current_x: Current ball X coordinate (relative to field, MUST be inside [0…field_width])
        current_y: Current ball Y coordinate (relative to field, MUST be inside [0…field_height])
        field_width: Width of the playfield
        field_height: Height of the playfield
        state: Dictionary to maintain state between calls (pass same dict each frame)
        velocity_threshold: Min velocity change to consider bounce (pixels/frame)
        angle_threshold: Min direction change angle in degrees
        boundary_margin: Distance from boundary to consider for bounce (pixels)
        min_frames_between: Minimum frames between consecutive bounces (inside field, default: 8)
        min_frames_boundary: Minimum frames between consecutive bounces (at boundary, default: 4)
        history_size: Number of recent positions to track
        min_bounce_distance: Minimum distance between bounces to prevent duplicates (pixels, default: 15)
        
    Returns:
        Tuple (x, y) of precise bounce coordinates if detected, None otherwise
        Returns None if bounce is a duplicate (same location as last bounce)
        
    State Dictionary Contents:
        - position_history: Deque of recent (x, y) positions
        - velocity_history: Deque of recent (dx, dy, magnitude) velocities
        - previous_position: Last frame's (x, y) position
        - frames_since_bounce: Counter for lockout period
        - last_bounce_coords: Last detected bounce (x, y)
        - bounce_history: List of all detected bounces with metadata
    """
    
    # ---- 1. Validate coordinates ----
    if not (0 <= current_x <= field_width and 0 <= current_y <= field_height):
        return None
    
    # ---- 2. Initialize state on first call ----
    if 'position_history' not in state:
        state['position_history'] = deque(maxlen=history_size)
        state['velocity_history'] = deque(maxlen=history_size - 1)
        state['previous_position'] = None
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = None
        state['bounce_history'] = []
    
    current_pos = (current_x, current_y)
    
    # ---- 3. Update position and velocity history ----
    if state['previous_position'] is not None:
        velocity = _calculate_velocity(state['previous_position'], current_pos)
        state['velocity_history'].append(velocity)
    
    state['position_history'].append(current_pos)
    state['previous_position'] = current_pos
    state['frames_since_bounce'] += 1
    
    # ---- 4. Need minimum history ----
    if len(state['position_history']) < 3 or len(state['velocity_history']) < 2:
        return None
    
    # ---- 5. Check lockout period (adaptive based on location) ----
    near_boundary, in_corner = _is_near_boundary(
        current_x, current_y, field_width, field_height, boundary_margin
    )
    lockout = min_frames_boundary if near_boundary else min_frames_between
    
    if state['frames_since_bounce'] < lockout:
        return None
    
    # ---- 6. Analyze velocity changes ----
    vel_list = list(state['velocity_history'])
    
    # Calculate recent velocity changes
    recent_window = min(4, len(vel_list))
    recent_vels = vel_list[-recent_window:]
    
    velocity_changes = [
        abs(recent_vels[i + 1][2] - recent_vels[i][2])
        for i in range(len(recent_vels) - 1)
    ]
    
    max_velocity_change = max(velocity_changes) if velocity_changes else 0.0
    
    # ---- 7. Calculate direction change ----
    angle_change = _calculate_angle_change(vel_list[-2], vel_list[-1])
    
    # ---- 8. Adaptive thresholds based on location ----
    v_thresh = velocity_threshold
    a_thresh = math.radians(angle_threshold)
    
    # Relax thresholds for corners and boundaries
    if in_corner:
        v_thresh *= 0.5
        a_thresh *= 0.6
    elif near_boundary:
        v_thresh *= 0.7
        a_thresh *= 0.75
    
    # ---- 9. Bounce detection logic ----
    bounce_detected = False
    bounce_type = None
    
    # Strong velocity change
    if max_velocity_change >= v_thresh:
        bounce_detected = True
        bounce_type = "velocity_change"
    
    # Significant direction change with moderate velocity change
    elif angle_change >= a_thresh and max_velocity_change >= v_thresh * 0.5:
        bounce_detected = True
        bounce_type = "direction_change"
    
    # Boundary bounce with relaxed thresholds
    elif near_boundary:
        if max_velocity_change >= v_thresh * 0.6 or angle_change >= a_thresh * 0.7:
            bounce_detected = True
            bounce_type = "boundary_bounce"
    
    # Combined indicator: sudden deceleration + direction change
    elif max_velocity_change >= v_thresh * 0.6 and angle_change >= a_thresh * 0.6:
        bounce_detected = True
        bounce_type = "combined"
    
    # ---- 10. Register bounce if detected ----
    if bounce_detected:
        # Find precise bounce location (not just current position)
        bounce_coords = _find_precise_bounce_location(
            state['position_history'], 
            state['velocity_history']
        )
        
        # ---- 11. DUPLICATE PREVENTION CHECK ----
        # Check if this bounce is too close to the last detected bounce
        if state['last_bounce_coords'] is not None:
            distance_from_last = _calculate_distance(state['last_bounce_coords'], bounce_coords)
            
            # If bounce is within min_bounce_distance of last bounce, it's a duplicate
            if distance_from_last < min_bounce_distance:
                # This is a duplicate - do NOT report it
                # But DO reset the lockout timer to prevent continuous false detections
                state['frames_since_bounce'] = 0
                return None
        
        # ---- 12. This is a valid, unique bounce ----
        # Update state
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = bounce_coords
        
        # Store in history for analysis
        bounce_info = {
            'coords': bounce_coords,
            'type': bounce_type,
            'velocity_change': max_velocity_change,
            'angle_change': math.degrees(angle_change),
            'near_boundary': near_boundary,
            'in_corner': in_corner
        }
        state['bounce_history'].append(bounce_info)
        
        return bounce_coords
    
    return None


# ============================================================================
# Utility Functions
# ============================================================================

def reset_bounce_detector(state: Dict) -> None:
    """
    Reset the bounce detector state.
    Call this when ball is lost or tracking is interrupted.
    
    Args:
        state: State dictionary used in detect_bounce()
    """
    state.clear()


def get_bounce_history(state: Dict) -> List[Dict]:
    """
    Get history of all detected bounces with metadata.
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        List of bounce information dictionaries containing:
        - coords: (x, y) bounce location
        - type: bounce detection type (velocity_change, direction_change, boundary_bounce, combined)
        - velocity_change: magnitude of velocity change (pixels/frame)
        - angle_change: direction change in degrees
        - near_boundary: whether bounce was near boundary
        - in_corner: whether bounce was in corner
    """
    return state.get('bounce_history', []).copy()


def get_position_history(state: Dict) -> List[Tuple[int, int]]:
    """
    Get recent position history.
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        List of (x, y) positions in chronological order
    """
    history = state.get('position_history', deque())
    return list(history)


def get_previous_position(state: Dict) -> Optional[Tuple[int, int]]:
    """
    Get the previous ball position (last frame).
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        Previous position (x, y) or None if not available
    """
    return state.get('previous_position', None)


def get_last_bounce_coords(state: Dict) -> Optional[Tuple[int, int]]:
    """
    Get the coordinates of the last detected bounce.
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        Last bounce position (x, y) or None if no bounce detected yet
    """
    return state.get('last_bounce_coords', None)


def get_velocity_history(state: Dict) -> List[Tuple[float, float, float]]:
    """
    Get recent velocity history.
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        List of (dx, dy, magnitude) velocity vectors in chronological order
    """
    history = state.get('velocity_history', deque())
    return list(history)


def get_current_velocity(state: Dict) -> Optional[Tuple[float, float, float]]:
    """
    Get the most recent velocity vector.
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        Current velocity (dx, dy, magnitude) or None if not available
    """
    velocity_history = state.get('velocity_history', deque())
    if len(velocity_history) > 0:
        return velocity_history[-1]
    return None


def get_ball_speed(state: Dict) -> Optional[float]:
    """
    Get current ball speed (velocity magnitude).
    
    Args:
        state: State dictionary used in detect_bounce()
    
    Returns:
        Speed in pixels/frame or None if not available
    """
    vel = get_current_velocity(state)
    if vel is not None:
        return vel[2]  # Return magnitude
    return None
