"""Task prioritisation scoring.

This module ranks :class:`Task` objects by a computed *importance score* so a user
can see what to work on next. The score is a pure, additive function of a task's
fields (priority, due date, status, tags, recency); it is never stored on the task.

Scoring model (all contributions are summed):
    base       = priority weight x 10   (LOW=1, MEDIUM=2, HIGH=4, URGENT=6)
    due date   = overdue +35 / today +20 / <=2 days +15 / <=7 days +10 / else 0
    status     = DONE -50 / REVIEW -15 / else 0
    tags       = +8 if any tag in {blocker, critical, urgent}
    freshness  = +5 if updated less than 1 day ago
"""

from datetime import datetime

from models import TaskStatus, TaskPriority


def calculate_task_score(task):
    """Compute an importance score for a single task.

    The score combines five independent factors (see module docstring). Higher
    scores mean the task is more important to act on now. The function is pure:
    it does not mutate ``task`` and depends only on ``datetime.now()`` for the
    due-date and freshness factors.

    Args:
        task: A task-like object exposing ``priority`` (:class:`TaskPriority`),
            ``due_date`` (:class:`datetime` or ``None``), ``status``
            (:class:`TaskStatus`), ``tags`` (list of str) and ``updated_at``
            (:class:`datetime`).

    Returns:
        int: The summed importance score. Can be negative (e.g. a DONE task).

    Notes:
        * ``days_until_due`` uses ``timedelta.days``, which truncates toward
          zero, so a task due in 47 hours reports 1 day. Boundary results near
          midnight can therefore be surprising.
        * An unknown priority contributes a base of 0 (``dict.get`` default).

    Example:
        >>> calculate_task_score(task)  # HIGH, due in 1 day, TODO, tag 'critical', fresh
        68
    """
    # Base priority weights (deliberately non-linear: URGENT is emphasised).
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6,
    }

    # Base score from priority.
    score = priority_weights.get(task.priority, 0) * 10

    # Due-date urgency: sooner (or overdue) means a bigger boost.
    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:      # Overdue
            score += 35
        elif days_until_due == 0:   # Due today
            score += 20
        elif days_until_due <= 2:   # Due within two days
            score += 15
        elif days_until_due <= 7:   # Due within a week
            score += 10

    # Status penalties: finished/near-finished work is deprioritised.
    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    # Tag boost for explicitly critical work.
    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    # Freshness boost for very recently touched tasks.
    days_since_update = (datetime.now() - task.updated_at).days
    if days_since_update < 1:
        score += 5

    return score


def sort_tasks_by_importance(tasks):
    """Return ``tasks`` ordered by importance score, highest first.

    Each task is scored exactly once. Sorting keys on the score only, so two
    tasks with equal scores are never compared as objects (which would raise
    ``TypeError``); ties preserve input order because Python's sort is stable.

    Args:
        tasks: Iterable of task-like objects (see :func:`calculate_task_score`).

    Returns:
        list: A new list of the same tasks, sorted by descending score.
    """
    task_scores = [(calculate_task_score(task), task) for task in tasks]
    sorted_tasks = [task for _, task in sorted(task_scores, key=lambda x: x[0], reverse=True)]
    return sorted_tasks


def get_top_priority_tasks(tasks, limit=5):
    """Return the ``limit`` most important tasks.

    Args:
        tasks: Iterable of task-like objects.
        limit: Maximum number of tasks to return (default 5). If ``tasks`` has
            fewer items, all of them are returned.

    Returns:
        list: Up to ``limit`` tasks, ordered by descending importance score.
    """
    sorted_tasks = sort_tasks_by_importance(tasks)
    return sorted_tasks[:limit]
