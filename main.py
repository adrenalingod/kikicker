# libraries
import time
import argparse

# hardware libraries
from bla_payload import BLA_Payload
import cv2
from picamera2 import Picamera2

# own libraries
from kicker_vision import find_playfield_roi, detect_ball, quantize_to_bits
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
    fx, fy = 0, 0
    fw, fh = initial_frame_rgb.shape[1], initial_frame_rgb.shape[0]
else:
    fx, fy, fw, fh = field_roi

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

        result = detect_ball(frame_rgb, debug=debug)
        if result is not None:
            cx, cy, x, y, w, h = result
            field_x = cx - fx
            field_y = cy - fy
            x_7bit, y_6bit = quantize_to_bits(field_x, field_y, fw, fh)
            
            if frame_count == 35 or bounces == 4:
                bounces = 0
                data = payload.to_bytes()
                adv.set_custom_payload(data)
            
            if frame_count % 10 == 0:
                bounces += 1
                payload.add_bounce(Bounce(field_x, field_y, 13, 5))
                payload.team1_scored()
                
        if debug:
            window_name = 'Kicker Live'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

            display_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            cv2.rectangle(display_frame, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)
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
