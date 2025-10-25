# import cv2
import numpy as np
from typing import Tuple, Dict

# outer: temporal corner of the right eye
# inner: nasal corner of the right eye
# upper: top‑mid of the eye opening
# lower: bottom‑mid of the eye opening
# iris: centre of the iris (refined landmark)
RIGHT_EYE = {
    "outer": 33,   "inner": 133,
    "upper": 159,  "lower": 145,
    "iris":  468,
}
LEFT_EYE = {
    "outer": 362,  "inner": 263,
    "upper": 386,  "lower": 374,
    "iris":  473,
}


def landmarks_to_np_array(landmarks, img_shape):
    h, w = img_shape[:2]
    points = np.array(
        [(int(l.x * w), int(l.y * h)) for l in landmarks],
        dtype=np.int32,
    )
    return points


def norm_to_px(lm, w: int, h: int) -> Tuple[int, int]:
    """Return (x, y) in pixel space."""
    return int(lm.x * w), int(lm.y * h)


def get_eye_pts(idx_map: Dict[str, int], lm, w: int, h: int) -> Dict[str, Tuple[int, int]]:
    """
    Convert the five MediaPipe landmark indices to pixel coordinates.
    `lm` is the list of NormalizedLandmark objects for the current frame.
    """
    return {
        "outer": norm_to_px(lm[idx_map["outer"]], w, h),
        "inner": norm_to_px(lm[idx_map["inner"]], w, h),
        "upper": norm_to_px(lm[idx_map["upper"]], w, h),
        "lower": norm_to_px(lm[idx_map["lower"]], w, h),
        "iris":  norm_to_px(lm[idx_map["iris"]],  w, h),
    }


def eye_gaze_vector(pts: Dict[str, Tuple[int, int]]) -> np.ndarray:
    """
    Return normalized (dx, dy) of the iris centre inside its eye box.
    """
    eye_w = pts["inner"][0] - pts["outer"][0]
    eye_h = pts["lower"][1] - pts["upper"][1]

    if eye_w == 0 or eye_h == 0:
        return np.array([0.5, 0.5])

    dx = (pts["iris"][0] - pts["outer"][0]) / eye_w     # 0-1 across eye
    dy = (pts["iris"][1] - pts["upper"][1]) / eye_h     # 0-1 top to bottom
    # print("dx: ", dx)
    # print('pts["iris"][0]: ', pts["iris"][0])
    # print('pts["outer"][0]: ', pts["outer"][0])
    # print("eye_w: ", eye_w)

    # print("dy: ", dy)
    # print('pts["iris"][1]: ', pts["iris"][1])
    # print('pts["upper"][0]: ', pts["upper"][0])
    # print("eye_h: ", eye_h)
    return np.array([dx, dy])