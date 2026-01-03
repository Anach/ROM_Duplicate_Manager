"""Icon handling utilities for ROM Duplicate Manager."""

import base64
import tkinter as tk
from typing import Optional

# Application icon data
PACMAN_ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABq0lEQVR4nO2bYZKDIAyFkzdcpvc/TI/DjrvT3Z1WBSQJifD9q6LvvQwgxZFosVgsFvPClmL5Sbm2LT9svLGn0COKwV5DWxWDowTXKgQoYHhJPUQML6nLow2MHhK4Q/geP7AU0+aKL1iIWNLqL2kZ4cfnsfwkd0Cjunvhz44PXXKT8E23kDn/NWXmYT2h5skAzfDf1779frWzoMY3pMRaQ1kVobsA2fms3+sf0oLvY35vDrCkNA8kFdHBoVuWxulO3f8o9Jbj6BxLFqBlYpN8FPbsDSQ5Gz+haoogEV59QyRf7P6lcL3ht+BXwh/lSX12DsXE/wtobYwmUsJTNz/VIIdPAKt3Aqo9wHNoVwXgQcF/9cnREBhRDJAjtqJbFx7kkFchJIthug6Q5L9xjSECCoTGEOGSIDmnt1eAglMzX5ydA92IK0OEa25KgSkNEdDNMd8UjQa8r9V7mX4IlECxReBeIPZuMGIRav1C46ajafEJmhy0XuC9F7T6g4WIFVd8wVJMk6t+WEI88hY6PJgYqQsZK/ZFkNJjUmDa7wX2mPKLkUjfDC0WiwXNzBcIwbWZE7SXrAAAAABJRU5ErkJggg=="


def get_icon_photo() -> Optional[tk.PhotoImage]:
    """Convert base64 icon to tkinter PhotoImage.

    Returns:
        PhotoImage object or None if loading fails
    """
    try:
        icon_data = base64.b64decode(PACMAN_ICON_BASE64)
        return tk.PhotoImage(data=icon_data)
    except Exception as e:
        print(f"Failed to load icon: {e}")
        return None