"""
Bounce Detection Module for Foosball Ball Tracking
Implements velocity-based bounce detection with coordinate tracking
"""

import math
from collections import deque
from typing import Optional, Tuple, Dict

def detect_bounce(
    current_x: int,
    current_y: int,
    field_width: int,
    field_height: int,
    state: Dict,
    velocity_threshold: float = 25.0,
    angle_threshold: float = 50.0,
    boundary_margin: int = 25,
    min_frames_between: int = 4,
    history_size: int = 6
) -> Optional[Tuple[int, int]]:
    """
    Detect ball bounces based on velocity changes and trajectory analysis.
    
    A bounce is detected when:
    1. Significant velocity magnitude change occurs (sudden deceleration/acceleration)
    2. Direction change exceeds threshold (ball changes trajectory)
    3. Ball is near playfield boundaries (wall/rod collision)
    
    Args:
        current_x: Current ball X coordinate (relative to field)
        current_y: Current ball Y coordinate (relative to field)
        field_width: Width of the playfield
        field_height: Height of the playfield
        state: Dictionary to maintain state between calls (pass same dict each frame)
        velocity_threshold: Min velocity change to consider bounce (pixels/frame)
        angle_threshold: Min direction change angle in degrees
        boundary_margin: Distance from boundary to consider for bounce (pixels)
        min_frames_between: Minimum frames between consecutive bounces
        history_size: Number of recent positions to track
    
    Returns:
        Tuple (x, y) of bounce coordinates if bounce detected, None otherwise
        
    Usage:
        bounce_state = {}  # Initialize once before loop
        
        while True:
            # ... get ball position ...
            bounce_coords = detect_bounce(field_x, field_y, fw, fh, bounce_state)
            if bounce_coords is not None:
                bx, by = bounce_coords
                print(f"Bounce detected at ({bx}, {by})")
    """
    
    # Initialize state on first call
    if 'position_history' not in state:
        state['position_history'] = deque(maxlen=history_size)
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = None
    
    # Add current position to history
    state['position_history'].append((current_x, current_y))
    state['frames_since_bounce'] += 1
    
    # Need at least 3 positions to detect bounce
    if len(state['position_history']) < 3:
        return None
    
    # Don't detect bounce too soon after previous one
    if state['frames_since_bounce'] < min_frames_between:
        return None
    
    history = list(state['position_history'])
    
    # Calculate velocities between consecutive positions
    velocities = []
    for i in range(len(history) - 1):
        dx = history[i + 1][0] - history[i][0]
        dy = history[i + 1][1] - history[i][1]
        velocity = math.sqrt(dx * dx + dy * dy)
        velocities.append((dx, dy, velocity))
    
    # Need at least 2 velocity measurements
    if len(velocities) < 2:
        return None
    
    # Check for velocity change (bounce signature: sudden deceleration or acceleration)
    recent_velocities = velocities[-3:] if len(velocities) >= 3 else velocities
    velocity_changes = []
    
    for i in range(len(recent_velocities) - 1):
        v1 = recent_velocities[i][2]
        v2 = recent_velocities[i + 1][2]
        velocity_change = abs(v2 - v1)
        velocity_changes.append(velocity_change)
    
    max_velocity_change = max(velocity_changes) if velocity_changes else 0
    
    # Check for direction change
    if len(velocities) >= 2:
        # Compare velocity directions (last two velocity vectors)
        dx1, dy1, v1 = velocities[-2]
        dx2, dy2, v2 = velocities[-1]
        
        # Calculate angle between velocity vectors
        if v1 > 0 and v2 > 0:
            # Dot product and magnitudes
            dot_product = dx1 * dx2 + dy1 * dy2
            cos_angle = dot_product / (v1 * v2)
            # Clamp to [-1, 1] to handle numerical errors
            cos_angle = max(-1.0, min(1.0, cos_angle))
            angle_change = math.acos(cos_angle)
        else:
            angle_change = 0
    else:
        angle_change = 0
    
    # Check if ball is near boundary
    near_boundary = (
        current_x <= boundary_margin or 
        current_x >= field_width - boundary_margin or
        current_y <= boundary_margin or 
        current_y >= field_height - boundary_margin
    )
    
    # Bounce detection logic
    bounce_detected = False
    
    # Primary detection: significant velocity change
    if max_velocity_change >= velocity_threshold:
        bounce_detected = True
    
    # Secondary detection: significant direction change with moderate velocity change
    elif angle_change >= math.radians(angle_threshold) and max_velocity_change >= velocity_threshold * 0.5:
        bounce_detected = True
    
    # Tertiary detection: near boundary with any significant change
    elif near_boundary and (max_velocity_change >= velocity_threshold * 0.6 or 
                            angle_change >= math.radians(angle_threshold * 0.7)):
        bounce_detected = True
    
    # If bounce detected, return coordinates
    if bounce_detected:
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = (current_x, current_y)
        return (current_x, current_y)
    
    return None


def reset_bounce_detector(state: Dict) -> None:
    """
    Reset the bounce detector state.
    Call this when ball is lost or tracking is interrupted.
    
    Args:
        state: The state dictionary used in detect_bounce
    """
    state.clear()
