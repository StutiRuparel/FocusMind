"""
calibration.py
==============

Functions that guide the user through a quick eye‑movement calibration,
measure the raw eye‑gaze ratios, compute personalized thresholds and
persist them to JSON.

The module does **not** depend on any GUI framework – it just uses the
already‑opened OpenCV capture object.
"""

import json
import time
import numpy as np
from typing import Dict
import cv2
from face_tracking_utils import RIGHT_EYE, LEFT_EYE
from ema_smoother import GazeSmoother

# -------------------------------------------------------------------------
# Core calibration routine
# -------------------------------------------------------------------------
def calibrate_user(
    cap,
    face_mesh,
    w: int,
    h: int,
    get_eye_pts,
    eye_gaze_vector,
    smoothing_alpha: float = 0.3,
    font=cv2.FONT_HERSHEY_SIMPLEX,
) -> Dict[str, float]:
    """
    Runs a 5‑step calibration (center, left, right, up, down).

    Parameters
    ----------
    cap            : cv2.VideoCapture – already opened.
    face_mesh      : mediapipe FaceMesh object.
    w, h           : frame width/height (pixels).
    get_eye_pts    : callable(idx_map) → dict of 5 eye landmarks in pixel coordinates.
    eye_gaze_vector: callable(eye_pts) → np.array([dx, dy]) where 0‑1 are normalized.
    font           : OpenCV font used for the on‑screen prompt.

    Returns
    -------
    cfg : dict
        {
            "left_thresh": float,   # left‑side boundary
            "right_thresh": float,   # right‑side boundary
            "top_thresh" : float,   # top‑side boundary
            "down_thresh" : float,   # bottom‑side boundary
        }
    The dict is also written to *gaze_calibration_parameters.json* in the current folder.
    """
    prompts = [
        ("Look CENTER",   None),
        ("Look LEFT",  None),
        ("Look RIGHT", None),
        ("Look UP",    None),
        ("Look DOWN",  None),
    ]

    # Containers for the raw horizontal/vertical values we collect.
    horiz_vals = []
    vert_vals  = []

    smoother = GazeSmoother(alpha=smoothing_alpha)

    for text, _ in prompts:
        samples_h, samples_v = [], [] # containers for the current pose

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark

                # Grab eye points for both eyes using the caller‑provided helper.
                right_pts = get_eye_pts(RIGHT_EYE, lm, w, h)
                left_pts  = get_eye_pts(LEFT_EYE,  lm, w, h)

                # Average the two eyes → raw (dx, dy)
                raw_vec = (eye_gaze_vector(right_pts) + eye_gaze_vector(left_pts)) / 2.0

                # Smooth the vector before we record it
                smooth_vec = smoother.update(raw_vec)

                # store the smoothed components
                samples_h.append(float(smooth_vec[0]))
                samples_v.append(float(smooth_vec[1]))

            # Show instruction on screen.
            cv2.putText(frame, f"CALIBRATE: {text}", (30, 40), font, 1.2, (0, 255, 255), 2)
            cv2.imshow("Calibration", frame)

            user_keyboard_input = cv2.waitKey(1) & 0xFF
            # 13 = carriage return, 10 = line-feed
            if user_keyboard_input == 13 or user_keyboard_input == 10:
                break       # Go to the next pose
            # 27 = esc
            if user_keyboard_input == 27:
                raise KeyboardInterrupt

        # Keep the median of the collected samples (robust to outliers).
        if samples_h:
            horiz_vals.append(np.median(samples_h))
            vert_vals.append(np.median(samples_v))

    # -----------------------------------------------------------------
    # Derive user‑specific thresholds from the measured extremes.
    # -----------------------------------------------------------------
    # Center measurements are the first entries.
    h_center = horiz_vals[0]
    v_center = vert_vals[0]

    # Extremes from the directional poses.
    h_left  = min(horiz_vals[1:])   # Look LEFT
    h_right = max(horiz_vals[2:])   # Look RIGHT
    v_up    = min(vert_vals[3:])    # Look UP
    v_down  = max(vert_vals[4:])    # Look DOWN

    if np.isclose(v_up, v_down):
        vertical_height = (v_up + v_down) / 2.0
        v_up = max(0.0, vertical_height - 0.05)
        v_down = min(1.0, vertical_height + 0.05)

    # Small safety margin (≈5 % of the observed span) to avoid jitter.
    horiz_margin = 0.5 * (h_right - h_left)
    vert_margin  = 0.5 * (v_down - v_up)

    cfg = {
        "left_thresh": float(h_center - horiz_margin),   # left boundary
        "right_thresh": float(h_center + horiz_margin),   # right boundary
        "top_thresh":  float(v_center - vert_margin),    # top boundary
        "down_thresh":  float(v_center + vert_margin),    # bottom boundary
    }

    # Persist the calibration for future runs.
    with open("gaze_calibration_parameters.json", "w") as f:
        json.dump(cfg, f, indent=2)

    print("Calibration finished – thresholds saved to gaze_calibration_parameters.json")
    cv2.destroyWindow("Calibration")
    return cfg


# -------------------------------------------------------------------------
# Convenience loader – returns defaults if the JSON file is missing.
# -------------------------------------------------------------------------
def load_calibration() -> Dict[str, float]:
    try:
        with open("gaze_calibration_parameters.json", "r") as f:
            cfg = json.load(f)
        print("Loaded saved calibration.")
        return cfg
    except FileNotFoundError:
        print("No saved calibration – using generic defaults.")
        # Generic defaults that work reasonably for most faces.
        return {
            "left_thresh": 0.35,
            "right_thresh": 0.65,
            "top_thresh":  0.3,
            "down_thresh":  0.7,
        }