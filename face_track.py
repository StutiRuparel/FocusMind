import cv2
import mediapipe as mp
import numpy as np
import argparse

RIGHT_EYE_IDX = {
    "outer_corner": 33,    # temporal corner of the right eye
    "inner_corner": 133,   # nasal corner of the right eye
    "upper_mid":    159,   # top‑mid of the eye opening
    "lower_mid":    145,   # bottom‑mid of the eye opening
    "iris_center":  468,   # centre of the iris (refined landmark)
}
LEFT_EYE_IDX = {
    "outer_corner": 362,
    "inner_corner": 263,
    "upper_mid":    386,
    "lower_mid": 374,
    "iris_center":  473,
}


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

def norm_to_px(lm, w, h):
    """lm is a mediapipe NormalizedLandmark, w/h are image dimensions."""
    return np.array([int(lm.x * w), int(lm.y * h)])


def get_gaze_direction(outer_corner, inner_corner,
                       upper_mid, lower_mid, iris_center,
                       horiz_thresh=0.35, vert_thresh=0.35):
    """
    Estimate gaze direction from a single eye.

    Parameters
    ----------
    outer_corner : np.ndarray (2,)
        Pixel coordinate of the eye’s outer (temporal) corner.
    inner_corner : np.ndarray (2,)
        Pixel coordinate of the eye’s inner (nasal) corner.
    upper_mid : np.ndarray (2,)
        Pixel coordinate of the upper eyelid midpoint.
    lower_mid : np.ndarray (2,)
        Pixel coordinate of the lower eyelid midpoint.
    iris_center : np.ndarray (2,)
        Pixel coordinate of the iris centre (provided by MediaPipe’s refined landmarks).
    horiz_thresh : float, optional
        Fraction of eye‑width used to decide “left” vs “right”. Default 0.35.
    vert_thresh : float, optional
        Fraction of eye‑height used to decide “up” vs “down”. Default 0.35.

    Returns
    -------
    str
        One of: "Left", "Right", "Up", "Down", "Center".
    """
    # Width / height of the eye bounding box
    eye_w = inner_corner[0] - outer_corner[0]
    eye_h = lower_mid[1] - upper_mid[1]

    # Normalised position of the iris centre inside the eye box (0‑1 range)
    rel_x = (iris_center[0] - outer_corner[0]) / eye_w   # 0 = outer, 1 = inner
    rel_y = (iris_center[1] - upper_mid[1])   / eye_h   # 0 = top,   1 = bottom

    # Decide direction with simple thresholds
    if rel_x < horiz_thresh:
        return "Left"
    if rel_x > 1 - horiz_thresh:
        return "Right"
    if rel_y < vert_thresh:
        return "Up"
    if rel_y > 1 - vert_thresh:
        return "Down"
    return "Center"

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
#source = int(args.video_path) if args.video_path.isdigit() else args.video_path
cap = cv2.VideoCapture(0) # 0 for webcam input
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video source: Webcam")

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

    h, w = frame.shape[:2]


    if results.multi_face_landmarks:
        # use first detected face
        landmarks = results.multi_face_landmarks[0].landmark
        pts = landmarks_to_np(landmarks, frame.shape)

        # outer  = landmarks_to_np(landmarks[RIGHT_EYE_IDX["outer_corner"]], frame.shape)
        # inner  = landmarks_to_np(landmarks[RIGHT_EYE_IDX["inner_corner"]], frame.shape)
        # upper  = landmarks_to_np(landmarks[RIGHT_EYE_IDX["upper_mid"]], frame.shape)
        # lower  = landmarks_to_np(landmarks[RIGHT_EYE_IDX["lower_mid"]], frame.shape)
        # iris   = landmarks_to_np(landmarks[RIGHT_EYE_IDX["iris_center"]], frame.shape)

        outer  = norm_to_px(landmarks[RIGHT_EYE_IDX["outer_corner"]], w, h)
        inner  = norm_to_px(landmarks[RIGHT_EYE_IDX["inner_corner"]], w, h)
        upper  = norm_to_px(landmarks[RIGHT_EYE_IDX["upper_mid"]], w, h)
        lower  = norm_to_px(landmarks[RIGHT_EYE_IDX["lower_mid"]], w, h)
        iris   = norm_to_px(landmarks[RIGHT_EYE_IDX["iris_center"]], w, h)

        for pt, col in zip([outer, inner, upper, lower, iris],
                           [(0,255,0), (0,255,0), (255,0,0), (255,0,0), (0,0,255)]):
            cv2.circle(frame, tuple(pt), 3, col, -1)

        # draw a few key points for visual feedback
        for idx in (61, 291, 13, 14, 159, 145, 386, 374):
            cv2.circle(frame, tuple(pts[idx]), 2, (0, 255, 0), -1)

        gaze = get_gaze_direction(outer, inner, upper, lower, iris)
        cv2.putText(frame, f"Gaze: {gaze}", (30,30),
        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0), 2)

        expr = infer_expression(pts)
        cv2.putText(frame, expr, (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        

    cv2.imshow("MediaPipe Facial Expression", frame)

    # Esc to quit early
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

