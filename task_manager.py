import networkx as nx
from models import Task, TaskState
from utils import extract_date, extract_tags
from typing import Dict, List

class TaskManager:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, Task] = {}

    # Pulls data from task and updates edges
    def add_task(self, task: Task, parents: List[str] = []):
        task.due_date = extract_date(task.description)
        task.tags = extract_tags(task.description)
        self.tasks[task.id] = task
        self.graph.add_node(task.id)

        for parent_id in parents:
            self.graph.add_edge(parent_id, task.id)

        self._update_blocking_states()

    # Marks a task as COMPLETED and updates the rest of the graph
    def complete_task(self, task_id: str):
        self.tasks[task_id].state = TaskState.COMPLETED
        self._update_blocking_states()

    # Updates dependencies on graph change
    #
    def _update_blocking_states(self):
        # print('\n~~~ New Iteration ~~~')
        for task_id in self.graph.nodes:
            task = self.tasks[task_id]
            td = task.description
            # print(task.title, '-', task_id)
            # print(f'\t{task.description}')
            # print(f'\tCurrent State = {task.state}')
            if task.state == TaskState.COMPLETED:
                # print('\tUpdated State = COMPLETED')
                continue
            predecessors = list(self.graph.predecessors(task_id))
            if any(self.tasks[p].state != TaskState.COMPLETED for p in predecessors):
                # If any upstream task is not completed, this task is blocked
                task.state = TaskState.BLOCKED
            elif "EXTERNAL" in td:
                # Change later to include manual task state changing
                task.state = TaskState.EXTERNAL
            else:
                # If task is not complete, blocked, or external, it is pending
                task.state = TaskState.PENDING
            # print(f'\tUpdated State = {task.state}')

    # Returns all tasks of a certain state (PENDING, BLOCKED, EXTERNAL, COMPLETED)
    def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        return [t for t in self.tasks.values() if t.state == state]
