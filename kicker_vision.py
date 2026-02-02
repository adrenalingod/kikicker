# kicker_vision.py
import cv2
import numpy as np

# Ball color in HSV (orange)
LOWER_ORANGE = np.array([10, 120, 129])
UPPER_ORANGE = np.array([40, 255, 255])
MIN_BALL_AREA = 3

# Field aspect ratio (width:height = 68:120)
FIELD_RATIO_W = 68
FIELD_RATIO_H = 120

# Template cache for ROI detection (loaded once on first call)
_template_cache = None


def load_template(template_path='TrueRoi.png'):
    """Loads the template and extracts edges for matching."""
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    # Extract edges for better matching
    template_edges = cv2.Canny(template, 50, 150)
    
    return template, template_edges


def find_playfield_roi(image, debug=False, template_path='TrueRoi.png', rotation_range=2, rotation_step=2):
    """
    Finds the playfield ROI using template matching with rotation support.
    
    Args:
        image: RGB image
        debug: Show debug visualization
        template_path: Path to template image
        rotation_range: Maximum rotation angle to test in degrees (±range)
        rotation_step: Step size for rotation testing in degrees
        
    Returns:
        dict with keys:
            'corners': numpy array of 4 corner points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
                       ordered as: top-left, top-right, bottom-right, bottom-left
            'center': (cx, cy) center point
            'angle': rotation angle in degrees
            'width': width of the playfield
            'height': height of the playfield
        or None if not found
    """
    global _template_cache
    
    # Load template only once
    if _template_cache is None:
        try:
            _template_cache = load_template(template_path)
        except FileNotFoundError as e:
            if debug:
                print(f"Template error: {e}")
            return None
    
    template, template_edges = _template_cache
    template_h, template_w = template.shape
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    img_h, img_w = gray.shape
    
    if debug:
        print(f"Template size: {template_w}x{template_h}")
        print(f"Image size: {img_w}x{img_h}")
    
    # Extract edges in search image
    edges_img = cv2.Canny(gray, 50, 150)
    
    if debug:
        cv2.imshow("1. Template Edges", template_edges)
    
    # Calculate sensible scale range (field should fill 60-95% of image)
    min_coverage, max_coverage = 0.6, 0.95
    
    scale_to_fit_w = (img_w * max_coverage) / template_w
    scale_to_fit_h = (img_h * max_coverage) / template_h
    max_scale = min(scale_to_fit_w, scale_to_fit_h)
    
    scale_to_fill_w = (img_w * min_coverage) / template_w
    scale_to_fill_h = (img_h * min_coverage) / template_h
    min_scale = min(scale_to_fill_w, scale_to_fill_h)
    
    if debug:
        print(f"Smart scale range: {min_scale:.3f} to {max_scale:.3f}")
    
    # Multi-scale and multi-rotation template matching
    best_match = None
    best_val = -1
    best_scale = 1.0
    best_rotation = 0.0
    best_method = None
    
    methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
    scales = np.linspace(min_scale, max_scale, 25)
    
    # Generate rotation angles to test
    if rotation_range > 0:
        rotation_angles = np.arange(-rotation_range, rotation_range + rotation_step, rotation_step)
    else:
        rotation_angles = [0]
    
    if debug:
        print(f"Testing {len(scales)} scales × {len(rotation_angles)} rotations = {len(scales) * len(rotation_angles)} combinations per method")
    
    for method in methods:
        method_name = {cv2.TM_CCOEFF_NORMED: "CCOEFF", cv2.TM_CCORR_NORMED: "CCORR"}[method]
        
        for angle in rotation_angles:
            # Rotate template edges around center
            if angle != 0:
                center = (template_w // 2, template_h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Calculate new bounding box after rotation
                cos = np.abs(rotation_matrix[0, 0])
                sin = np.abs(rotation_matrix[0, 1])
                new_w = int((template_h * sin) + (template_w * cos))
                new_h = int((template_h * cos) + (template_w * sin))
                
                # Adjust translation to keep image centered
                rotation_matrix[0, 2] += (new_w / 2) - center[0]
                rotation_matrix[1, 2] += (new_h / 2) - center[1]
                
                rotated_template = cv2.warpAffine(template_edges, rotation_matrix, (new_w, new_h))
                template_to_use = rotated_template
                current_template_w = new_w
                current_template_h = new_h
            else:
                template_to_use = template_edges
                current_template_w = template_w
                current_template_h = template_h
            
            for scale in scales:
                scaled_w = int(current_template_w * scale)
                scaled_h = int(current_template_h * scale)
                
                # Skip invalid sizes
                if scaled_w > img_w or scaled_h > img_h or scaled_w < 50 or scaled_h < 50:
                    continue
                
                scaled_template = cv2.resize(template_to_use, (scaled_w, scaled_h))
                
                try:
                    res = cv2.matchTemplate(edges_img, scaled_template, method)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val > best_val:
                        best_val = max_val
                        best_match = max_loc
                        best_scale = scale
                        best_rotation = angle
                        best_method = method_name
                        
                    if debug and max_val > 0.2:
                        print(f"  {method_name} Angle {angle:+.1f}° Scale {scale:.3f} ({scaled_w}x{scaled_h}): score={max_val:.3f}")
                        
                except cv2.error:
                    continue
    
    # Check match quality threshold
    if best_val < 0.1:
        if debug:
            print(f"\nTemplate matching failed. Best score: {best_val:.3f}")
            print("Press any key to close debug windows...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return None
    
    # Calculate the 4 corners of the rotated playfield
    match_x, match_y = best_match
    
    # Original template dimensions at best scale
    scaled_template_w = int(template_w * best_scale)
    scaled_template_h = int(template_h * best_scale)
    
    # Calculate center of the matched rotated template
    if best_rotation != 0:
        cos = np.abs(np.cos(np.radians(best_rotation)))
        sin = np.abs(np.sin(np.radians(best_rotation)))
        rotated_w = int((scaled_template_h * sin) + (scaled_template_w * cos))
        rotated_h = int((scaled_template_h * cos) + (scaled_template_w * sin))
        
        center_x = match_x + rotated_w // 2
        center_y = match_y + rotated_h // 2
    else:
        center_x = match_x + scaled_template_w // 2
        center_y = match_y + scaled_template_h // 2
    
    # Calculate the 4 corners of the original (non-rotated) template
    half_w = scaled_template_w / 2
    half_h = scaled_template_h / 2
    
    # Define corners relative to center (before rotation)
    # Order: top-left, top-right, bottom-right, bottom-left
    corners_local = np.array([
        [-half_w, -half_h],  # top-left
        [half_w, -half_h],   # top-right
        [half_w, half_h],    # bottom-right
        [-half_w, half_h]    # bottom-left
    ], dtype=np.float32)
    
    # Apply rotation
    angle_rad = np.radians(-best_rotation)  # Negative because cv2 rotates clockwise
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    rotation_mat = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    
    rotated_corners = corners_local @ rotation_mat.T
    
    # Translate to image coordinates
    rotated_corners[:, 0] += center_x
    rotated_corners[:, 1] += center_y
    
    # Clamp corners to image boundaries
    rotated_corners[:, 0] = np.clip(rotated_corners[:, 0], 0, img_w - 1)
    rotated_corners[:, 1] = np.clip(rotated_corners[:, 1], 0, img_h - 1)
    
    result = {
        'corners': rotated_corners.astype(np.int32),
        'center': (int(center_x), int(center_y)),
        'angle': best_rotation,
        'width': scaled_template_w,
        'height': scaled_template_h
    }
    
    if debug:
        print(f"\n✓ Template match found!")
        print(f"  Method: {best_method}")
        print(f"  Score: {best_val:.3f}")
        print(f"  Scale: {best_scale:.3f}")
        print(f"  Rotation: {best_rotation:+.1f}°")
        print(f"  Center: ({center_x}, {center_y})")
        print(f"  Size: {scaled_template_w}x{scaled_template_h}")
        print(f"  Corners:")
        for i, corner in enumerate(rotated_corners):
            corner_names = ["top-left", "top-right", "bottom-right", "bottom-left"]
            print(f"    {corner_names[i]}: ({corner[0]:.1f}, {corner[1]:.1f})")
        
        # Show matched edges overlay with green/red coloring
        edges_overlay = cv2.cvtColor(edges_img, cv2.COLOR_GRAY2BGR)
        
        # Create the scaled and rotated template for overlay
        if best_rotation != 0:
            center = (template_w // 2, template_h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, best_rotation, 1.0)
            cos = np.abs(rotation_matrix[0, 0])
            sin = np.abs(rotation_matrix[0, 1])
            new_w = int((template_h * sin) + (template_w * cos))
            new_h = int((template_h * cos) + (template_w * sin))
            rotation_matrix[0, 2] += (new_w / 2) - center[0]
            rotation_matrix[1, 2] += (new_h / 2) - center[1]
            rotated_template = cv2.warpAffine(template_edges, rotation_matrix, (new_w, new_h))
            
            # Calculate dimensions for scaling
            rotated_w = int((scaled_template_h * sin) + (scaled_template_w * cos))
            rotated_h = int((scaled_template_h * cos) + (scaled_template_w * sin))
            scaled_template_overlay = cv2.resize(rotated_template, (rotated_w, rotated_h))
            
            # Position for overlay
            overlay_x = match_x
            overlay_y = match_y
            overlay_w = rotated_w
            overlay_h = rotated_h
        else:
            scaled_template_overlay = cv2.resize(template_edges, (scaled_template_w, scaled_template_h))
            overlay_x = match_x
            overlay_y = match_y
            overlay_w = scaled_template_w
            overlay_h = scaled_template_h
        
        # First, make all search edges green
        search_mask = edges_img > 0
        edges_overlay[search_mask] = [0, 255, 0]  # Green for search edges
        
        # Then overlay template edges in red at matched location
        if overlay_x >= 0 and overlay_y >= 0 and overlay_x + overlay_w <= img_w and overlay_y + overlay_h <= img_h:
            template_mask = scaled_template_overlay > 0
            edges_overlay[overlay_y:overlay_y+overlay_h, overlay_x:overlay_x+overlay_w][template_mask] = [0, 0, 255]  # Red for template
        
        # Draw the rotated rectangle corners
        corners_int = rotated_corners.astype(np.int32)
        cv2.polylines(edges_overlay, [corners_int], True, (0, 0, 255), 2)
        
        # Draw corner points with labels
        corner_labels = ["TL", "TR", "BR", "BL"]
        for i, corner in enumerate(corners_int):
            cv2.circle(edges_overlay, tuple(corner), 6, (255, 0, 0), -1)
            cv2.putText(edges_overlay, corner_labels[i], 
                       (corner[0] + 8, corner[1] - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        cv2.circle(edges_overlay, (int(center_x), int(center_y)), 5, (255, 0, 0), -1)
        
        cv2.imshow("2. Matched Edges", edges_overlay)
        
        # Show on original image
        debug_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        cv2.polylines(debug_img, [corners_int], True, (0, 0, 255), 3)
        
        # Draw corner points with labels on original image
        for i, corner in enumerate(corners_int):
            cv2.circle(debug_img, tuple(corner), 8, (255, 0, 0), -1)
            cv2.putText(debug_img, corner_labels[i], 
                       (corner[0] + 10, corner[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.circle(debug_img, (int(center_x), int(center_y)), 5, (255, 0, 0), -1)
        cv2.putText(debug_img, f"{best_method}: {best_val:.2f} {best_rotation:+.1f}deg", 
                   (int(center_x) - 100, int(center_y) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        cv2.imshow("3. Detected ROI", debug_img)
        print("\nPress any key to close debug windows...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return result


def point_in_rotated_rect(point, corners):
    """
    Check if a point is inside a rotated rectangle defined by 4 corners.
    Uses cross product method.
    
    Args:
        point: (x, y) tuple
        corners: numpy array of 4 corner points
        
    Returns:
        bool: True if point is inside
    """
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    
    # Check if point is on the same side of all 4 edges
    d1 = sign(point, corners[0], corners[1])
    d2 = sign(point, corners[1], corners[2])
    d3 = sign(point, corners[2], corners[3])
    d4 = sign(point, corners[3], corners[0])
    
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0) or (d4 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0) or (d4 > 0)
    
    return not (has_neg and has_pos)


def detect_ball(frame, field_roi=None, debug=False):
    """
    Detects the orange ball within the specified ROI.
    
    Args:
        frame: RGB image
        field_roi: Dictionary from find_playfield_roi() or None for full image
        debug: Show debug visualization
        
    Returns:
        (cx, cy, x, y, w, h) in global coordinates, or None if no ball found
    """
    img_h, img_w = frame.shape[:2]
    
    if field_roi is None:
        # Search entire image
        roi_frame = frame
        roi_x, roi_y = 0, 0
        search_mask = None
    else:
        # Get axis-aligned bounding box of the rotated rectangle for efficient search
        corners = field_roi['corners']
        x_min = int(np.min(corners[:, 0]))
        y_min = int(np.min(corners[:, 1]))
        x_max = int(np.max(corners[:, 0]))
        y_max = int(np.max(corners[:, 1]))
        
        # Clamp to image boundaries
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(img_w, x_max)
        y_max = min(img_h, y_max)
        
        roi_x, roi_y = x_min, y_min
        roi_frame = frame[y_min:y_max, x_min:x_max]
        
        # Create mask for the rotated rectangle within the bounding box
        mask_shape = (y_max - y_min, x_max - x_min)
        search_mask = np.zeros(mask_shape, dtype=np.uint8)
        
        # Adjust corners to ROI-local coordinates
        corners_local = corners.copy()
        corners_local[:, 0] -= x_min
        corners_local[:, 1] -= y_min
        
        cv2.fillPoly(search_mask, [corners_local], 255)
    
    # Convert to HSV and create color mask
    hsv = cv2.cvtColor(roi_frame, cv2.COLOR_RGB2HSV)
    color_mask = cv2.inRange(hsv, LOWER_ORANGE, UPPER_ORANGE)
    
    # Apply ROI mask if we have a rotated rectangle
    if search_mask is not None:
        color_mask = cv2.bitwise_and(color_mask, search_mask)
    
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if debug:
        # Visualization on full image
        dbg = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Draw ROI
        if field_roi is not None:
            corners = field_roi['corners']
            cv2.polylines(dbg, [corners], True, (0, 0, 255), 2)
            
            # Draw corner points with labels
            corner_labels = ["TL", "TR", "BR", "BL"]
            for i, corner in enumerate(corners):
                cv2.circle(dbg, tuple(corner), 6, (255, 0, 0), -1)
                cv2.putText(dbg, corner_labels[i], 
                           (corner[0] + 8, corner[1] - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            center = field_roi['center']
            cv2.circle(dbg, center, 5, (255, 0, 0), -1)
    
    if not contours:
        if debug:
            print("No ball contours found in ROI")
            cv2.imshow("Ball Detection", dbg)
            cv2.waitKey(1)
        return None

    # Find largest contour
    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < MIN_BALL_AREA:
        if debug:
            print(f"Largest contour too small: {cv2.contourArea(c)}")
        return None

    # Bounding box in ROI-local coordinates
    x_local, y_local, w, h = cv2.boundingRect(c)
    
    # Convert to global image coordinates
    x = roi_x + x_local
    y = roi_y + y_local
    cx = x + w // 2
    cy = y + h // 2
    
    if debug:
        # Draw ball
        cv2.rectangle(dbg, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(dbg, (cx, cy), 5, (0, 255, 0), -1)
        cv2.putText(dbg, f"Ball: ({cx},{cy})", (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow("Ball Detection", dbg)
        cv2.waitKey(1)

    return (cx, cy, x, y, w, h)


def transform_to_field_coordinates(ball_cx, ball_cy, field_roi):
    """
    Transform ball position from image coordinates to field-local coordinates.
    Returns coordinates relative to the rotated playfield (0,0 at top-left corner).
    
    Args:
        ball_cx, ball_cy: Ball center in image coordinates
        field_roi: Dictionary from find_playfield_roi()
        
    Returns:
        (field_x, field_y): Coordinates in the playfield coordinate system
    """
    center = field_roi['center']
    angle = field_roi['angle']
    width = field_roi['width']
    height = field_roi['height']
    
    # Translate to center-relative coordinates
    dx = ball_cx - center[0]
    dy = ball_cy - center[1]
    
    # Rotate back to align with playfield (inverse rotation)
    angle_rad = np.radians(angle)  # Positive because we're doing inverse rotation
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    rotated_x = dx * cos_a - dy * sin_a
    rotated_y = dx * sin_a + dy * cos_a
    
    # Translate to top-left origin (0,0 at top-left corner of field)
    field_x = rotated_x + width / 2
    field_y = rotated_y + height / 2
    
    return field_x, field_y


def quantize_to_bits(field_x, field_y, field_width, field_height):
    """
    Maps field-local pixel coordinates to bit representation:
      - X: 8 bits (0..255)
      - Y: 7 bits (0..127)
    """
    x_8bit = int((field_x / field_width) * 255)
    y_7bit = int((field_y / field_height) * 127)

    x_8bit = max(0, min(255, x_8bit))
    y_7bit = max(0, min(127, y_7bit))

    return x_8bit, y_7bit


if __name__ == '__main__':
    # Load initial frame
    initial_frame = cv2.imread('initial_frame.png')
    if initial_frame is None:
        print("Error: Could not read initial_frame.png")
        exit(1)
    
    print("Image loaded successfully")
    initial_frame_rgb = cv2.cvtColor(initial_frame, cv2.COLOR_BGR2RGB)
    
    # Find playfield ROI
    field_roi = find_playfield_roi(initial_frame_rgb, debug=True)
    
    if field_roi:
        print(f"\nPlayfield ROI detected:")
        print(f"  Center: {field_roi['center']}")
        print(f"  Rotation: {field_roi['angle']:+.1f}°")
        print(f"  Size: {field_roi['width']}x{field_roi['height']}")
        print(f"  Corners:")
        corner_names = ["top-left", "top-right", "bottom-right", "bottom-left"]
        for i, corner in enumerate(field_roi['corners']):
            print(f"    {corner_names[i]}: ({corner[0]}, {corner[1]})")
        
        # Visualize detected ROI with corners
        roi_vis = cv2.cvtColor(initial_frame_rgb, cv2.COLOR_RGB2BGR)
        
        corners = field_roi['corners']
        cv2.polylines(roi_vis, [corners], True, (0, 0, 255), 3)
        
        # Draw corner points
        for i, corner in enumerate(corners):
            cv2.circle(roi_vis, tuple(corner), 8, (255, 0, 0), -1)
            cv2.putText(roi_vis, str(i+1), tuple(corner + [10, 10]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Draw center
        cv2.circle(roi_vis, field_roi['center'], 8, (0, 255, 255), -1)
        
        cv2.putText(roi_vis, f"ROI: {field_roi['width']}x{field_roi['height']} {field_roi['angle']:+.1f}deg", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Detected ROI", roi_vis)
        print("\nPress any key to continue to ball detection...")
        cv2.waitKey(0)
        cv2.destroyWindow("Detected ROI")
        
        # Test ball detection
        print("\nTesting ball detection. Press 'q' to quit.")
        
        try:
            while True:
                result = detect_ball(initial_frame_rgb, field_roi, debug=True)
                
                if result:
                    cx, cy, bx, by, bw, bh = result
                    field_x, field_y = transform_to_field_coordinates(cx, cy, field_roi)
                    print(f"✓ Ball found at image ({cx}, {cy}) -> field ({field_x:.1f}, {field_y:.1f})")
                else:
                    print("✗ No ball detected in ROI")
                
                key = cv2.waitKey(500)
                if key & 0xFF == ord('q'):
                    print("\nQuitting...")
                    break
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            cv2.destroyAllWindows()
            
    else:
        print("No playfield ROI detected")

