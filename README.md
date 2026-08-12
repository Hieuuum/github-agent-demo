# task-manager

A small Python library for managing tasks in memory.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```python
from task_manager import TaskStore

store = TaskStore()
task = store.create_task("Buy milk", priority=1)
store.complete_task(task.id)
store.delete_task(task.id)
```

## Project layout

```text
src/task_manager/
    models.py      # Task data model
    validation.py  # validate_title, validate_priority
    storage.py      # in-memory storage backend
    tasks.py       # TaskStore: create_task, get_task, complete_task, delete_task
tests/
```

## Running tests

```bash
pytest
```
