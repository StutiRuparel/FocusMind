import numpy as np
# ----- Exponential moving‑average for a 2‑D vector -----
class GazeSmoother:
    """EMA smoother for (dx, dy).  alpha ∈ (0,1] – higher = less lag."""
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha          # larger alpha = less smoothing
        self.state = None           # current smoothed (dx, dy)

    def update(self, vec):
        """vec = np.array([dx, dy])"""
        if self.state is None:
            self.state = np.asarray(vec, dtype=float)
        else:
            self.state = self.alpha * np.asarray(vec) + (1.0 - self.alpha) * self.state
        return self.state