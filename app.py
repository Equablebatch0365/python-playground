"""TaskFlow — A modern desktop to-do list application."""

from pathlib import Path

from task_manager import TaskManager
from ui import TaskFlowApp


def main() -> None:
    """Launch the TaskFlow application."""
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data" / "tasks.json"
    manager = TaskManager(data_path)
    app = TaskFlowApp(manager)
    app.run()


if __name__ == "__main__":
    main()
