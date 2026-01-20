import math
from collections import deque
from typing import Optional, Tuple, Dict
import numpy as np

def detect_bounce(
    current_x: int,
    current_y: int,
    field_width: int,
    field_height: int,
    state: Dict,
    velocity_threshold: float = 15.0,  # Reduced from 25
    angle_threshold: float = 45.0,     # Reduced from 50
    boundary_margin: int = 25,
    min_frames_between: int = 6,       # Increased from 4
    min_frames_boundary: int = 3,      # Increased from 0
    history_size: int = 15,            # Increased from 12
    min_movement_threshold: float = 2.0,  # NEW: minimum movement to consider
    noise_filter_size: int = 3         # NEW: smoothing window
) -> Optional[Tuple[int, int]]:
    """
    Enhanced bounce detection with noise filtering and better static detection
    """
    
    # ---- 1. Reject garbage coordinates immediately ----
    if not (0 <= current_x <= field_width and 0 <= current_y <= field_height):
        return None

    # ---- 2. Initialise state on first call ----
    if 'position_history' not in state:
        state['position_history'] = deque(maxlen=history_size)
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = None
        state['movement_history'] = deque(maxlen=10)  # NEW: track movement patterns
        state['filtered_positions'] = deque(maxlen=noise_filter_size)  # NEW: smoothing

    # ---- 3. Position smoothing to reduce noise ----
    state['filtered_positions'].append((current_x, current_y))
    
    # Simple moving average for noise reduction
    if len(state['filtered_positions']) >= noise_filter_size:
        smoothed_x = int(np.mean([pos[0] for pos in state['filtered_positions']]))
        smoothed_y = int(np.mean([pos[1] for pos in state['filtered_positions']]))
    else:
        smoothed_x, smoothed_y = current_x, current_y

    # ---- 4. Book-keeping with smoothed positions ----
    state['position_history'].append((smoothed_x, smoothed_y))
    state['frames_since_bounce'] += 1

    # Track recent movement for static detection
    if len(state['position_history']) >= 2:
        prev_x, prev_y = state['position_history'][-2]
        movement = math.hypot(smoothed_x - prev_x, smoothed_y - prev_y)
        state['movement_history'].append(movement)

    # ---- 5. Early exit for static ball ----
    if len(state['movement_history']) >= 3:
        recent_movements = list(state['movement_history'])[-3:]
        avg_movement = np.mean(recent_movements)
        
        # If ball is barely moving, ignore bounce detection
        if avg_movement < min_movement_threshold:
            return None

    if len(state['position_history']) < 4:  # Increased minimum history
        return None

    # ---- 6. Enhanced lock-out mechanism ----
    near_boundary = (
        smoothed_x <= boundary_margin or
        smoothed_x >= field_width - boundary_margin or
        smoothed_y <= boundary_margin or
        smoothed_y >= field_height - boundary_margin
    )
    in_corner = (
        (smoothed_x <= boundary_margin or smoothed_x >= field_width - boundary_margin) and
        (smoothed_y <= boundary_margin or smoothed_y >= field_height - boundary_margin)
    )

    # Dynamic lockout based on recent activity
    lockout = min_frames_boundary if near_boundary else min_frames_between
    if state['frames_since_bounce'] < lockout:
        return None

    # ---- 7. Enhanced velocity & angle calculations ----
    history = list(state['position_history'])
    velocities = []
    for i in range(len(history) - 1):
        dx = history[i + 1][0] - history[i][0]
        dy = history[i + 1][1] - history[i][1]
        vel_mag = math.hypot(dx, dy)
        velocities.append((dx, dy, vel_mag))

    if len(velocities) < 3:
        return None

    # Use longer window for more reliable velocity calculation
    recent_velocities = velocities[-4:] if len(velocities) >= 4 else velocities
    velocity_changes = []
    for i in range(len(recent_velocities) - 1):
        change = abs(recent_velocities[i + 1][2] - recent_velocities[i][2])
        velocity_changes.append(change)
    
    max_velocity_change = max(velocity_changes) if velocity_changes else 0.0

    # ---- 8. Improved angle calculation ----
    # Use multiple vector pairs for more robust angle detection
    angle_changes = []
    for i in range(max(1, len(recent_velocities) - 2)):
        dx1, dy1, v1 = recent_velocities[i]
        dx2, dy2, v2 = recent_velocities[i + 1]
        
        if v1 > 0.5 and v2 > 0.5:  # Increased minimum velocity threshold
            dot = dx1 * dx2 + dy1 * dy2
            cos_angle = max(-1.0, min(1.0, dot / (v1 * v2 + 1e-6)))  # Add small epsilon
            angle_change = math.acos(cos_angle)
            angle_changes.append(angle_change)
    
    avg_angle_change = np.mean(angle_changes) if angle_changes else 0.0
    max_angle_change = max(angle_changes) if angle_changes else 0.0

    # ---- 9. Adaptive thresholds based on ball speed ----
    # Adjust thresholds based on recent average velocity
    recent_avg_velocity = np.mean([v[2] for v in recent_velocities])
    
    # Dynamic velocity threshold
    if recent_avg_velocity < 10:  # Slow moving ball
        v_thresh = velocity_threshold * 0.7
    elif recent_avg_velocity > 50:  # Fast moving ball
        v_thresh = velocity_threshold * 1.3
    else:
        v_thresh = velocity_threshold

    a_thresh = math.radians(angle_threshold)

    # Enhanced corner detection
    if in_corner:
        v_thresh *= 0.4  # More sensitive in corners
        a_thresh *= 0.5

    # ---- 10. Enhanced bounce detection logic ----
    bounce_detected = False
    
    # Primary detection: significant velocity change
    if max_velocity_change >= v_thresh:
        bounce_detected = True
    
    # Secondary detection: moderate velocity change with clear direction change
    elif (max_velocity_change >= v_thresh * 0.6 and 
          max_angle_change >= a_thresh * 0.8):
        bounce_detected = True
    
    # Boundary detection: lower thresholds near walls
    elif (near_boundary and 
          (max_velocity_change >= v_thresh * 0.5 or 
           max_angle_change >= a_thresh * 0.6)):
        bounce_detected = True

    # Additional check: look for velocity pattern typical of bounces
    if not bounce_detected and len(velocity_changes) >= 2:
        # Check for sudden deceleration followed by acceleration
        if (velocity_changes[-1] > v_thresh * 0.4 and 
            velocity_changes[-2] > v_thresh * 0.3):
            bounce_detected = True

    if bounce_detected:
        state['frames_since_bounce'] = 0
        state['last_bounce_coords'] = (smoothed_x, smoothed_y)
        return (smoothed_x, smoothed_y)

    return None


def reset_bounce_detector(state: Dict) -> None:
    """
    Reset the bounce detector state with enhanced cleanup
    """
    state.clear()


# NEW: Additional utility function for debugging
def get_bounce_metrics(state: Dict) -> Dict:
    """
    Get diagnostic information about bounce detection
    Useful for tuning parameters
    """
    if 'movement_history' not in state:
        return {}
    
    return {
        'avg_movement': np.mean(list(state['movement_history'])) if state['movement_history'] else 0,
        'frames_since_bounce': state.get('frames_since_bounce', 0),
        'position_history_length': len(state.get('position_history', [])),
        'last_bounce': state.get('last_bounce_coords', None)
    }




