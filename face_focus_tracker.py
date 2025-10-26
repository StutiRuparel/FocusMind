"""
AI-Powered Face Tracking Focus Monitor
Integrates face_track.py with FocusScore.py to automatically monitor user focus
and send real-time focus scores to the FocusMind backend.
"""

import argparse
import math
import time
import requests
import json
import threading
from collections import deque
from typing import Optional, Dict, Any

import cv2
import mediapipe as mp
import numpy as np

# Import existing modules
from ema_smoother import GazeSmoother
from face_tracking_utils import RIGHT_EYE, LEFT_EYE, get_eye_pts, eye_gaze_vector, landmarks_to_np_array
from calibration import calibrate_user, load_calibration
from FocusScore import compute_focus_score

# Face tracking constants
HEAD_POSE_LANDMARKS = [1, 152, 33, 263, 61, 291]
LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
LEFT_EYE_CORNERS = (33, 133)
RIGHT_EYE_CORNERS = (362, 263)
LEFT_EYE_VERTICAL = (159, 145)
RIGHT_EYE_VERTICAL = (386, 374)

MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),        # Nose tip
    (0.0, -63.6, -12.5),    # Chin
    (-43.3, 32.7, -26.0),   # Left eye outer corner
    (43.3, 32.7, -26.0),    # Right eye outer corner
    (-28.9, -28.9, -24.1),  # Left mouth corner
    (28.9, -28.9, -24.1),   # Right mouth corner
], dtype=np.float32)

class FaceFocusTracker:
    """
    Real-time face tracking focus monitor that integrates with FocusMind backend
    """
    
    def __init__(self, backend_url="http://localhost:8000", update_interval=2.0, show_video=True, force_calibrate=False):
        self.backend_url = backend_url
        self.update_interval = update_interval  # seconds between focus score updates
        self.show_video = show_video
        self.force_calibrate = force_calibrate
        self.running = False
        
        # Focus tracking state
        self.current_focus_score = 100.0
        self.last_update_time = 0
        self.last_quote_threshold = 100  # Track last threshold that triggered a quote
        
        # Video capture and MediaPipe
        self.cap = None
        self.face_mesh = None
        self.smoother = None
        self.cfg = None
        
        # Tracking variables
        self.eyes_closed_start_time = None
        self.eyes_closed_duration = 0.0
        self.blink_in_progress = False
        self.blink_count = 0
        self.session_start_time = 0
        
        # Rolling buffers for smoothing
        self.eye_horizontal_history = deque(maxlen=5)
        self.eye_vertical_history = deque(maxlen=5)
        self.head_pitch_history = deque(maxlen=5)
        self.head_yaw_history = deque(maxlen=5)
        
        # Face tracking data
        self.expression = None
        self.eyes_open_ratio = 0.0
        self.eye_direction = None
        self.head_direction = None
        self.gaze_label = ""
        
        print("🎯 FaceFocusTracker initialized")
        print(f"📡 Backend URL: {self.backend_url}")
        print(f"⏱️ Update interval: {self.update_interval}s")

    def initialize_camera(self, source=0):
        """Initialize camera and MediaPipe components"""
        try:
            # Open video source
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise RuntimeError(f"Cannot open video source: {source}")
            
            # Initialize MediaPipe Face-Mesh
            mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            
            self.smoother = GazeSmoother(alpha=0.3)
            
            # Try to load existing calibration first, or force calibration if requested
            if self.force_calibrate:
                print("🔧 Starting forced gaze calibration...")
                self.cfg = calibrate_user(
                    self.cap, self.face_mesh,
                    int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    get_eye_pts, eye_gaze_vector, smoothing_alpha=0.2
                )
                print("✅ Calibration completed")
            else:
                print("🔧 Loading gaze calibration...")
                try:
                    self.cfg = load_calibration()
                    print("✅ Loaded existing calibration")
                except (FileNotFoundError, json.JSONDecodeError):
                    print("⚠️ No calibration found, using default values")
                    # Default calibration values that work reasonably well
                    self.cfg = {
                        "left_thresh": -0.15,
                        "right_thresh": 0.15, 
                        "up_thresh": -0.10,
                        "down_thresh": 0.10,
                        "center_x": 0.0,
                        "center_y": 0.0
                    }
                    print("💡 Run with --calibrate flag to perform custom calibration")
            print("✅ Camera and MediaPipe initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize camera: {e}")
            return False

    def infer_expression(self, pts):
        """Simple expression inference from facial landmarks"""
        # Basic expression detection (simplified version)
        # This could be enhanced with more sophisticated analysis
        
        # Check if mouth is open (simple approximation)
        mouth_top = pts[13]    # Upper lip
        mouth_bottom = pts[14] # Lower lip
        mouth_opening = np.linalg.norm(mouth_top - mouth_bottom)
        
        if mouth_opening > 10:  # Threshold for mouth being open
            return "talking"
        
        return "neutral"

    def gaze_vector_to_label(self, vec):
        """Convert smoothed eye gaze vector to directional label"""
        if not self.cfg:
            return "Center"
            
        dx, dy = vec
        if dx < self.cfg["left_thresh"]:
            return "Right"
        if dx > self.cfg["right_thresh"]:
            return "Left"
        if dy < self.cfg["top_thresh"]:
            return "Down"
        if dy > self.cfg["down_thresh"]:
            return "Up"
        
        return "Center"

    def process_frame(self, frame):
        """Process a single video frame and extract focus metrics"""
        current_time = time.perf_counter()
        
        # Convert to RGB for MediaPipe
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        face_present = bool(results.multi_face_landmarks)
        
        if face_present:
            # Use first detected face
            lm = results.multi_face_landmarks[0].landmark
            pts = landmarks_to_np_array(lm, frame.shape)
            
            # Extract eye data
            right_pts = get_eye_pts(RIGHT_EYE, lm, w, h)
            left_pts = get_eye_pts(LEFT_EYE, lm, w, h)
            
            vec_r = eye_gaze_vector(right_pts)
            vec_l = eye_gaze_vector(left_pts)
            
            # Average and smooth gaze vectors
            raw_vec = (vec_r + vec_l) / 2.0
            smoothed_vec = self.smoother.update(raw_vec)
            self.gaze_label = self.gaze_vector_to_label(smoothed_vec)
            
            # Calculate eye openness ratio
            # This is a simplified calculation - you may want to enhance this
            left_eye_height = np.linalg.norm(pts[159] - pts[145])   # Left eye vertical
            right_eye_height = np.linalg.norm(pts[386] - pts[374])  # Right eye vertical
            avg_eye_height = (left_eye_height + right_eye_height) / 2
            
            # Normalize eye openness (you may need to adjust these thresholds)
            self.eyes_open_ratio = min(avg_eye_height / 8.0, 1.0)  # Adjust divisor as needed
            
            # Detect expression
            self.expression = self.infer_expression(pts)
            
            # Track eyes closed duration
            if self.eyes_open_ratio < 0.3:  # Eyes considered closed
                if self.eyes_closed_start_time is None:
                    self.eyes_closed_start_time = current_time
                self.eyes_closed_duration = current_time - self.eyes_closed_start_time
                
                if not self.blink_in_progress and self.eyes_closed_duration > 0.1:
                    self.blink_count += 1
                    self.blink_in_progress = True
            else:
                self.eyes_closed_start_time = None
                self.eyes_closed_duration = 0.0
                self.blink_in_progress = False
            
            # Calculate head pose (simplified)
            # In a full implementation, you'd use cv2.solvePnP for accurate head pose
            nose_tip = pts[1]
            chin = pts[152]
            left_eye = pts[33]
            right_eye = pts[263]
            
            # Simple head direction based on eye positions relative to nose
            head_center_x = (left_eye[0] + right_eye[0]) / 2
            head_tilt = (nose_tip[0] - head_center_x) / w * 100  # Normalize to percentage
            
            # Calculate pitch and yaw (simplified)
            head_pitch = 0.0  # Placeholder - would need proper 3D calculation
            head_yaw = head_tilt
            
            # Store in history for smoothing
            self.head_pitch_history.append(head_pitch)
            self.head_yaw_history.append(head_yaw)
            
            # Determine gaze away ratio
            gaze_away_ratio = 0.0 if self.gaze_label == "Center" else 1.0
            
        else:
            # No face detected
            self.eyes_open_ratio = 0.0
            self.eyes_closed_duration = 0.0
            self.expression = None
            self.gaze_label = "Away"
            gaze_away_ratio = 1.0
            head_pitch = 0.0
            head_yaw = 0.0
        
        # Calculate blink rate
        elapsed_minutes = max((current_time - self.session_start_time) / 60.0, 1e-6)
        blink_rate = (self.blink_count / elapsed_minutes) if self.blink_count else 0.0
        
        return {
            'face_present': face_present,
            'eyes_open_ratio': self.eyes_open_ratio,
            'eyes_closed_duration': self.eyes_closed_duration,
            'gaze_direction': self.gaze_label,
            'gaze_away_ratio': gaze_away_ratio,
            'head_pitch': head_pitch,
            'head_yaw': head_yaw,
            'blink_rate': blink_rate,
            'expression': self.expression
        }

    def compute_and_update_focus_score(self, metrics):
        """Compute focus score using FocusScore.py and update backend if needed"""
        try:
            # Use FocusScore.py to compute the focus score
            new_focus_score = compute_focus_score(
                face_present=metrics['face_present'],
                eyes_open_ratio=metrics['eyes_open_ratio'],
                eyes_closed_duration=metrics['eyes_closed_duration'],
                gaze_direction=metrics['gaze_direction'],
                gaze_away_ratio=metrics['gaze_away_ratio'],
                head_pitch=metrics['head_pitch'],
                head_yaw=metrics['head_yaw'],
                blink_rate=metrics['blink_rate'],
                keys_per_30s=0,  # Not tracking typing in this implementation
                typing_active=False,  # Not tracking typing in this implementation
                focus_trend=0.0,  # Could be enhanced to track trend
                prev_score=self.current_focus_score
            )
            
            # Only print score changes if significant (>2 point change)
            if abs(new_focus_score - self.current_focus_score) > 2.0:
                print(f"🎯 Focus score: {self.current_focus_score:.1f} → {new_focus_score:.1f}")
            
            self.current_focus_score = new_focus_score
            
            # Send update to backend
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.send_focus_update(new_focus_score)
                self.last_update_time = current_time
                
                # Check if we should trigger a motivational quote
                self.check_quote_thresholds(new_focus_score)
            
        except Exception as e:
            print(f"❌ Error computing focus score: {e}")

    def send_focus_update(self, focus_score):
        """Send focus score update to backend"""
        try:
            response = requests.post(f"{self.backend_url}/update-focus-score", 
                                   json={"focus_score": focus_score}, 
                                   timeout=1.0)
            if response.status_code == 200:
                print(f"📊 Focus score updated: {focus_score:.1f}")
            else:
                print(f"⚠️ Failed to update backend: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"🔌 Backend connection failed: {e}")

    def check_quote_thresholds(self, focus_score):
        """Check if focus score has crossed thresholds and trigger quotes accordingly"""
        thresholds = [80, 60, 50, 40, 20]  # Define your threshold levels
        
        for threshold in thresholds:
            # Check if we've crossed below this threshold since last quote
            if focus_score < threshold and self.last_quote_threshold >= threshold:
                self.trigger_motivational_quote(threshold)
                self.last_quote_threshold = threshold
                break
        
        # Reset threshold tracking if score improves significantly
        if focus_score > self.last_quote_threshold + 10:
            self.last_quote_threshold = 100

    def trigger_motivational_quote(self, threshold):
        """Trigger a motivational quote via the backend"""
        try:
            print(f"🚨 Focus dropped below {threshold}% - triggering motivational quote!")
            response = requests.post(f"{self.backend_url}/trigger-auto-motivation", 
                                   json={"threshold": threshold, "focus_score": self.current_focus_score}, 
                                   timeout=3.0)
            if response.status_code == 200:
                print("💪 Motivational quote triggered successfully")
            else:
                print(f"⚠️ Failed to trigger quote: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"🔌 Failed to trigger motivation: {e}")

    def draw_overlay(self, frame, metrics):
        """Draw focus tracking overlay on video frame"""
        if not self.show_video:
            return
            
        # Draw HUD information
        hud_lines = [
            f"Face: {'Yes' if metrics['face_present'] else 'No'}",
            f"Focus Score: {self.current_focus_score:.1f}%",
            f"Expression: {metrics['expression'] or '--'}",
            f"Eye openness: {metrics['eyes_open_ratio']:.2f}",
            f"Eyes closed: {metrics['eyes_closed_duration']:.1f}s",
            f"Blink rate: {metrics['blink_rate']:.1f}/min",
            f"Gaze: {metrics['gaze_direction']}"
        ]
        
        # Color code based on focus score
        if self.current_focus_score >= 80:
            color = (0, 255, 0)  # Green
        elif self.current_focus_score >= 60:
            color = (0, 255, 255)  # Yellow
        elif self.current_focus_score >= 40:
            color = (0, 165, 255)  # Orange
        else:
            color = (0, 0, 255)  # Red
        
        y = 30
        for line in hud_lines:
            cv2.putText(frame, line, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y += 30
        
        # Draw focus score bar
        bar_width = 300
        bar_height = 20
        bar_x = 30
        bar_y = y + 10
        
        # Background bar
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Fill bar based on focus score
        fill_width = int((self.current_focus_score / 100.0) * bar_width)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), color, -1)
        
        # Border
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)

    def run(self, source=0):
        """Main tracking loop"""
        print("🚀 Starting FaceFocusTracker...")
        
        if not self.initialize_camera(source):
            return False
        
        self.running = True
        self.session_start_time = time.perf_counter()
        
        print("📹 Face tracking started - monitoring focus...")
        print("Press ESC to stop tracking")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("📹 Video stream ended")
                    break
                
                # Process frame and get focus metrics
                metrics = self.process_frame(frame)
                
                # Compute and update focus score
                self.compute_and_update_focus_score(metrics)
                
                # Draw overlay if video display is enabled
                if self.show_video:
                    self.draw_overlay(frame, metrics)
                    cv2.imshow("FocusMind - AI Focus Tracker", frame)
                    
                    # Check for ESC key
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping face tracking...")
        finally:
            self.stop()
        
        return True

    def stop(self):
        """Stop the tracker and cleanup resources"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.show_video:
            cv2.destroyAllWindows()
        print("🛑 FaceFocusTracker stopped")

def main():
    parser = argparse.ArgumentParser(description="AI-Powered Face Focus Tracker for FocusMind")
    parser.add_argument("--source", default="0", help="Video source (0 for webcam, or video file path)")
    parser.add_argument("--backend", default="http://localhost:8000", help="FocusMind backend URL")
    parser.add_argument("--interval", type=float, default=20.0, help="Focus score update interval (seconds)")
    parser.add_argument("--no-video", action="store_true", help="Run without video display (headless)")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode without camera (simulates focus tracking)")
    parser.add_argument("--calibrate", action="store_true", help="Force gaze calibration (otherwise uses defaults/saved)")
    
    args = parser.parse_args()
    
    # Convert source to int if it's a digit
    source = int(args.source) if args.source.isdigit() else args.source
    
    # Create and run tracker
    tracker = FaceFocusTracker(
        backend_url=args.backend,
        update_interval=args.interval,
        show_video=not args.no_video,
        force_calibrate=args.calibrate
    )
    
    success = tracker.run(source)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())