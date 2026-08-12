"""High-level task operations."""

from typing import Optional

from .models import Task
from .storage import TaskStorage
from .validation import validate_priority, validate_title


class TaskStore:
    """Coordinates validation and storage for tasks."""

    def __init__(self):
        self._storage = TaskStorage()

    def create_task(self, title: str, priority: int = 0, task_id: Optional[int] = None) -> Task:
        validate_title(title)
        validate_priority(priority)

        if task_id is None:
            task_id = self._storage.generate_id()

        task = Task(id=task_id, title=title, priority=priority)
        return self._storage.add(task)

    def get_task(self, task_id: int) -> Optional[Task]:
        return self._storage.get(task_id)

    def complete_task(self, task_id: int) -> bool:
        task = self._storage.get(task_id)
        task.completed = True
        return True

    def delete_task(self, task_id: int) -> bool:
        return self._storage.delete(task_id)
