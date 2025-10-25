import argparse
import time

import cv2
import mediapipe as mp
import numpy as np

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


# -------------------------------------------------------------
# 5️⃣  Open video source
# -------------------------------------------------------------
source = int(args.video_path) if args.video_path.isdigit() else args.video_path
cap = cv2.VideoCapture(source)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video source: {source}")


# -------------------------------------------------------------
# 6️⃣  Main processing loop
# -------------------------------------------------------------
# These track closed-eye duration across frames.
eyes_closed_start_time = None
eyes_closed_duration = 0.0

while True:
    ret, frame = cap.read()
    if not ret:                     # end of file
        print("Finished processing video.")
        break

    # MediaPipe expects RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    face_present = bool(results.multi_face_landmarks)
    expression = None
    eyes_open_ratio = 0.0

    if face_present:
        # use first detected face
        landmarks = results.multi_face_landmarks[0].landmark
        pts = landmarks_to_np(landmarks, frame.shape)

        # draw a few key points for visual feedback
        for idx in (61, 291, 13, 14, 159, 145, 386, 374, 33, 133, 362, 263):
            cv2.circle(frame, tuple(pts[idx]), 2, (0, 255, 0), -1)

        # expression and eye status ride on the same landmarks
        expression = infer_expression(pts)

        avg_ear = compute_average_ear(pts)
        eyes_open_ratio = normalize_ear(avg_ear)

        if eyes_open_ratio < 0.2:
            if eyes_closed_start_time is None:
                eyes_closed_start_time = time.perf_counter()
            eyes_closed_duration = time.perf_counter() - eyes_closed_start_time
        else:
            eyes_closed_start_time = None
            eyes_closed_duration = 0.0
    else:
        eyes_closed_start_time = None
        eyes_closed_duration = 0.0

    # Overlay telemetry in the top-left corner for live debugging.
    hud_lines = [
        f"Face: {'Yes' if face_present else 'No'}",
        f"Expression: {expression}" if expression else "Expression: --",
        f"Eye openness: {eyes_open_ratio:.2f}",
        f"Eyes closed: {eyes_closed_duration:.1f}s",
    ]

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
