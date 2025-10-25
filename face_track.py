import cv2
import mediapipe as mp
import numpy as np
import argparse

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
    mouth_left   = pts[61]  # left corner
    mouth_right  = pts[291] # right corner
    mouth_top    = pts[13]  # upper lip
    mouth_bottom = pts[14]  # lower lip

    mouth_w = np.linalg.norm(mouth_right - mouth_left)
    mouth_h = np.linalg.norm(mouth_bottom - mouth_top)

    left_eye_top    = pts[159]
    left_eye_bottom = pts[145]
    right_eye_top   = pts[386]
    right_eye_bottom= pts[374]

    left_eye_h  = np.linalg.norm(left_eye_bottom - left_eye_top)
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
# 5️⃣  Open video source
# -------------------------------------------------------------
source = int(args.video_path) if args.video_path.isdigit() else args.video_path
cap = cv2.VideoCapture(source)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video source: {source}")

# -------------------------------------------------------------
# 6️⃣  Main processing loop
# -------------------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:                     # end of file
        print("Finished processing video.")
        break

    # MediaPipe expects RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        # use first detected face
        landmarks = results.multi_face_landmarks[0].landmark
        pts = landmarks_to_np(landmarks, frame.shape)

        # draw a few key points for visual feedback
        for idx in (61, 291, 13, 14, 159, 145, 386, 374):
            cv2.circle(frame, tuple(pts[idx]), 2, (0, 255, 0), -1)

        expr = infer_expression(pts)
        cv2.putText(frame, expr, (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

    cv2.imshow("MediaPipe Facial Expression", frame)

    # Esc to quit early
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()