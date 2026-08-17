"""Tests for task prioritisation (Exercise 10).

Covers: Part 1 behaviour analysis, Part 2 improved single test, Part 3 TDD for
the assignee feature and the freshness bug fix, and Part 4 integration.
"""
import unittest
from datetime import datetime, timedelta

from models import Task, TaskStatus, TaskPriority
from task_priority import (
    calculate_task_score,
    sort_tasks_by_importance,
    get_top_priority_tasks,
)


def make_task(priority=TaskPriority.MEDIUM, status=TaskStatus.TODO,
              due_in_hours=None, tags=None, updated_days_ago=0, assignee=None):
    """Build a Task in a known state.

    Due offsets are expressed in HOURS and chosen to sit in the middle of a
    scoring bucket. This deliberately avoids the ``timedelta.days`` truncation
    boundary problem (see Exercise 3): if we used exact day offsets, the few
    microseconds between building the task and scoring it would push a task
    across a bucket edge and make the test flaky.
    """
    t = Task("t", priority=priority, tags=tags or [], assignee=assignee)
    t.status = status
    t.updated_at = datetime.now() - timedelta(days=updated_days_ago)
    if due_in_hours is not None:
        t.due_date = datetime.now() + timedelta(hours=due_in_hours)
    return t


class TestScoringComponents(unittest.TestCase):
    """Part 1 — behaviour analysis: each factor in isolation."""

    def test_base_priority_weights(self):
        # No due date, TODO, no tags, updated 5 days ago -> only base score.
        for pr, expected in [
            (TaskPriority.LOW, 10), (TaskPriority.MEDIUM, 20),
            (TaskPriority.HIGH, 40), (TaskPriority.URGENT, 60),
        ]:
            t = make_task(priority=pr, updated_days_ago=5)
            self.assertEqual(calculate_task_score(t), expected)

    def test_due_date_buckets(self):
        base = 20  # MEDIUM
        self.assertEqual(calculate_task_score(make_task(due_in_hours=-24, updated_days_ago=5)), base + 35)  # overdue
        self.assertEqual(calculate_task_score(make_task(due_in_hours=12,  updated_days_ago=5)), base + 20)  # today (0 days)
        self.assertEqual(calculate_task_score(make_task(due_in_hours=36,  updated_days_ago=5)), base + 15)  # 1 day -> <=2
        self.assertEqual(calculate_task_score(make_task(due_in_hours=120, updated_days_ago=5)), base + 10)  # 5 days -> <=7
        self.assertEqual(calculate_task_score(make_task(due_in_hours=720, updated_days_ago=5)), base)        # 30 days off

    def test_status_penalties(self):
        self.assertEqual(calculate_task_score(make_task(status=TaskStatus.DONE, updated_days_ago=5)), 20 - 50)
        self.assertEqual(calculate_task_score(make_task(status=TaskStatus.REVIEW, updated_days_ago=5)), 20 - 15)

    def test_tag_boost_applies_once(self):
        t = make_task(tags=["critical", "blocker"], updated_days_ago=5)
        self.assertEqual(calculate_task_score(t), 20 + 8)  # single +8 even with two matching tags

    def test_freshness_boost(self):
        self.assertEqual(calculate_task_score(make_task(updated_days_ago=0)), 20 + 5)  # fresh
        self.assertEqual(calculate_task_score(make_task(updated_days_ago=5)), 20)      # stale


class TestDueDateBehaviour(unittest.TestCase):
    """Part 2 — improved test: assert behaviour (the +15 due bonus), not internals."""

    def test_task_due_within_two_days_scores_higher_than_same_task_with_no_due_date(self):
        due_soon = make_task(priority=TaskPriority.MEDIUM, due_in_hours=36, updated_days_ago=5)  # 1 day -> +15
        no_due   = make_task(priority=TaskPriority.MEDIUM, due_in_hours=None, updated_days_ago=5)
        self.assertGreater(calculate_task_score(due_soon), calculate_task_score(no_due))
        self.assertEqual(calculate_task_score(due_soon) - calculate_task_score(no_due), 15)


class TestAssigneeFeature(unittest.TestCase):
    """Part 3.1 — TDD: +12 boost for the current user's tasks."""

    def test_assigned_to_current_user_gets_plus_12(self):
        mine = make_task(assignee="chris", updated_days_ago=5)
        self.assertEqual(calculate_task_score(mine, current_user="chris"), 20 + 12)

    def test_assigned_to_someone_else_gets_no_boost(self):
        theirs = make_task(assignee="sam", updated_days_ago=5)
        self.assertEqual(calculate_task_score(theirs, current_user="chris"), 20)

    def test_no_current_user_means_no_boost(self):
        mine = make_task(assignee="chris", updated_days_ago=5)
        self.assertEqual(calculate_task_score(mine), 20)


class TestFreshnessBugFix(unittest.TestCase):
    """Part 3.2 — TDD: a task updated days ago must NOT be treated as fresh."""

    def test_stale_task_does_not_get_freshness_boost(self):
        # Regression test for the '.seconds' bug: 3 days old -> no +5.
        stale = make_task(updated_days_ago=3)
        self.assertEqual(calculate_task_score(stale), 20)


class TestWorkflowIntegration(unittest.TestCase):
    """Part 4 — integration: score -> sort -> top-N work together."""

    def test_sort_and_top_n_order_by_score(self):
        urgent_overdue = make_task(priority=TaskPriority.URGENT, due_in_hours=-24, updated_days_ago=5)  # 60+35=95
        high_soon      = make_task(priority=TaskPriority.HIGH, due_in_hours=36, updated_days_ago=5)     # 40+15=55
        low_far        = make_task(priority=TaskPriority.LOW, updated_days_ago=5)                     # 10
        done_urgent    = make_task(priority=TaskPriority.URGENT, status=TaskStatus.DONE, updated_days_ago=5)  # 60-50=10

        tasks = [low_far, done_urgent, high_soon, urgent_overdue]
        ordered = sort_tasks_by_importance(tasks)
        self.assertIs(ordered[0], urgent_overdue)
        self.assertIs(ordered[1], high_soon)

        top2 = get_top_priority_tasks(tasks, limit=2)
        self.assertEqual([t is urgent_overdue for t in top2], [True, False])
        self.assertIs(top2[1], high_soon)

    def test_current_user_boost_changes_ordering(self):
        a = make_task(priority=TaskPriority.MEDIUM, updated_days_ago=5)                 # 20
        mine = make_task(priority=TaskPriority.MEDIUM, updated_days_ago=5, assignee="chris")  # 20 (+12 when viewed by chris)
        # Without a current user, ordering among equal scores is stable (a first).
        self.assertEqual(sort_tasks_by_importance([a, mine]), [a, mine])
        # As chris, my task jumps ahead.
        self.assertEqual(sort_tasks_by_importance([a, mine], current_user="chris"), [mine, a])


if __name__ == "__main__":
    unittest.main()
