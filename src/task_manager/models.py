"""Data model for a task."""

from dataclasses import dataclass


@dataclass
class Task:
    id: int
    title: str
    priority: int
    completed: bool = False
