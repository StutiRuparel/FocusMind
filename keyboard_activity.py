from pynput import keyboard
import time
import threading

keystrokes_detected = []  # Store timestamps of each keystroke
keys_per_30s = 0          # Keystrokes detected in last 30 seconds
typing_active = False     # True/False if typing detected recently

def update_typing_activity():
    global keys_per_30s, typing_active
    window_seconds = 30
    while True:
        now = time.time()
        # Remove outdated keystrokes
        keystrokes_detected[:] = [t for t in keystrokes_detected if now - t <= window_seconds]
        keys_per_30s = len(keystrokes_detected)
        typing_active = keys_per_30s > 0
        #print(f"Typing Activity | keys_per_30s: {keys_per_30s} | typing_active: {typing_active}")
        time.sleep(1)

def on_press(key):
    current_time = time.time()
    keystrokes_detected.append(current_time)

def on_release(key):
    if key == keyboard.Key.esc:
        #print("Exiting...")
        return False

# Thread for ongoing typing activity check
activity_thread = threading.Thread(target=update_typing_activity, daemon=True)
activity_thread.start()

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
listener.join()