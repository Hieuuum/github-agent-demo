import pytest

from task_manager.tasks import TaskStore


def test_create_task_returns_task_with_generated_id():
    store = TaskStore()
    task = store.create_task("Buy milk", priority=1)
    assert task.id == 1
    assert task.title == "Buy milk"
    assert task.priority == 1
    assert task.completed is False


def test_create_task_auto_increments_ids():
    store = TaskStore()
    first = store.create_task("First")
    second = store.create_task("Second")
    assert second.id == first.id + 1


def test_get_task_returns_existing_task():
    store = TaskStore()
    created = store.create_task("Read a book")
    fetched = store.get_task(created.id)
    assert fetched == created


def test_get_task_returns_none_for_missing_task():
    store = TaskStore()
    assert store.get_task(999) is None


def test_complete_task_marks_task_completed():
    store = TaskStore()
    task = store.create_task("Wash dishes")
    result = store.complete_task(task.id)
    assert result is True
    assert store.get_task(task.id).completed is True


def test_delete_task_removes_existing_task():
    store = TaskStore()
    task = store.create_task("Take out trash")
    assert store.delete_task(task.id) is True
    assert store.get_task(task.id) is None


def test_delete_task_returns_false_for_missing_task():
    store = TaskStore()
    assert store.delete_task(999) is False


def test_create_task_rejects_whitespace_only_title():
    store = TaskStore()
    with pytest.raises(ValueError):
        store.create_task("   ")
