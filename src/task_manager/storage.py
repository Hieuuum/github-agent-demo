"""In-memory storage backend for tasks."""

from typing import Optional

from .models import Task


class TaskStorage:
    """Simple in-memory storage keyed by task id."""

    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def generate_id(self) -> int:
        task_id = self._next_id
        self._next_id += 1
        return task_id

    def add(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def get(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def delete(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def all(self) -> list[Task]:
        return list(self._tasks.values())
