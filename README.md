# TaskFlow

A modern, elegant desktop to-do list application built with Python and Tkinter. TaskFlow combines a calming visual design with practical productivity features — inspired by Microsoft To Do and Notion.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-6BAA75?style=flat)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat)

---

## Project Overview

TaskFlow is a professional desktop productivity app that helps you organize tasks by category, priority, and due date. It features a clean sidebar navigation, card-based task layout, progress tracking, and automatic JSON persistence — all in a modular, maintainable codebase ready for GitHub.

---

## Features

### Task Management
- Add, edit, delete, and mark tasks complete
- Priority levels: Low, Medium, High
- Categories: Personal, School, Work, Shopping, Coding, Other
- Optional due dates and important flag
- Duplicate title detection

### Views & Filters
- **All Tasks** — full task list
- **Today** — tasks due today or without a due date
- **Important** — starred active tasks
- **Completed** — finished tasks
- Search by title, category, or notes
- Filter by category and completion status
- Sort by due date, priority, title, or created date

### Progress Tracking
- Tasks completed / remaining counts
- Completion percentage
- Animated progress bar

### UX & Animations
- Fade-in on startup
- Smooth task card appearance
- Fade-out on deletion
- Animated progress bar updates
- Button hover effects
- Toast notifications

### Data Persistence
- Automatic save to `data/tasks.json` on every change
- Automatic load on startup
- Handles missing, empty, or corrupted JSON files

---

## Screenshots

> Add screenshots here after running the app.

| Dashboard | Add Task Dialog |
|-----------|-----------------|
| *(screenshot)* | *(screenshot)* |

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Tkinter (included with standard Python on Windows and macOS)

On Linux, install Tkinter if needed:

```bash
sudo apt install python3-tk
```

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/taskflow.git
cd taskflow/todo-list
```

2. No external packages are required. Optionally create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

3. Run the application:

```bash
python app.py
```

---

## Usage

| Action | How |
|--------|-----|
| Add a task | Click **+ Add Task** in the bottom toolbar |
| Edit a task | Double-click the task title |
| Complete a task | Click the checkbox on a task card |
| Delete a task | Click **✕** on a task card |
| Bulk actions | Select tasks with the checkbox, then use toolbar buttons |
| Search | Type in the search field in the filter bar |
| Filter / Sort | Use the Category, Status, and Sort dropdowns |
| Navigate views | Use the left sidebar |

Tasks are saved automatically — no manual save required.

---

## Folder Structure

```
todo-list/
│
├── app.py              # Application entry point
├── ui.py               # User interface components
├── task_manager.py     # Business logic & JSON persistence
├── utils.py            # Theme, helpers, animations
├── README.md
├── requirements.txt
│
├── assets/             # Optional icons and images
│
└── data/
    └── tasks.json      # Task storage (auto-created)
```

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3 | Core language |
| Tkinter / ttk | Desktop GUI |
| JSON | Task persistence |
| pathlib | Cross-platform file paths |

---

## Architecture

TaskFlow follows a clean separation of concerns:

- **`task_manager.py`** — Task model, CRUD operations, filtering, sorting, and file I/O
- **`ui.py`** — Widgets, layout, dialogs, and user interactions
- **`utils.py`** — Shared theme constants, date helpers, and animation utilities
- **`app.py`** — Wires components together and launches the app

---

## Future Improvements

- [ ] Dark mode theme toggle
- [ ] Drag-and-drop task reordering
- [ ] Subtasks and checklists
- [ ] Recurring tasks
- [ ] Calendar view
- [ ] Export to CSV / PDF
- [ ] System tray integration
- [ ] Keyboard shortcuts
- [ ] Cloud sync

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Author

Built with care for productivity enthusiasts. Contributions and feedback are welcome!
