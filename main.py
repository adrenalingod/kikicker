"""
Foosball Tracking System - Main Application

Real-time foosball game tracking system using Raspberry Pi Camera and BLE advertising.
Tracks ball position, speed, possession, bounces, and goals with live debug visualization.

Features:
- 120 FPS ball detection and tracking
- Bounce detection with speed calculation
- Team possession tracking
- Goal detection with trajectory analysis
- BLE advertising of game state
- Multi-window debug visualization

Hardware Requirements:
- Raspberry Pi (3/4/5) with Camera Module
- Foosball table with consistent lighting

Usage:
    python main.py              # Run without debug windows
    python main.py --debug      # Run with live visualization

Author: [Your Name]
License: [Your License]
"""

# -------------------------------
# Standard libraries
# -------------------------------
import time
import argparse

# -------------------------------
# Hardware / Vision libraries
# -------------------------------
import cv2
from picamera2 import Picamera2

# -------------------------------
# Project libraries
# -------------------------------
from kicker_vision import find_playfield_roi, detect_ball, quantize_to_bits
from bla_glib import BLAAdvertiserGLib
from bla_payload import BLA_Payload, Bounce
from bounce import detect_bounce
from speed import get_speed_ms
from ballPosession import get_ball_possession
from goalCheck import check_goal_scored, draw_goal_debug

# -------------------------------
# Argument parser
# -------------------------------
parser = argparse.ArgumentParser(description='Foosball Kicker System')
parser.add_argument('--debug', action='store_true', help='Enable debug visualization windows')
args = parser.parse_args()
debug = args.debug

# -------------------------------
# Camera configuration
# -------------------------------
FPS = 120  # Frames per second for tracking
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    raw=picam2.sensor_modes[0],
    main={"size": (353, 200)},  # Resolution optimized for 120 FPS
    controls={"FrameRate": FPS}
)
picam2.configure(config)
picam2.start()
time.sleep(1.0)  # Allow camera to stabilize

# -------------------------------
# Initial frame & ROI detection
# -------------------------------
# Capture initial frame to detect playfield boundaries
initial_frame_rgb = picam2.capture_array()
initial_frame_bgr = cv2.cvtColor(initial_frame_rgb, cv2.COLOR_RGB2BGR)
cv2.imwrite("initial_frame.png", initial_frame_bgr)

# Detect playfield region of interest (ROI)
img_rgb = cv2.cvtColor(initial_frame_bgr, cv2.COLOR_BGR2RGB)
field_roi = find_playfield_roi(img_rgb, debug=debug)

if field_roi is None:
    # Use full frame if ROI detection fails
    fx, fy = 0, 0
    fw, fh = initial_frame_rgb.shape[1], initial_frame_rgb.shape[0]
else:
    fx, fy, fw, fh = field_roi

print(f"Playfield ROI: x={fx}, y={fy}, width={fw}, height={fh}")

# -------------------------------
# BLE advertiser initialization
# -------------------------------
# Initialize BLE advertiser for broadcasting game state
adv = BLAAdvertiserGLib(interval=0.005)  # 5ms advertising interval
adv.start()

payload = BLA_Payload()  # Payload structure for game data

# -------------------------------
# GAME STATE VARIABLES
# -------------------------------
# Bounce detection state
bounce_state = {}

# Goal detection state
goal_latched = False  # Prevents duplicate goal detection
pos_history = []      # Recent ball positions for trajectory analysis

# -------------------------------
# SPEED TRACKING STATE
# -------------------------------
last_bx = None        # Last bounce x-coordinate
last_by = None        # Last bounce y-coordinate
last_bt = None        # Last bounce timestamp
speed_debug = None    # Current speed value for display
speed_dt = None       # Time difference between bounces
speed_prev = None     # Previous bounce position (for visualization)
speed_curr = None     # Current bounce position (for visualization)

# -------------------------------
# BALL POSSESSION STATE
# -------------------------------
pos_team = None       # Current team with possession ("WHITE" or "BLACK")
pos_point = None      # Bounce coordinates where possession was determined
possession_debug = {"pos": None, "team_id": None}  # Debug visualization data

# -------------------------------
# FRAME COUNTER
# -------------------------------
frame_count = 0       # Frames processed per second (for FPS calculation)
total_frame_count = 0 # Total frames since start (for payload)

try:
    start_time = time.time()

    # ========================================
    # MAIN PROCESSING LOOP
    # ========================================
    while True:
        # Capture current frame
        frame_rgb = picam2.capture_array()
        display_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        total_frame_count += 1

        # -------------------------------
        # Ball detection
        # -------------------------------
        result = detect_ball(frame_rgb, fx, fy, fw, fh, debug=debug)
        curr_pos = None

        if result is not None:
            # Ball detected - extract coordinates
            cx, cy, x, y, w, h = result
            
            # Convert to field-relative coordinates
            field_x = cx - fx
            field_y = cy - fy
            curr_pos = (field_x, field_y)

            # Debug output
            if debug:
                print(f"Ball: {field_x}, {field_y}")

            # Maintain position history (last 2 positions for trajectory analysis)
            pos_history.append(curr_pos)
            if len(pos_history) > 2:
                pos_history.pop(0)

            # -------------------------------
            # Bounce detection
            # -------------------------------
            bounce_coords = detect_bounce(
                current_x=field_x,
                current_y=field_y,
                field_width=fw,
                field_height=fh,
                state=bounce_state
            )

            if bounce_coords:
                bx, by = bounce_coords
                curr_bt = time.time()
                print(f"💥 BOUNCE: ({bx}, {by})")

                # ========== INITIALIZE BOUNCE DATA ==========
                # Variables to store all bounce-related data before adding to payload
                bounce_x_quantized = None
                bounce_y_quantized = None
                bounce_speed = 0.0  # Default speed (m/s)
                bounce_possession = 0  # Team ID: 0 = WHITE, 1 = BLACK
                # ============================================

                # ========== QUANTIZE BOUNCE COORDINATES ==========
                # Convert bounce coordinates to 7-bit (x) and 6-bit (y) for BLE transmission
                bounce_x_quantized, bounce_y_quantized = quantize_to_bits(bx, by, fw, fh)
                print(f"📍 Quantized: x={bounce_x_quantized} (7-bit), y={bounce_y_quantized} (6-bit)")
                # =================================================

                # ========== SPEED CALCULATION ==========
                if last_bx is not None:
                    # Calculate speed between consecutive bounces
                    speed_ms = get_speed_ms(
                        last_bx, last_by, last_bt,
                        bx, by, curr_bt
                    )
                    
                    # Round to 1 decimal place
                    bounce_speed = round(speed_ms, 1)
                    speed_debug = bounce_speed
                    print(f"⚡ Speed: {bounce_speed} m/s")
                    
                    # Store debug visualization data
                    speed_dt = curr_bt - last_bt
                    speed_prev = (last_bx, last_by)
                    speed_curr = (bx, by)
                
                # Update last bounce data for next calculation
                last_bx, last_by, last_bt = bx, by, curr_bt
                # ========================================

                # ========== BALL POSSESSION ==========
                # Determine which team hit the ball
                pos_team = get_ball_possession(bx, by)
                print(f"🏁 Possession: {pos_team}")
                
                # Convert team name to numeric ID for payload
                # WHITE = 0, BLACK = 1
                if pos_team == "WHITE":
                    bounce_possession = 0  # White team = 0
                elif pos_team == "BLACK":
                    bounce_possession = 1  # Black team = 1
                
                # Store for debug visualization
                pos_point = (bx, by)
                possession_debug["pos"] = pos_point
                possession_debug["team_id"] = pos_team
                # =====================================

                # ========== ADD BOUNCE TO PAYLOAD ==========
                # Create Bounce object with all calculated data and add to payload
                bounce_obj = Bounce(
                    bounce_x_quantized,      # 7-bit quantized x-coordinate
                    bounce_y_quantized,      # 6-bit quantized y-coordinate
                    bounce_speed,            # Speed in m/s (1 decimal)
                    bounce_possession,       # Team ID (0=WHITE, 1=BLACK)
                    total_frame_count        # Current frame number
                )
                payload.add_bounce(bounce_obj)
                print(f"📦 Bounce added to payload: x={bounce_x_quantized}, y={bounce_y_quantized}, "
                      f"speed={bounce_speed}, possession={bounce_possession}, frame={total_frame_count}")
                # ===========================================

        # -------------------------------
        # Goal detection
        # -------------------------------
        goal, goal_latched = check_goal_scored(
            curr_pos=curr_pos,
            pos_history=pos_history,
            goal_latched=goal_latched
        )

        if goal:
            print(f"⚽ GOAL!!! {goal} scored!")
            
            # ========== UPDATE GOAL PAYLOAD ==========
            if goal == "White TEAM1":
                payload.team1_scored()  # White team scored
                print("📊 White team (0) goal counted")
            elif goal == "Black TEAM2":
                payload.team2_scored()  # Black team scored
                print("📊 Black team (1) goal counted")
            # =========================================
            
            # Pause briefly to celebrate the goal
            time.sleep(3.0)
            
            # Reset goal detection for next round
            goal_latched = False
            pos_history.clear()

        # ========== BROADCAST PAYLOAD VIA BLE ==========
        # Advertise current game state (uncomment when ready)
        # adv.advertise(payload.to_bytes())
        # ===============================================

        # ============================================================
        # DEBUG VISUALIZATION
        # ============================================================
        if debug:
            window_name = 'Kicker Live'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.namedWindow("Goal Detection Debug", cv2.WINDOW_NORMAL)

            # Draw playfield ROI
            cv2.rectangle(display_frame, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)

            # Draw ball detection box
            if result is not None:
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    display_frame,
                    f"{field_x},{field_y}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            # Goal detection debug window
            goal_debug_frame = display_frame.copy()
            draw_goal_debug(
                goal_debug_frame,
                fx, fy, fw, fh,
                curr_pos,
                goal,
                goal_latched
            )

            cv2.imshow(window_name, display_frame)
            cv2.imshow("Goal Detection Debug", goal_debug_frame)

            # ---------- SPEED DEBUG WINDOW ----------
            speed_frame = display_frame.copy()
            if speed_prev and speed_curr:
                # Convert field coordinates back to frame coordinates
                px, py = speed_prev
                cx, cy = speed_curr
                px += fx; py += fy
                cx += fx; cy += fy

                # Draw bounce trajectory
                cv2.circle(speed_frame, (px, py), 6, (0, 0, 255), -1)  # Previous (red)
                cv2.circle(speed_frame, (cx, cy), 6, (0, 255, 0), -1)  # Current (green)
                cv2.line(speed_frame, (px, py), (cx, cy), (255, 0, 0), 2)  # Trajectory (blue)

                # Display speed and time delta
                cv2.putText(
                    speed_frame,
                    f"Speed: {speed_debug:.1f} m/s",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2
                )
                cv2.putText(
                    speed_frame,
                    f"dt: {speed_dt:.3f} s",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (200, 200, 200),
                    2
                )

            cv2.imshow("Speed Debug", speed_frame)

            # ---------- BALL POSSESSION DEBUG WINDOW ----------
            pos_frame = display_frame.copy()
            if possession_debug["pos"]:
                # Convert field coordinates to frame coordinates
                px, py = possession_debug["pos"]
                px += fx; py += fy
                team = possession_debug["team_id"]  # "WHITE" or "BLACK"

                # Color-code by team
                if team == "WHITE":
                    color = (255, 255, 255)
                    label = "WHITE HIT (0)"
                else:
                    color = (0, 0, 0)
                    label = "BLACK HIT (1)"

                # Draw possession indicator
                cv2.circle(pos_frame, (px, py), 8, color, -1)
                cv2.putText(
                    pos_frame,
                    label,
                    (px + 10, py - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

            cv2.imshow("Ball Possession Debug", pos_frame)

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # -------------------------------
        # FPS counter (prints every second)
        # -------------------------------
        frame_count += 1
        if time.time() - start_time >= 1.0:
            print(f"📊 FPS: {frame_count} | Total Frames: {total_frame_count}")
            frame_count = 0
            start_time = time.time()

except KeyboardInterrupt:
    print("\n⚠️  Interrupted by user")

finally:
    # Clean shutdown
    print("🛑 Shutting down...")
    adv.stop()
    picam2.stop()
    if debug:
        cv2.destroyAllWindows()
    print("✅ Cleanup complete")
