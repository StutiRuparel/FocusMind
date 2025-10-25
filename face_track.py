import argparse
import math
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np

# Landmark groupings used for the additional analytics.
HEAD_POSE_LANDMARKS = [1, 152, 33, 263, 61, 291]
LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
LEFT_EYE_CORNERS = (33, 133)
RIGHT_EYE_CORNERS = (362, 263)
LEFT_EYE_VERTICAL = (159, 145)
RIGHT_EYE_VERTICAL = (386, 374)

# A lightweight 3D head model (in millimetres) for solvePnP head pose.
MODEL_POINTS = np.array(
    [
        (0.0, 0.0, 0.0),        # Nose tip
        (0.0, -63.6, -12.5),    # Chin
        (-43.3, 32.7, -26.0),   # Left eye outer corner
        (43.3, 32.7, -26.0),    # Right eye outer corner
        (-28.9, -28.9, -24.1),  # Left mouth corner
        (28.9, -28.9, -24.1),   # Right mouth corner
    ],
    dtype=np.float32,
)


# -------------------------------------------------------------
# 1️⃣  Command‑line argument – path to video (or 0 for webcam)
# -------------------------------------------------------------
parser = argparse.ArgumentParser(description="Facial‑expression demo with MediaPipe")
parser.add_argument("video_path", help="Path to video file, or 0 for webcam")
args = parser.parse_args()

# -------------------------------------------------------------
# 2️⃣  Initialise MediaPipe Face‑Mesh
# -------------------------------------------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# -------------------------------------------------------------
# 3️⃣  Helper to turn normalized landmarks into pixel coords
# -------------------------------------------------------------
def landmarks_to_np(landmarks, img_shape):
    h, w = img_shape[:2]
    points = np.array(
        [(int(l.x * w), int(l.y * h)) for l in landmarks],
        dtype=np.int32,
    )
    return points

def compute_iris_center(pts, indices):
    """Average the supplied landmark indices to approximate the iris centre."""
    return pts[indices].mean(axis=0)


def compute_gaze_ratios(pts):
    """
    Return the horizontal/vertical iris ratios in the [0, 1] range.

    The ratios describe where the iris lies between the eye corners (horizontal)
    and between the eyelids (vertical).
    """
    left_iris = compute_iris_center(pts, LEFT_IRIS_INDICES)
    right_iris = compute_iris_center(pts, RIGHT_IRIS_INDICES)

    left_outer, left_inner = pts[LEFT_EYE_CORNERS[0]], pts[LEFT_EYE_CORNERS[1]]
    right_outer, right_inner = pts[RIGHT_EYE_CORNERS[0]], pts[RIGHT_EYE_CORNERS[1]]

    left_top, left_bottom = pts[LEFT_EYE_VERTICAL[0]], pts[LEFT_EYE_VERTICAL[1]]
    right_top, right_bottom = pts[RIGHT_EYE_VERTICAL[0]], pts[RIGHT_EYE_VERTICAL[1]]

    # Sort coordinate pairs to avoid depending on landmark ordering conventions.
    left_min_x, left_max_x = sorted((left_outer[0], left_inner[0]))
    right_min_x, right_max_x = sorted((right_outer[0], right_inner[0]))
    left_width = left_max_x - left_min_x
    right_width = right_max_x - right_min_x

    left_min_y, left_max_y = sorted((left_top[1], left_bottom[1]))
    right_min_y, right_max_y = sorted((right_top[1], right_bottom[1]))
    left_height = left_max_y - left_min_y
    right_height = right_max_y - right_min_y

    # If MediaPipe fails to refine the iris/eyelids we bail out for this frame.
    if min(left_width, right_width, left_height, right_height) <= 1e-6:
        return None, None

    left_horizontal = (left_iris[0] - left_min_x) / left_width
    right_horizontal = (right_iris[0] - right_min_x) / right_width

    left_vertical = (left_iris[1] - left_min_y) / left_height
    right_vertical = (right_iris[1] - right_min_y) / right_height

    horizontal_ratio = float(
        np.clip((left_horizontal + right_horizontal) / 2.0, 0.0, 1.0)
    )
    vertical_ratio = float(np.clip((left_vertical + right_vertical) / 2.0, 0.0, 1.0))
    return horizontal_ratio, vertical_ratio


def determine_eye_direction(horizontal_ratio, vertical_ratio, low=0.35, high=0.65):
    """Classify eye direction from iris ratios."""
    if vertical_ratio < low:
        return "Up"
    if vertical_ratio > high:
        return "Down"
    if horizontal_ratio < low:
        return "Left"
    if horizontal_ratio > high:
        return "Right"
    return "Forward"


def rotation_matrix_to_euler_angles(rotation_matrix):
    """
    Convert a rotation matrix into XYZ Euler angles (in degrees).

    The result follows the OpenCV camera convention where +X is right, +Y is
    down, and +Z is forward. Angles are returned in degrees.
    """
    r = rotation_matrix
    sy = math.sqrt(r[0, 0] ** 2 + r[1, 0] ** 2)
    singular = sy < 1e-6

    if not singular:
        x = math.atan2(r[2, 1], r[2, 2])
        y = math.atan2(-r[2, 0], sy)
        z = math.atan2(r[1, 0], r[0, 0])
    else:
        x = math.atan2(-r[1, 2], r[1, 1])
        y = math.atan2(-r[2, 0], sy)
        z = 0.0

    return tuple(math.degrees(angle) for angle in (x, y, z))


def estimate_head_orientation(pts, frame_shape):
    """Estimate head pitch/yaw (degrees) from the 2D landmarks via solvePnP."""
    h, w = frame_shape[:2]
    image_points = pts[HEAD_POSE_LANDMARKS].astype(np.float32)

    focal_length = w
    center = (w / 2.0, h / 2.0)
    camera_matrix = np.array(
        [
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    success, rvec, _tvec = cv2.solvePnP(
        MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rvec)
    pitch, yaw, _ = rotation_matrix_to_euler_angles(rotation_matrix)
    # Pitch (rotation around the X axis) is positive when the subject nods down.
    pitch = float(pitch)
    if pitch > 90.0:
        pitch -= 180.0
    elif pitch < -90.0:
        pitch += 180.0

    yaw = float(yaw)
    if yaw > 90.0:
        yaw -= 180.0
    elif yaw < -90.0:
        yaw += 180.0

    return pitch, yaw


def determine_head_direction(pitch, yaw, pitch_thresh=10.0, yaw_thresh=10.0, forward_margin=35.0):
    """
    Reduce head pose into a coarse direction label.
    Prefers the axis whose absolute deviation exceeds its threshold by more.
    """

    # If both pitch and yaw remain within the relaxed forward margin we call it "Forward".
    if abs(pitch) <= forward_margin and abs(yaw) <= forward_margin:
        return "Forward"

    pitch_dev = pitch if abs(pitch) >= pitch_thresh else 0.0
    yaw_dev = yaw if abs(yaw) >= yaw_thresh else 0.0

    if abs(yaw_dev) >= abs(pitch_dev):
        if yaw_dev > 0.0:
            return "Right"
        if yaw_dev < 0.0:
            return "Left"
    else:
        if pitch_dev > 0.0:
            return "Down"
        if pitch_dev < 0.0:
            return "Up"
    return "Forward"

# -------------------------------------------------------------
# 4️⃣  Simple expression rules (you can tune the thresholds)
# -------------------------------------------------------------
def infer_expression(pts):
    # indices correspond to the 68‑point scheme used in many papers
    mouth_left = pts[61]   # left corner
    mouth_right = pts[291] # right corner
    mouth_top = pts[13]    # upper lip
    mouth_bottom = pts[14] # lower lip

    mouth_w = np.linalg.norm(mouth_right - mouth_left)
    mouth_h = np.linalg.norm(mouth_bottom - mouth_top)

    left_eye_top = pts[159]
    left_eye_bottom = pts[145]
    right_eye_top = pts[386]
    right_eye_bottom = pts[374]

    left_eye_h = np.linalg.norm(left_eye_bottom - left_eye_top)
    right_eye_h = np.linalg.norm(right_eye_bottom - right_eye_top)

    # mouth curvature proxy (frown vs smile)
    mouth_center = (mouth_top + mouth_bottom) // 2
    curvature = (mouth_left[1] + mouth_right[1]) / 2 - mouth_center[1]

    # thresholds (empirical, adjust for your video)
    if mouth_h / mouth_w > 0.6:
        return "Smile"
    if left_eye_h / mouth_w > 0.35 and right_eye_h / mouth_w > 0.35:
        return "Surprise"
    if curvature < -0.1 * mouth_w:
        return "Frown"
    return "Neutral"


# -------------------------------------------------------------
# 4b️⃣  Eye aspect ratio helpers
# -------------------------------------------------------------
def compute_average_ear(pts):
    """Return the average eye aspect ratio (EAR) across both eyes."""
    left_eye_height = np.linalg.norm(pts[159] - pts[145])
    left_eye_width = np.linalg.norm(pts[33] - pts[133])
    right_eye_height = np.linalg.norm(pts[386] - pts[374])
    right_eye_width = np.linalg.norm(pts[362] - pts[263])

    left_ear = left_eye_height / left_eye_width if left_eye_width else 0.0
    right_ear = right_eye_height / right_eye_width if right_eye_width else 0.0

    return (left_ear + right_ear) / 2.0


def normalize_ear(ear, closed_threshold=0.15, open_threshold=0.35):
    """
    Map EAR into a 0.0-1.0 range, where 0.0 means closed and 1.0 fully open.
    Thresholds are empirical and may be tuned for a specific subject/video.
    """
    if open_threshold == closed_threshold:
        return 0.0
    normalized = (ear - closed_threshold) / (open_threshold - closed_threshold)
    return float(np.clip(normalized, 0.0, 1.0))


def update_blink_metrics(
    eyes_open_ratio,
    current_time,
    blink_in_progress,
    blink_count,
    eyes_closed_start_time,
    eyes_closed_duration,
):
    """
    Apply blink hysteresis (0.2 close / 0.25 open) and update tracking values.

    Returns the updated tuple:
        blink_in_progress, blink_count, eyes_closed_start_time, eyes_closed_duration, blink_detected
    """
    blink_detected = False

    if eyes_open_ratio < 0.2:
        if eyes_closed_start_time is None:
            eyes_closed_start_time = current_time
        eyes_closed_duration = current_time - eyes_closed_start_time
        blink_in_progress = True
    elif eyes_open_ratio > 0.25:
        if blink_in_progress:
            blink_count += 1
            blink_detected = True
        blink_in_progress = False
        eyes_closed_start_time = None
        eyes_closed_duration = 0.0
    else:
        if eyes_closed_start_time is not None:
            eyes_closed_duration = current_time - eyes_closed_start_time

    return (
        blink_in_progress,
        blink_count,
        eyes_closed_start_time,
        eyes_closed_duration,
        blink_detected,
    )


# -------------------------------------------------------------
# 5️⃣  Open video source
# -------------------------------------------------------------
# 0 selects the default webcam; passing a path still works for recorded clips.
source_arg = args.video_path
source = int(source_arg) if source_arg.isdigit() else source_arg
cap = cv2.VideoCapture(source)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video source: {source}")


# -------------------------------------------------------------
# 6️⃣  Main processing loop
# -------------------------------------------------------------
# These track closed-eye duration, blinking, and keep-alive stats across frames.
eyes_closed_start_time = None
eyes_closed_duration = 0.0
blink_in_progress = False
blink_count = 0
session_start_time = time.perf_counter()
# Rolling buffers for smoothing.
eye_horizontal_history = deque(maxlen=5)
eye_vertical_history = deque(maxlen=5)
head_pitch_history = deque(maxlen=5)
head_yaw_history = deque(maxlen=5)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Finished processing video.")
        break

    current_time = time.perf_counter()

    # MediaPipe expects RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    face_present = bool(results.multi_face_landmarks)
    expression = None
    eyes_open_ratio = 0.0
    eye_direction = None
    head_direction = None

    if face_present:
        landmarks = results.multi_face_landmarks[0].landmark
        pts = landmarks_to_np(landmarks, frame.shape)

        # draw a few key points for visual feedback (mouth corners, lip centre, eyelid points)
        for idx in (61, 291, 13, 14, 159, 145, 386, 374, 33, 133, 362, 263):
            cv2.circle(frame, tuple(pts[idx]), 2, (0, 255, 0), -1)

        # Existing facial expression logic is untouched.
        expression = infer_expression(pts)

        avg_ear = compute_average_ear(pts)
        eyes_open_ratio = normalize_ear(avg_ear)

        (
            blink_in_progress,
            blink_count,
            eyes_closed_start_time,
            eyes_closed_duration,
            _,
        ) = update_blink_metrics(
            eyes_open_ratio,
            current_time,
            blink_in_progress,
            blink_count,
            eyes_closed_start_time,
            eyes_closed_duration,
        )

        # Head direction derived from smoothed pitch/yaw estimates.
        orientation = estimate_head_orientation(pts, frame.shape)
        if orientation is not None:
            pitch, yaw = orientation
            head_pitch_history.append(pitch)
            head_yaw_history.append(yaw)
            if head_pitch_history and head_yaw_history:
                avg_pitch = float(np.mean(head_pitch_history))
                avg_yaw = float(np.mean(head_yaw_history))
                head_direction = determine_head_direction(avg_pitch, avg_yaw)

        # Eye direction derived from smoothed iris ratios.
        horizontal_ratio, vertical_ratio = compute_gaze_ratios(pts)
        if horizontal_ratio is not None and vertical_ratio is not None:
            eye_horizontal_history.append(horizontal_ratio)
            eye_vertical_history.append(vertical_ratio)
            if eye_horizontal_history and eye_vertical_history:
                avg_horizontal = float(np.mean(eye_horizontal_history))
                avg_vertical = float(np.mean(eye_vertical_history))
                eye_direction = determine_eye_direction(avg_horizontal, avg_vertical)
        else:
            eye_horizontal_history.clear()
            eye_vertical_history.clear()
    else:
        eyes_closed_start_time = None
        eyes_closed_duration = 0.0
        blink_in_progress = False
        eye_horizontal_history.clear()
        eye_vertical_history.clear()
        head_pitch_history.clear()
        head_yaw_history.clear()

    elapsed_minutes = max((current_time - session_start_time) / 60.0, 1e-6)
    blink_rate = (blink_count / elapsed_minutes) if blink_count else 0.0

    # Overlay telemetry in the top-left corner for live debugging.
    hud_lines = [
        f"Face: {'Yes' if face_present else 'No'}",
        f"Expression: {expression}" if expression else "Expression: --",
        f"Eye openness: {eyes_open_ratio:.2f}",
        f"Eyes closed: {eyes_closed_duration:.1f}s",
        f"Blink rate: {blink_rate:.1f} blinks/min",
    ]

    if eye_direction is not None:
        hud_lines.append(f"Eye direction: {eye_direction}")

    if head_direction is not None:
        hud_lines.append(f"Head direction: {head_direction}")

    y = 30
    for line in hud_lines:
        cv2.putText(
            frame,
            line,
            (30, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
        )
        y += 30

    cv2.imshow("MediaPipe Facial Expression", frame)

    # Esc to quit early
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
