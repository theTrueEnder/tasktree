import unittest
from models import Task, TaskState
from task_manager import TaskManager

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.tm = TaskManager()

    def test_add_and_block_tasks(self):
        t1 = Task(
            title="Initial",
            description="Start the project"
        )
        t2 = Task(
            title="Follow-up",
            description="Wait for response EXTERNAL"
        )

        self.tm.add_task(t1)
        self.tm.add_task(t2, parents=[t1.id])

        self.assertEqual(self.tm.tasks[t2.id].state, TaskState.BLOCKED)

        self.tm.complete_task(t1.id)
        self.assertEqual(self.tm.tasks[t2.id].state, TaskState.EXTERNAL)

    def test_task_by_state(self):
        t1 = Task("Do something", "Due 2025-06-01 #important")
        self.tm.add_task(t1)
        result = self.tm.get_tasks_by_state(TaskState.PENDING)
        self.assertIn(t1, result)

if __name__ == "__main__":
    unittest.main()
