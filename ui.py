"""TaskFlow user interface — sidebar, dashboard, task cards, and dialogs."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from task_manager import Task, TaskManager
from utils import (
    APP_TITLE,
    CATEGORIES,
    COLORS,
    FONTS,
    PRIORITIES,
    SIDEBAR_ITEMS,
    SORT_OPTIONS,
    WINDOW_DEFAULT,
    WINDOW_MIN,
    animate_progress,
    center_window,
    fade_in_widget,
    fade_out_and_destroy,
    format_display_date,
    format_due_date,
    get_greeting,
    parse_date,
    priority_color,
    slide_fade_in,
)


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------

class RoundedButton(tk.Canvas):
    """Canvas-based button with hover effect and rounded appearance."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg_color: str = COLORS["primary"],
        hover_color: str = COLORS["accent"],
        fg_color: str = "#FFFFFF",
        width: int = 140,
        height: int = 36,
        font: tuple = FONTS["button"],
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=parent.cget("bg") if "bg" in parent.keys() else COLORS["background"],
            **kwargs,
        )
        self._text = text
        self._command = command
        self._bg = bg_color
        self._hover = hover_color
        self._fg = fg_color
        self._font = font
        self._enabled = True
        self._draw(self._bg)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, color: str) -> None:
        self.delete("all")
        w, h = int(self.cget("width")), int(self.cget("height"))
        radius = 8
        self._round_rect(2, 2, w - 2, h - 2, radius, fill=color, outline=color)
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg, font=self._font)

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs) -> None:
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, _event=None) -> None:
        if self._enabled:
            self._draw(self._hover)

    def _on_leave(self, _event=None) -> None:
        if self._enabled:
            self._draw(self._bg)

    def _on_click(self, _event=None) -> None:
        if self._enabled:
            self._command()


class SidebarButton(tk.Frame):
    """Navigation item in the left sidebar."""

    def __init__(
        self,
        parent: tk.Widget,
        key: str,
        label: str,
        icon: str,
        command: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=COLORS["sidebar"], cursor="hand2", **kwargs)
        self.key = key
        self._command = command
        self._active = False

        self.label = tk.Label(
            self,
            text=f"  {icon}   {label}",
            font=FONTS["sidebar"],
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
            anchor="w",
            padx=16,
            pady=12,
        )
        self.label.pack(fill="x")

        for widget in (self, self.label):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, _event=None) -> None:
        self._command()

    def _enter(self, _event=None) -> None:
        if not self._active:
            self.configure(bg=COLORS["sidebar_hover"])
            self.label.configure(bg=COLORS["sidebar_hover"])

    def _leave(self, _event=None) -> None:
        bg = COLORS["sidebar_active"] if self._active else COLORS["sidebar"]
        self.configure(bg=bg)
        self.label.configure(bg=bg)

    def set_active(self, active: bool) -> None:
        self._active = active
        bg = COLORS["sidebar_active"] if active else COLORS["sidebar"]
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=COLORS["primary"] if active else COLORS["text"])


class TaskCard(tk.Frame):
    """Modern card widget for a single task."""

    def __init__(
        self,
        parent: tk.Widget,
        task: Task,
        on_toggle: Callable[[str], None],
        on_delete: Callable[[str], None],
        on_edit: Callable[[str], None],
        on_select: Callable[[str, bool], None],
        **kwargs,
    ) -> None:
        bg = COLORS["completed"] if task.completed else COLORS["card"]
        super().__init__(
            parent,
            bg=bg,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=16,
            pady=12,
            **kwargs,
        )
        self.task = task
        self._on_toggle = on_toggle
        self._on_delete = on_delete
        self._on_edit = on_edit
        self._on_select = on_select
        self._selected = tk.BooleanVar(value=False)

        self._build()

    def _build(self) -> None:
        bg = self.cget("bg")
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")

        check_text = "☑" if self.task.completed else "☐"
        self.check_btn = tk.Label(
            row,
            text=check_text,
            font=("Segoe UI", 16),
            bg=bg,
            fg=COLORS["primary"],
            cursor="hand2",
        )
        self.check_btn.pack(side="left", padx=(0, 12))
        self.check_btn.bind("<Button-1>", lambda _e: self._on_toggle(self.task.id))

        info = tk.Frame(row, bg=bg)
        info.pack(side="left", fill="x", expand=True)

        title_font = FONTS["body_bold"]
        title_fg = COLORS["text_muted"] if self.task.completed else COLORS["text"]
        display_font = (
            (title_font[0], title_font[1], "bold", "overstrike")
            if self.task.completed
            else title_font
        )
        self.title_label = tk.Label(
            info,
            text=self.task.title,
            font=display_font,
            bg=bg,
            fg=title_fg,
            anchor="w",
        )
        self.title_label.pack(fill="x")
        self.title_label.bind("<Double-Button-1>", lambda _e: self._on_edit(self.task.id))

        meta = tk.Frame(info, bg=bg)
        meta.pack(fill="x", pady=(6, 0))

        self._badge(meta, self.task.category, COLORS["border"], COLORS["text_muted"])
        self._badge(meta, self.task.priority, priority_color(self.task.priority), "#FFFFFF")
        self._badge(meta, format_due_date(self.task.due_date), COLORS["accent"], COLORS["text"])

        if self.task.important:
            self._badge(meta, "Important", COLORS["warning"], "#FFFFFF")

        select_cb = tk.Checkbutton(
            row,
            variable=self._selected,
            bg=bg,
            activebackground=bg,
            highlightthickness=0,
            command=lambda: self._on_select(self.task.id, self._selected.get()),
        )
        select_cb.pack(side="right", padx=(8, 0))

        del_btn = tk.Label(
            row,
            text="✕",
            font=("Segoe UI", 12, "bold"),
            bg=bg,
            fg=COLORS["danger"],
            cursor="hand2",
        )
        del_btn.pack(side="right", padx=(8, 0))
        del_btn.bind("<Enter>", lambda _e: del_btn.configure(fg=COLORS["danger_hover"]))
        del_btn.bind("<Leave>", lambda _e: del_btn.configure(fg=COLORS["danger"]))
        del_btn.bind("<Button-1>", lambda _e: self._on_delete(self.task.id))

    def _badge(self, parent: tk.Widget, text: str, bg: str, fg: str) -> None:
        lbl = tk.Label(
            parent,
            text=f" {text} ",
            font=FONTS["small"],
            bg=bg,
            fg=fg,
            padx=4,
            pady=2,
        )
        lbl.pack(side="left", padx=(0, 6))

    def is_selected(self) -> bool:
        return self._selected.get()

    def set_selected(self, value: bool) -> None:
        self._selected.set(value)

    def refresh(self, task: Task) -> None:
        """Rebuild card after task update."""
        for child in self.winfo_children():
            child.destroy()
        self.task = task
        bg = COLORS["completed"] if task.completed else COLORS["card"]
        self.configure(bg=bg)
        self._build()


class NotificationToast(tk.Frame):
    """Subtle bottom-right notification banner."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, bg=COLORS["notification_bg"], **kwargs)
        self.label = tk.Label(
            self,
            text="",
            font=FONTS["body"],
            bg=COLORS["notification_bg"],
            fg=COLORS["notification_text"],
            padx=20,
            pady=10,
        )
        self.label.pack()
        self.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-60)
        self.place_forget()

    def show(self, message: str, duration: int = 2500) -> None:
        self.label.configure(text=message)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-60)
        self.after(duration, self.place_forget)


class TaskDialog(tk.Toplevel):
    """Modal dialog for adding or editing a task."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        on_submit: Callable[[dict], None],
        task: Optional[Task] = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(bg=COLORS["background"])
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._on_submit = on_submit
        self._result: Optional[dict] = None

        w, h = 460, 420
        center_window(self, w, h)

        container = tk.Frame(self, bg=COLORS["background"], padx=24, pady=24)
        container.pack(fill="both", expand=True)

        tk.Label(container, text=title, font=FONTS["heading"], bg=COLORS["background"], fg=COLORS["text"]).pack(anchor="w")

        self.title_var = tk.StringVar(value=task.title if task else "")
        self.category_var = tk.StringVar(value=task.category if task else CATEGORIES[0])
        self.priority_var = tk.StringVar(value=task.priority if task else PRIORITIES[1])
        self.due_var = tk.StringVar(value=task.due_date or "" if task else "")
        self.important_var = tk.BooleanVar(value=task.important if task else False)
        self.notes_var = tk.StringVar(value=task.notes if task else "")

        self._field(container, "Title *", self.title_var)
        self._combo(container, "Category", self.category_var, CATEGORIES)
        self._combo(container, "Priority", self.priority_var, PRIORITIES)
        self._field(container, "Due Date (YYYY-MM-DD)", self.due_var)

        tk.Checkbutton(
            container,
            text="Mark as important",
            variable=self.important_var,
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["text"],
            activebackground=COLORS["background"],
        ).pack(anchor="w", pady=(4, 8))

        tk.Label(container, text="Notes", font=FONTS["body_bold"], bg=COLORS["background"], fg=COLORS["text"]).pack(anchor="w")
        self.notes_text = tk.Text(container, height=3, font=FONTS["body"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
        self.notes_text.pack(fill="x", pady=(4, 12))
        if task and task.notes:
            self.notes_text.insert("1.0", task.notes)

        btn_row = tk.Frame(container, bg=COLORS["background"])
        btn_row.pack(fill="x", pady=(8, 0))
        RoundedButton(btn_row, "Cancel", self.destroy, bg_color=COLORS["border"], hover_color="#DDE3DF", fg_color=COLORS["text"], width=120).pack(side="right", padx=(8, 0))
        RoundedButton(btn_row, "Save", self._save, width=120).pack(side="right")

        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _field(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        tk.Label(parent, text=label, font=FONTS["body_bold"], bg=COLORS["background"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        entry = tk.Entry(parent, textvariable=variable, font=FONTS["body"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
        entry.pack(fill="x", ipady=6)

    def _combo(self, parent: tk.Widget, label: str, variable: tk.StringVar, values: list[str]) -> None:
        tk.Label(parent, text=label, font=FONTS["body_bold"], bg=COLORS["background"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", font=FONTS["body"]).pack(fill="x")

    def _save(self) -> None:
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Task title is required.", parent=self)
            return

        due = self.due_var.get().strip()
        if due and parse_date(due) is None:
            messagebox.showwarning("Validation", "Invalid due date. Use YYYY-MM-DD.", parent=self)
            return

        payload = {
            "title": title,
            "category": self.category_var.get(),
            "priority": self.priority_var.get(),
            "due_date": due or None,
            "important": self.important_var.get(),
            "notes": self.notes_text.get("1.0", "end").strip(),
        }
        self._on_submit(payload)
        self.destroy()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class TaskFlowApp:
    """Main TaskFlow application window."""

    def __init__(self, manager: TaskManager) -> None:
        self.manager = manager
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.configure(bg=COLORS["background"])
        self.root.minsize(*WINDOW_MIN)

        self.current_view = "all"
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar(value="All")
        self.status_filter_var = tk.StringVar(value="All")
        self.sort_var = tk.StringVar(value=SORT_OPTIONS[0])
        self.selected_ids: set[str] = set()
        self.sidebar_buttons: dict[str, SidebarButton] = {}
        self.task_cards: list[TaskCard] = []

        self._configure_styles()
        self._build_layout()
        center_window(self.root, *WINDOW_DEFAULT)
        self._bind_events()
        self.refresh_tasks(animate=False)
        self._update_header()
        fade_in_widget(self.main_frame, on_complete=lambda: self.notification.show("Welcome to TaskFlow"))

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=COLORS["card"], background=COLORS["card"])
        style.configure("Horizontal.TProgressbar", troughcolor=COLORS["border"], background=COLORS["primary"], thickness=8)

    def _build_layout(self) -> None:
        self.main_frame = tk.Frame(self.root, bg=COLORS["background"])
        self.main_frame.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(self.main_frame, bg=COLORS["sidebar"], width=220, highlightbackground=COLORS["border"], highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Label(sidebar, text="TaskFlow", font=FONTS["title"], bg=COLORS["sidebar"], fg=COLORS["primary"], pady=24, padx=16)
        brand.pack(anchor="w")

        tk.Label(sidebar, text="  NAVIGATION", font=FONTS["small"], bg=COLORS["sidebar"], fg=COLORS["text_muted"], anchor="w").pack(fill="x", padx=8)

        for key, label, icon in SIDEBAR_ITEMS:
            btn = SidebarButton(sidebar, key, label, icon, lambda k=key: self._switch_view(k))
            btn.pack(fill="x", padx=8, pady=2)
            self.sidebar_buttons[key] = btn

        self.sidebar_buttons["all"].set_active(True)

        # Content area
        content = tk.Frame(self.main_frame, bg=COLORS["background"])
        content.pack(side="left", fill="both", expand=True)

        # Header
        self.header = tk.Frame(content, bg=COLORS["background"], padx=28, pady=20)
        self.header.pack(fill="x")

        self.greeting_label = tk.Label(self.header, text="", font=FONTS["title"], bg=COLORS["background"], fg=COLORS["text"])
        self.greeting_label.pack(anchor="w")

        self.date_label = tk.Label(self.header, text="", font=FONTS["body"], bg=COLORS["background"], fg=COLORS["text_muted"])
        self.date_label.pack(anchor="w", pady=(4, 12))

        stats_row = tk.Frame(self.header, bg=COLORS["background"])
        stats_row.pack(fill="x")

        self.stats_label = tk.Label(stats_row, text="", font=FONTS["subheading"], bg=COLORS["background"], fg=COLORS["text"])
        self.stats_label.pack(side="left")

        progress_wrap = tk.Frame(stats_row, bg=COLORS["background"])
        progress_wrap.pack(side="right", fill="x", expand=True, padx=(40, 0))

        self.progress_canvas = tk.Canvas(progress_wrap, height=10, bg=COLORS["border"], highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(8, 0))
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill=COLORS["primary"], outline="")

        self.progress_label = tk.Label(progress_wrap, text="", font=FONTS["small"], bg=COLORS["background"], fg=COLORS["text_muted"], anchor="e")
        self.progress_label.pack(fill="x", pady=(4, 0))

        # Filters toolbar
        filters = tk.Frame(
    content,
    bg=COLORS["background"]
)
        filters.pack(fill="x")

        tk.Label(filters, text="Search", font=FONTS["small"], bg=COLORS["background"], fg=COLORS["text_muted"]).pack(side="left")
        search_entry = tk.Entry(filters, textvariable=self.search_var, font=FONTS["body"], width=22, relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
        search_entry.pack(side="left", padx=(8, 20), ipady=4)

        tk.Label(filters, text="Category", font=FONTS["small"], bg=COLORS["background"], fg=COLORS["text_muted"]).pack(side="left")
        ttk.Combobox(filters, textvariable=self.category_filter_var, values=["All"] + CATEGORIES, state="readonly", width=12).pack(side="left", padx=(8, 20))

        tk.Label(filters, text="Status", font=FONTS["small"], bg=COLORS["background"], fg=COLORS["text_muted"]).pack(side="left")
        ttk.Combobox(filters, textvariable=self.status_filter_var, values=["All", "Active", "Completed"], state="readonly", width=10).pack(side="left", padx=(8, 20))

        tk.Label(filters, text="Sort", font=FONTS["small"], bg=COLORS["background"], fg=COLORS["text_muted"]).pack(side="left")
        ttk.Combobox(filters, textvariable=self.sort_var, values=SORT_OPTIONS, state="readonly", width=12).pack(side="left", padx=(8, 0))

        # Scrollable task list
        list_wrap = tk.Frame(content, bg=COLORS["background"], padx=28)
        list_wrap.pack(fill="both", expand=True, pady=(8, 0))

        self.canvas = tk.Canvas(list_wrap, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=self.canvas.yview)
        self.task_container = tk.Frame(self.canvas, bg=COLORS["background"])

        self.task_container.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.task_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.empty_label = tk.Label(self.task_container, text="No tasks yet. Click '+ Add Task' to get started.", font=FONTS["body"], bg=COLORS["background"], fg=COLORS["text_muted"], pady=40)
        self.empty_label.pack()

        # Bottom toolbar
        toolbar = tk.Frame(content, bg=COLORS["card"], highlightbackground=COLORS["border"], highlightthickness=1, padx=20, pady=12)
        toolbar.pack(fill="x", side="bottom")

        RoundedButton(toolbar, "+ Add Task", self._add_task, width=130).pack(side="left", padx=(0, 8))
        RoundedButton(toolbar, "Delete Selected", self._delete_selected, bg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], width=150).pack(side="left", padx=8)
        RoundedButton(toolbar, "Mark Complete", self._mark_selected_complete, bg_color=COLORS["accent"], hover_color=COLORS["primary"], width=150).pack(side="left", padx=8)
        RoundedButton(toolbar, "Clear Completed", self._clear_completed, bg_color=COLORS["border"], hover_color="#DDE3DF", fg_color=COLORS["text"], width=150).pack(side="left", padx=8)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", font=FONTS["small"], bg=COLORS["sidebar"], fg=COLORS["text_muted"], anchor="w", padx=12, pady=6)
        self.status_bar.pack(fill="x", side="bottom")

        self.notification = NotificationToast(content)

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_: self.refresh_tasks())
        self.category_filter_var.trace_add("write", lambda *_: self.refresh_tasks())
        self.status_filter_var.trace_add("write", lambda *_: self.refresh_tasks())
        self.sort_var.trace_add("write", lambda *_: self.refresh_tasks())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _switch_view(self, view: str) -> None:
        if view == "settings":
            self._show_settings()
            return
        self.current_view = view
        for key, btn in self.sidebar_buttons.items():
            btn.set_active(key == view)
        self.refresh_tasks()
        self._set_status(f"Viewing: {view.replace('_', ' ').title()}")

    def _show_settings(self) -> None:
        stats = self.manager.get_stats()
        messagebox.showinfo(
            "Settings",
            f"TaskFlow Settings\n\n"
            f"Data file: {self.manager.data_path}\n"
            f"Total tasks: {stats['total']}\n"
            f"Auto-save: Enabled\n\n"
            f"Categories: {', '.join(CATEGORIES)}\n"
            f"Priorities: {', '.join(PRIORITIES)}",
            parent=self.root,
        )

    def _update_header(self) -> None:
        stats = self.manager.get_stats()
        self.greeting_label.configure(text=f"{get_greeting()}!")
        self.date_label.configure(text=format_display_date())
        self.stats_label.configure(
            text=f"{stats['total']} tasks · {stats['completed']} completed · {stats['remaining']} remaining"
        )
        self.progress_label.configure(text=f"{stats['percentage']}% complete")

        canvas_width = max(self.progress_canvas.winfo_width(), 200)
        target = (stats["percentage"] / 100) * canvas_width if stats["total"] else 0
        animate_progress(self.progress_canvas, self.progress_bar, target, canvas_width)

    def refresh_tasks(self, animate: bool = True) -> None:
        """Rebuild the task list from the manager."""
        for card in self.task_cards:
            card.destroy()
        self.task_cards.clear()
        self.selected_ids.clear()

        if hasattr(self, "empty_label") and self.empty_label.winfo_exists():
            self.empty_label.destroy()

        tasks = self.manager.get_all_tasks(
            view=self.current_view,
            search=self.search_var.get(),
            category_filter=self.category_filter_var.get(),
            status_filter=self.status_filter_var.get(),
            sort_by=self.sort_var.get(),
        )

        if not tasks:
            self.empty_label = tk.Label(
                self.task_container,
                text="No tasks match your filters." if self.manager.tasks else "No tasks yet. Click '+ Add Task' to get started.",
                font=FONTS["body"],
                bg=COLORS["background"],
                fg=COLORS["text_muted"],
                pady=40,
            )
            self.empty_label.pack()
        else:
            for i, task in enumerate(tasks):
                card = TaskCard(
                    self.task_container,
                    task,
                    on_toggle=self._toggle_task,
                    on_delete=self._delete_task,
                    on_edit=self._edit_task,
                    on_select=self._select_task,
                )
                card.pack(fill="x", pady=6, padx=2)
                self.task_cards.append(card)
                if animate:
                    self.root.after(i * 40, lambda c=card: slide_fade_in(c, 0))

        self._update_header()

    def _select_task(self, task_id: str, selected: bool) -> None:
        if selected:
            self.selected_ids.add(task_id)
        else:
            self.selected_ids.discard(task_id)

    def _add_task(self) -> None:
        def submit(data: dict) -> None:
            task = Task(**data)
            ok, msg = self.manager.add_task(task)
            if ok:
                self.refresh_tasks()
                self.notification.show(msg)
                self._set_status(msg)
            else:
                messagebox.showwarning("Add Task", msg, parent=self.root)

        TaskDialog(self.root, "Add New Task", submit)

    def _edit_task(self, task_id: str) -> None:
        task = self.manager.get_task(task_id)
        if not task:
            return

        def submit(data: dict) -> None:
            ok, msg = self.manager.update_task(task_id, **data)
            if ok:
                self.refresh_tasks()
                self.notification.show(msg)
                self._set_status(msg)
            else:
                messagebox.showwarning("Edit Task", msg, parent=self.root)

        TaskDialog(self.root, "Edit Task", submit, task=task)

    def _toggle_task(self, task_id: str) -> None:
        ok, msg = self.manager.toggle_complete(task_id)
        if ok:
            task = self.manager.get_task(task_id)
            for card in self.task_cards:
                if card.task.id == task_id and task:
                    card.refresh(task)
                    if task.completed:
                        self.notification.show("Task completed!")
                    break
            self._update_header()
            self._set_status(msg)

    def _delete_task(self, task_id: str) -> None:
        card = next((c for c in self.task_cards if c.task.id == task_id), None)
        if card is None:
            return

        def after_destroy() -> None:
            ok, msg = self.manager.delete_task(task_id)
            if ok:
                self.task_cards.remove(card)
                self.selected_ids.discard(task_id)
                self.refresh_tasks(animate=False)
                self.notification.show(msg)
                self._set_status(msg)

        fade_out_and_destroy(card, on_destroy=after_destroy)

    def _delete_selected(self) -> None:
        ids = [c.task.id for c in self.task_cards if c.is_selected()]
        if not ids:
            messagebox.showinfo("Delete Selected", "No tasks selected.", parent=self.root)
            return
        if not messagebox.askyesno("Confirm", f"Delete {len(ids)} selected task(s)?", parent=self.root):
            return
        count = self.manager.delete_tasks(ids)
        self.refresh_tasks()
        self.notification.show(f"Deleted {count} task(s).")
        self._set_status(f"Deleted {count} task(s).")

    def _mark_selected_complete(self) -> None:
        ids = [c.task.id for c in self.task_cards if c.is_selected()]
        if not ids:
            messagebox.showinfo("Mark Complete", "No tasks selected.", parent=self.root)
            return
        count = self.manager.mark_complete(ids, completed=True)
        self.refresh_tasks()
        self.notification.show(f"Marked {count} task(s) complete.")
        self._set_status(f"Marked {count} task(s) complete.")

    def _clear_completed(self) -> None:
        count = self.manager.clear_completed()
        if count:
            self.refresh_tasks()
            self.notification.show(f"Cleared {count} completed task(s).")
            self._set_status(f"Cleared {count} completed task(s).")
        else:
            messagebox.showinfo("Clear Completed", "No completed tasks to clear.", parent=self.root)

    def _set_status(self, text: str) -> None:
        self.status_bar.configure(text=text)

    def _on_close(self) -> None:
        self.manager._save()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
