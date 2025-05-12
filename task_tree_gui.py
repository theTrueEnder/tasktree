import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QLineEdit, QTextEdit, QPushButton, QCheckBox, QGroupBox, QFormLayout,
    QComboBox, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QDialog, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt

from enum import Enum
import uuid

class TaskState(Enum):
    PENDING = "pending"
    EXTERNAL = "external"
    COMPLETED = "completed"

class Task:
    def __init__(self, title, description=""):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.state = TaskState.PENDING
        self.dependencies = []
        self.dependents = []

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task):
        self.tasks[task.id] = task

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def update_task_state(self, task_id, new_state):
        if task_id in self.tasks:
            self.tasks[task_id].state = new_state

class TaskTreeDialog(QDialog):
    def __init__(self, task_manager):
        super().__init__()
        self.setWindowTitle("Task Tree")
        self.setMinimumSize(800, 600)
        self.tm = task_manager
        self.view = QGraphicsView()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.draw_tree()

    def draw_tree(self):
        scene = QGraphicsScene()
        node_width, node_height = 120, 50
        level_spacing, node_spacing = 100, 150
        positions = {}

        def place_task(task_id, level, index):
            x = index * node_spacing
            y = level * level_spacing
            positions[task_id] = (x, y)
            return x, y

        visited = set()
        levels = {}

        def dfs(task_id, level):
            if task_id in visited:
                return
            visited.add(task_id)
            levels.setdefault(level, []).append(task_id)
            for child_id in self.tm.tasks[task_id].dependents:
                dfs(child_id, level + 1)

        roots = [t.id for t in self.tm.tasks.values() if not t.dependencies]
        for i, root_id in enumerate(roots):
            dfs(root_id, 0)

        for level in sorted(levels.keys()):
            for i, task_id in enumerate(levels[level]):
                place_task(task_id, level, i)

        for task_id, (x, y) in positions.items():
            node = QGraphicsEllipseItem(x, y, node_width, node_height)
            node.setBrush(Qt.GlobalColor.cyan)
            scene.addItem(node)

            label = QGraphicsTextItem(self.tm.tasks[task_id].title)
            label.setDefaultTextColor(Qt.GlobalColor.white)
            label.setPos(x + 10, y + 15)
            scene.addItem(label)

        for task in self.tm.tasks.values():
            for dep_id in task.dependencies:
                if dep_id in positions and task.id in positions:
                    x1, y1 = positions[dep_id][0] + node_width / 2, positions[dep_id][1] + node_height
                    x2, y2 = positions[task.id][0] + node_width / 2, positions[task.id][1]
                    line = QGraphicsLineItem(x1, y1, x2, y2)
                    scene.addItem(line)

        self.view.setScene(scene)


class TaskTreeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Tree")
        self.setMinimumSize(1000, 600)
        self.tm = TaskManager()
        self.selected_task = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Left: Hierarchical Task Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Tasks")
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)

        # Right: Task form
        form_group = QGroupBox("Task Details")
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.parent_dropdown = QComboBox()
        self.external_check = QCheckBox("External Task")
        self.completed_check = QCheckBox("Completed")
        self.submit_btn = QPushButton("Add Task")
        self.tree_btn = QPushButton("Open Task Tree")

        self.submit_btn.clicked.connect(self.submit_task)
        self.tree_btn.clicked.connect(self.show_tree)

        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Description:", self.desc_input)
        form_layout.addRow("Depends on:", self.parent_dropdown)
        form_layout.addRow("", self.external_check)
        form_layout.addRow("", self.completed_check)
        form_layout.addRow("", self.submit_btn)
        form_layout.addRow("", self.tree_btn)

        form_group.setLayout(form_layout)

        layout.addWidget(self.tree_widget, 2)
        layout.addWidget(form_group, 1)

        self.setStyleSheet(self.dark_theme())
        # self.refresh_lists()


    def refresh_tree(self):
        self.tree_widget.clear()
        self.parent_dropdown.clear()
        self.parent_dropdown.addItem("")

        task_items = {}
        for task in self.tm.tasks.values():
            item = QTreeWidgetItem([task.title])
            item.setData(0, Qt.ItemDataRole.UserRole, task.id)
            if task.state == TaskState.COMPLETED:
                item.setForeground(0, Qt.GlobalColor.green)
            elif task.state == TaskState.EXTERNAL:
                item.setForeground(0, Qt.GlobalColor.yellow)
            task_items[task.id] = item

        for task in self.tm.tasks.values():
            if not task.dependencies:
                self.tree_widget.addTopLevelItem(task_items[task.id])
            for dep_id in task.dependencies:
                if dep_id in task_items:
                    task_items[dep_id].addChild(task_items[task.id])

            self.parent_dropdown.addItem(task.title)

        self.tree_widget.expandAll()

    def on_tree_item_clicked(self, item):
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        task = self.tm.get_task(task_id)
        if task:
            self.selected_task = task
            self.title_input.setText(task.title)
            self.desc_input.setText(task.description)
            self.external_check.setChecked(task.state == TaskState.EXTERNAL)
            self.completed_check.setChecked(task.state == TaskState.COMPLETED)
            self.submit_btn.setText("Save Changes")

    def submit_task(self):
        title = self.title_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        is_external = self.external_check.isChecked()
        is_completed = self.completed_check.isChecked()
        parent_title = self.parent_dropdown.currentText()

        if not title:
            return

        state = TaskState.COMPLETED if is_completed else TaskState.EXTERNAL if is_external else TaskState.PENDING

        if self.selected_task:
            self.selected_task.title = title
            self.selected_task.description = desc
            self.selected_task.state = state
        else:
            task = Task(title=title, description=desc)
            task.state = state

            if parent_title:
                for t in self.tm.tasks.values():
                    if t.title == parent_title:
                        task.dependencies.append(t.id)
                        t.dependents.append(task.id)
                        break
            self.tm.add_task(task)

        self.title_input.clear()
        self.desc_input.clear()
        self.external_check.setChecked(False)
        self.completed_check.setChecked(False)
        self.selected_task = None
        self.submit_btn.setText("Add Task")

        self.refresh_tree()

    def show_tree(self):
        dlg = TaskTreeDialog(self.tm)
        dlg.exec()

    def dark_theme(self):
        return """
        QWidget {
            background-color: #121212;
            color: #eeeeee;
            font-family: Arial;
        }
        QGroupBox {
            border: 1px solid #333;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #555;
        }
        QPushButton {
            background-color: #03dac5;
            color: #000;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #00c4a7;
        }
        QTreeWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #444;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TaskTreeApp()
    win.show()
    sys.exit(app.exec())
