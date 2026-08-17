"""Task prioritisation scoring (Exercise 10 — tested & extended).

Two changes were driven by TDD in this exercise:
  * Part 3.1 (new feature): tasks assigned to the *current user* get a +12 boost.
  * Part 3.2 (bug fix): the "days since update" freshness check must use the
    timedelta's ``.days`` (whole elapsed days). The original buggy analogue used
    ``.seconds`` which ignores the day component entirely — so a task last
    updated several days ago still looked "fresh" and wrongly earned +5.
"""

from datetime import datetime

from models import TaskStatus, TaskPriority


def calculate_task_score(task, current_user=None):
    """Compute a task's importance score.

    Args:
        task: task-like object (priority, due_date, status, tags, updated_at,
            and optionally assignee).
        current_user: username of the person viewing the list. If the task is
            assigned to them, it receives a +12 boost.

    Returns:
        int: the summed importance score.
    """
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6,
    }
    score = priority_weights.get(task.priority, 0) * 10

    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:
            score += 35
        elif days_until_due == 0:
            score += 20
        elif days_until_due <= 2:
            score += 15
        elif days_until_due <= 7:
            score += 10

    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    # Freshness: whole elapsed days (fixed — see module docstring).
    days_since_update = (datetime.now() - task.updated_at).days
    if days_since_update < 1:
        score += 5

    # New feature: boost tasks assigned to the current user.
    if current_user is not None and getattr(task, "assignee", None) == current_user:
        score += 12

    return score


def sort_tasks_by_importance(tasks, current_user=None):
    """Return tasks ordered by importance score, highest first."""
    task_scores = [(calculate_task_score(task, current_user), task) for task in tasks]
    return [task for _, task in sorted(task_scores, key=lambda x: x[0], reverse=True)]


def get_top_priority_tasks(tasks, limit=5, current_user=None):
    """Return the top ``limit`` tasks by importance score."""
    return sort_tasks_by_importance(tasks, current_user)[:limit]
