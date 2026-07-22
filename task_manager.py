"""Business logic and persistence for TaskFlow tasks."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from utils import CATEGORIES, PRIORITIES, priority_weight


class Task:
    """Represents a single to-do item."""

    __slots__ = (
        "id",
        "title",
        "category",
        "priority",
        "due_date",
        "completed",
        "important",
        "created_at",
        "notes",
    )

    def __init__(
        self,
        title: str,
        category: str = "Personal",
        priority: str = "Medium",
        due_date: Optional[str] = None,
        completed: bool = False,
        important: bool = False,
        task_id: Optional[str] = None,
        created_at: Optional[str] = None,
        notes: str = "",
    ) -> None:
        self.id = task_id or str(uuid.uuid4())
        self.title = title.strip()
        self.category = category if category in CATEGORIES else "Other"
        self.priority = priority if priority in PRIORITIES else "Medium"
        self.due_date = due_date
        self.completed = completed
        self.important = important
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self.notes = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed,
            "important": self.important,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            title=str(data.get("title", "")),
            category=str(data.get("category", "Personal")),
            priority=str(data.get("priority", "Medium")),
            due_date=data.get("due_date"),
            completed=bool(data.get("completed", False)),
            important=bool(data.get("important", False)),
            task_id=str(data.get("id", uuid.uuid4())),
            created_at=data.get("created_at"),
            notes=str(data.get("notes", "")),
        )


class TaskManager:
    """Manages task CRUD, filtering, sorting, and JSON persistence."""

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.tasks: list[Task] = []
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load tasks from JSON; handle missing or corrupted files."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.data_path.exists():
            self.tasks = []
            self._save()
            return

        try:
            raw = self.data_path.read_text(encoding="utf-8").strip()
            if not raw:
                self.tasks = []
                self._save()
                return
            payload = json.loads(raw)
            if not isinstance(payload, list):
                raise ValueError("Root JSON must be a list")
            self.tasks = [Task.from_dict(item) for item in payload if isinstance(item, dict)]
            self._deduplicate_ids()
        except (json.JSONDecodeError, ValueError, OSError):
            backup = self.data_path.with_suffix(".json.bak")
            try:
                self.data_path.rename(backup)
            except OSError:
                pass
            self.tasks = []
            self._save()

    def _save(self) -> None:
        """Persist all tasks to JSON."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        data = [task.to_dict() for task in self.tasks]
        self.data_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _deduplicate_ids(self) -> None:
        """Ensure task IDs are unique; regenerate duplicates."""
        seen: set[str] = set()
        changed = False
        for task in self.tasks:
            if task.id in seen:
                task.id = str(uuid.uuid4())
                changed = True
            seen.add(task.id)
        if changed:
            self._save()

    def _persist(self) -> None:
        """Save after every mutation."""
        self._save()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> tuple[bool, str]:
        """Add a task; reject duplicates by title (case-insensitive)."""
        if not task.title:
            return False, "Task title cannot be empty."

        if self._is_duplicate_title(task.title):
            return False, "A task with this title already exists."

        self.tasks.append(task)
        self._persist()
        return True, "Task added successfully."

    def update_task(self, task_id: str, **fields: Any) -> tuple[bool, str]:
        """Update task fields by ID."""
        task = self.get_task(task_id)
        if task is None:
            return False, "Task not found."

        if "title" in fields:
            new_title = str(fields["title"]).strip()
            if not new_title:
                return False, "Task title cannot be empty."
            if self._is_duplicate_title(new_title, exclude_id=task_id):
                return False, "A task with this title already exists."
            task.title = new_title

        if "category" in fields:
            cat = str(fields["category"])
            task.category = cat if cat in CATEGORIES else task.category

        if "priority" in fields:
            pri = str(fields["priority"])
            task.priority = pri if pri in PRIORITIES else task.priority

        if "due_date" in fields:
            task.due_date = fields["due_date"]

        if "important" in fields:
            task.important = bool(fields["important"])

        if "notes" in fields:
            task.notes = str(fields["notes"])

        if "completed" in fields:
            task.completed = bool(fields["completed"])

        self._persist()
        return True, "Task updated successfully."

    def delete_task(self, task_id: str) -> tuple[bool, str]:
        """Remove a task by ID."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) == before:
            return False, "Task not found."
        self._persist()
        return True, "Task deleted."

    def delete_tasks(self, task_ids: list[str]) -> int:
        """Remove multiple tasks; return count deleted."""
        id_set = set(task_ids)
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id not in id_set]
        deleted = before - len(self.tasks)
        if deleted:
            self._persist()
        return deleted

    def toggle_complete(self, task_id: str) -> tuple[bool, str]:
        """Toggle completion status."""
        task = self.get_task(task_id)
        if task is None:
            return False, "Task not found."
        task.completed = not task.completed
        self._persist()
        status = "completed" if task.completed else "marked active"
        return True, f"Task {status}."

    def mark_complete(self, task_ids: list[str], completed: bool = True) -> int:
        """Set completion for multiple tasks."""
        id_set = set(task_ids)
        count = 0
        for task in self.tasks:
            if task.id in id_set and task.completed != completed:
                task.completed = completed
                count += 1
        if count:
            self._persist()
        return count

    def clear_completed(self) -> int:
        """Delete all completed tasks."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.completed]
        removed = before - len(self.tasks)
        if removed:
            self._persist()
        return removed

    def toggle_important(self, task_id: str) -> tuple[bool, str]:
        """Toggle important flag."""
        task = self.get_task(task_id)
        if task is None:
            return False, "Task not found."
        task.important = not task.important
        self._persist()
        return True, "Important status updated."

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def _is_duplicate_title(self, title: str, exclude_id: Optional[str] = None) -> bool:
        normalized = title.strip().lower()
        for task in self.tasks:
            if exclude_id and task.id == exclude_id:
                continue
            if task.title.strip().lower() == normalized:
                return True
        return False

    # ------------------------------------------------------------------
    # Query, filter, sort
    # ------------------------------------------------------------------

    def get_all_tasks(
        self,
        view: str = "all",
        search: str = "",
        category_filter: str = "All",
        status_filter: str = "All",
        sort_by: str = "Due Date",
    ) -> list[Task]:
        """Return filtered and sorted task list for the current view."""
        tasks = deepcopy(self.tasks)
        tasks = self._filter_by_view(tasks, view)
        tasks = self._filter_by_search(tasks, search)
        tasks = self._filter_by_category(tasks, category_filter)
        tasks = self._filter_by_status(tasks, status_filter)
        return self._sort_tasks(tasks, sort_by)

    def _filter_by_view(self, tasks: list[Task], view: str) -> list[Task]:
        today_str = date.today().isoformat()
        if view == "today":
            return [
                t for t in tasks
                if not t.completed and (t.due_date == today_str or t.due_date is None)
            ]
        if view == "important":
            return [t for t in tasks if t.important and not t.completed]
        if view == "completed":
            return [t for t in tasks if t.completed]
        return tasks

    def _filter_by_search(self, tasks: list[Task], search: str) -> list[Task]:
        if not search.strip():
            return tasks
        query = search.strip().lower()
        return [
            t for t in tasks
            if query in t.title.lower()
            or query in t.category.lower()
            or query in t.notes.lower()
        ]

    def _filter_by_category(self, tasks: list[Task], category: str) -> list[Task]:
        if category == "All":
            return tasks
        return [t for t in tasks if t.category == category]

    def _filter_by_status(self, tasks: list[Task], status: str) -> list[Task]:
        if status == "Active":
            return [t for t in tasks if not t.completed]
        if status == "Completed":
            return [t for t in tasks if t.completed]
        return tasks

    def _sort_tasks(self, tasks: list[Task], sort_by: str) -> list[Task]:
        if sort_by == "Title":
            return sorted(tasks, key=lambda t: t.title.lower())
        if sort_by == "Priority":
            return sorted(tasks, key=lambda t: priority_weight(t.priority))
        if sort_by == "Created":
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)
        # Due Date — tasks with dates first, then by date ascending
        def due_key(t: Task) -> tuple[int, str]:
            if t.due_date:
                return (0, t.due_date)
            return (1, "9999-12-31")

        return sorted(tasks, key=due_key)

    def get_stats(self) -> dict[str, Any]:
        """Return progress statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        remaining = total - completed
        percentage = int((completed / total) * 100) if total else 0
        return {
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "percentage": percentage,
        }
