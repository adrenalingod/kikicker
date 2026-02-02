# libraries
import time
import argparse
import numpy as np

# hardware libraries
from bla_payload import BLA_Payload
import cv2
from picamera2 import Picamera2

# own libraries
from kicker_vision import find_playfield_roi, detect_ball, quantize_to_bits, transform_to_field_coordinates
from bla_glib import BLAAdvertiserGLib
from bla_payload import Bounce
parser = argparse.ArgumentParser(description='Kicker')
parser.add_argument('--debug', action='store_true') 
args = parser.parse_args()
debug = args.debug

# Create picamera2 and configuration
FPS = 120
picam2 = Picamera2()
config = picam2.create_preview_configuration(raw=picam2.sensor_modes[0], main={"size": (384, 216)}, controls={"FrameRate":FPS})
picam2.configure(config)
picam2.start()
time.sleep(1.0)

# Initial frame and ROI
initial_frame_rgb = picam2.capture_array()
field_roi = find_playfield_roi(initial_frame_rgb, debug=debug)
if field_roi is None:
    print("Warning: Could not detect playfield ROI, using full frame")
    # Create a dummy ROI covering the full frame (no rotation)
    h, w = initial_frame_rgb.shape[:2]
    field_roi = {
        'corners': np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype=np.int32),
        'center': (w//2, h//2),
        'angle': 0,
        'width': w,
        'height': h
    }

# Initialize BLA advertiser and Paload
adv = BLAAdvertiserGLib(interval=0.005) 
adv.start()

payload = BLA_Payload()

try:
    start_time = time.time()
    frame_count = 0
    bounces = 0
    while True:

        frame_rgb = picam2.capture_array()

        result = detect_ball(frame_rgb, field_roi, debug=debug)
        if result is not None:
            cx, cy, x, y, w, h = result
            
            # Transform to field-local coordinates
            field_x, field_y = transform_to_field_coordinates(cx, cy, field_roi)
            
            # Quantize using field dimensions
            x_7bit, y_6bit = quantize_to_bits(field_x, field_y, field_roi['width'], field_roi['height'])
            
            # Determine ball possession based on field position (simple heuristic)
            if field_x < field_roi['width'] / 2:
                payload.set_team1_ball_possession()
            else:
                payload.set_team2_ball_possession()
            
            if frame_count == 35 or bounces == 3:
                bounces = 0
                data = payload.to_bytes()
                adv.set_custom_payload(data)
            
            if frame_count % 10 == 0:
                bounces += 1
                payload.add_bounce(Bounce(x_7bit, y_6bit, 13, frame_count % 127))
                # Simulate scoring for testing
                if frame_count % 100 == 0:
                    payload.team1_scored()
                
        if debug:
            window_name = 'Kicker Live'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

            display_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            
            # Draw playfield corners
            corners = field_roi['corners']
            cv2.polylines(display_frame, [corners], True, (0, 0, 255), 2)
            
            # Draw ROI info text
            roi_text = f"ROI: {field_roi['width']}x{field_roi['height']} {field_roi['angle']:+.1f}deg"
            cv2.putText(display_frame, roi_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Draw corner points with numbers
            corner_names = ["TL", "TR", "BR", "BL"]
            for i, corner in enumerate(corners):
                cv2.circle(display_frame, tuple(corner), 6, (255, 0, 0), -1)
                cv2.putText(display_frame, corner_names[i], 
                           (corner[0] + 8, corner[1] - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw center point
            cv2.circle(display_frame, field_roi['center'], 5, (255, 0, 0), -1)
            
            if result is not None:
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, f"{x_7bit},{y_6bit}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow(window_name, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        if time.time() - start_time >= 1.0:
            print(f"FPS: {frame_count}")
            frame_count = 1
            start_time = time.time()
        frame_count += 1

except KeyboardInterrupt:
    pass
finally:
    adv.stop()
    picam2.stop()
    if debug:
        cv2.destroyAllWindows()
