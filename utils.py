"""Utility helpers for TaskFlow — colors, fonts, dates, and animations."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, date
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

COLORS = {
    "background": "#F8FAF7",
    "card": "#FFFFFF",
    "primary": "#6BAA75",
    "accent": "#8CCF97",
    "completed": "#CFEAD6",
    "text": "#2F3E46",
    "text_muted": "#5C6B73",
    "border": "#E8ECEA",
    "sidebar": "#FFFFFF",
    "sidebar_hover": "#EEF5F0",
    "sidebar_active": "#E2F0E5",
    "danger": "#E07A5F",
    "danger_hover": "#D46A4F",
    "warning": "#F4A261",
    "priority_high": "#E07A5F",
    "priority_medium": "#F4A261",
    "priority_low": "#6BAA75",
    "shadow": "#D8DDD9",
    "notification_bg": "#2F3E46",
    "notification_text": "#FFFFFF",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 11),
    "body_bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 9),
    "sidebar": ("Segoe UI", 12),
    "button": ("Segoe UI", 10, "bold"),
}

PRIORITIES = ["Low", "Medium", "High"]
CATEGORIES = ["Personal", "School", "Work", "Shopping", "Coding", "Other"]
SORT_OPTIONS = ["Due Date", "Priority", "Title", "Created"]

SIDEBAR_ITEMS = [
    ("all", "All Tasks", "📋"),
    ("today", "Today", "📅"),
    ("important", "Important", "⭐"),
    ("completed", "Completed", "✅"),
    ("settings", "Settings", "⚙"),
]

WINDOW_DEFAULT = (1000, 700)
WINDOW_MIN = (900, 650)
APP_TITLE = "TaskFlow"


# ---------------------------------------------------------------------------
# Date & greeting helpers
# ---------------------------------------------------------------------------

def get_greeting() -> str:
    """Return a time-of-day greeting string."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def format_display_date(d: Optional[date] = None) -> str:
    """Format a date for the dashboard header."""
    d = d or date.today()
    return d.strftime("%A, %B %d, %Y")


def parse_date(value: str) -> Optional[date]:
    """Parse YYYY-MM-DD; return None on invalid input."""
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def format_due_date(value: Optional[str]) -> str:
    """Human-readable due date label for task cards."""
    if not value:
        return "No due date"
    parsed = parse_date(value)
    if parsed is None:
        return "Invalid date"
    today = date.today()
    if parsed == today:
        return "Due today"
    if parsed < today:
        return f"Overdue · {parsed.strftime('%b %d')}"
    return parsed.strftime("%b %d, %Y")


def priority_color(priority: str) -> str:
    """Map priority level to theme color."""
    return {
        "High": COLORS["priority_high"],
        "Medium": COLORS["priority_medium"],
        "Low": COLORS["priority_low"],
    }.get(priority, COLORS["primary"])


def priority_weight(priority: str) -> int:
    """Numeric weight for sorting by priority."""
    return {"High": 0, "Medium": 1, "Low": 2}.get(priority, 3)


# ---------------------------------------------------------------------------
# Window helpers
# ---------------------------------------------------------------------------

def center_window(window: tk.Tk | tk.Toplevel, width: int, height: int) -> None:
    """Center a window on the primary screen."""
    window.update_idletasks()
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


# ---------------------------------------------------------------------------
# Animation helpers (Tkinter after()-based)
# ---------------------------------------------------------------------------

def fade_in_widget(
    widget: tk.Widget,
    steps: int = 12,
    interval: int = 30,
    on_complete: Optional[Callable[[], None]] = None,
) -> None:
    """Simulate fade-in by stepping background toward target color."""
    target = COLORS["background"]
    start = "#FFFFFF"
    r1, g1, b1 = _hex_to_rgb(start)
    r2, g2, b2 = _hex_to_rgb(target)

    def step(i: int = 0) -> None:
        if i > steps:
            if on_complete:
                on_complete()
            return
        t = i / steps
        color = _rgb_to_hex(
            int(r1 + (r2 - r1) * t),
            int(g1 + (g2 - g1) * t),
            int(b1 + (b2 - b1) * t),
        )
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
        widget.after(interval, lambda: step(i + 1))

    step()


def animate_progress(
    canvas: tk.Canvas,
    bar_id: int,
    target_width: float,
    max_width: float,
    steps: int = 20,
    interval: int = 25,
) -> None:
    """Smoothly animate a progress bar rectangle width."""
    current = 0.0
    increment = target_width / steps

    def step(i: int = 0) -> None:
        nonlocal current
        if i >= steps:
            canvas.coords(bar_id, 0, 0, target_width, 8)
            return
        current += increment
        canvas.coords(bar_id, 0, 0, min(current, target_width), 8)
        canvas.after(interval, lambda: step(i + 1))

    step()


def slide_fade_in(
    widget: tk.Widget,
    parent_height: int,
    steps: int = 10,
    interval: int = 25,
    on_complete: Optional[Callable[[], None]] = None,
) -> None:
    """Slide a widget in from slightly above with opacity-like effect."""
    try:
        widget.pack_info()
        use_grid = False
    except tk.TclError:
        use_grid = True

    original_pady = 6

    def step(i: int = 0) -> None:
        if i >= steps:
            if on_complete:
                on_complete()
            return
        offset = int((steps - i) * 2)
        if not use_grid:
            widget.pack_configure(pady=(original_pady + offset, original_pady))
        widget.after(interval, lambda: step(i + 1))

    step()


def fade_out_and_destroy(
    widget: tk.Widget,
    steps: int = 8,
    interval: int = 30,
    on_destroy: Optional[Callable[[], None]] = None,
) -> None:
    """Fade task card out then destroy it."""
    base = COLORS["card"]

    def step(i: int = 0) -> None:
        if i >= steps:
            widget.destroy()
            if on_destroy:
                on_destroy()
            return
        factor = 1 - (i / steps)
        r, g, b = _hex_to_rgb(base)
        faded = _rgb_to_hex(
            min(255, int(r + (255 - r) * (1 - factor))),
            min(255, int(g + (255 - g) * (1 - factor))),
            min(255, int(b + (255 - b) * (1 - factor))),
        )
        try:
            widget.configure(bg=faded)
            for child in widget.winfo_children():
                try:
                    child.configure(bg=faded)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass
        widget.after(interval, lambda: step(i + 1))

    step()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"
