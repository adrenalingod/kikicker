# kicker_vision.py
import cv2
import numpy as np

# Ball color in HSV (orange)
LOWER_ORANGE = np.array([10, 120, 129])
UPPER_ORANGE = np.array([40, 255, 255])
MIN_BALL_AREA = 100

# Field color HSV (green)
LOWER_GREEN = np.array([30, 50, 30])
UPPER_GREEN = np.array([80, 255, 255])


def find_playfield_roi(image, debug=False):
    """
    Detects the green field and returns its bounding box (x, y, w, h),
    or None if not found.
    If debug=True, shows step-by-step windows.
    """

    # 1) Convert to HSV (input image is expected in RGB)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    # 2) Green mask
    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

    # 3) Close gaps
    kernel = np.ones((50, 50), np.uint8)
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 4) Find contours on closed mask
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        if debug:
            print("No contours found.")
        return None

    # 5) Select largest green area
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    # DEBUG: Show contour on the original image
    if debug:
        cv2.imshow("Step 1 - HSV", hsv)
        cv2.imshow("Step 2 - Green Mask BEFORE Closing", mask)
        cv2.imshow("Step 3 - Green Mask AFTER Closing", closed)
        # For visualization convert RGB->BGR for correct color display in OpenCV
        debug_img = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.drawContours(debug_img, [largest], -1, (0, 255, 0), 3)
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 0, 255), 3)
        cv2.imshow("Step 4 - Largest Contour + Bounding Field", debug_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return x, y, w, h



def detect_ball(frame, debug=False):
    """
    Detects the orange ball in a frame.
    Returns (cx, cy, x, y, w, h) or None if no ball.
    """
    # frame is expected in RGB
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, LOWER_ORANGE, UPPER_ORANGE)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < MIN_BALL_AREA:
        return None

    x, y, w, h = cv2.boundingRect(c)
    cx = x + w // 2
    cy = y + h // 2
    # If debug is requested, show a visualization (convert to BGR for display)
    if debug:
        dbg = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.rectangle(dbg, (x, y), (x + w, y + h), (0, 255, 0), 2)
        label = f"{cx},{cy}"
        cv2.putText(dbg, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow("Detect Ball - Debug", dbg)
        # non-blocking short wait so window updates
        cv2.waitKey(1)

    return (cx, cy, x, y, w, h)


def quantize_to_bits(field_x, field_y, field_width, field_height):
    """
    Maps field-local pixel coords to:
      - X: 7 bits (0..127)
      - Y: 6 bits (0..63)
    """
    x_7bit = int((field_x / field_width) * 127)
    y_6bit = int((field_y / field_height) * 63)

    x_7bit = max(0, min(127, x_7bit))
    y_6bit = max(0, min(63,  y_6bit))

    return x_7bit, y_6bit