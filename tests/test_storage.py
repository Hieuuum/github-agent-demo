from task_manager.models import Task
from task_manager.storage import TaskStorage


def test_add_and_get_task():
    storage = TaskStorage()
    task = Task(id=1, title="Buy milk", priority=0)
    storage.add(task)
    assert storage.get(1) == task


def test_get_missing_task_returns_none():
    storage = TaskStorage()
    assert storage.get(42) is None


def test_delete_existing_task_returns_true():
    storage = TaskStorage()
    task = Task(id=1, title="Buy milk", priority=0)
    storage.add(task)
    assert storage.delete(1) is True
    assert storage.get(1) is None


def test_delete_missing_task_returns_false():
    storage = TaskStorage()
    assert storage.delete(99) is False


def test_all_returns_every_stored_task():
    storage = TaskStorage()
    t1 = Task(id=1, title="One", priority=0)
    t2 = Task(id=2, title="Two", priority=1)
    storage.add(t1)
    storage.add(t2)
    assert storage.all() == [t1, t2]
