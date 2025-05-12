import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QLineEdit, QTextEdit, QPushButton, QCheckBox, QGroupBox, QFormLayout,
    QComboBox, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QDialog
)
from PyQt6.QtCore import Qt
from models import Task, TaskState
from task_manager import TaskManager

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

        # Left: Task lists
        list_layout = QVBoxLayout()

        self.remaining_list = self.create_task_list("Remaining Tasks")
        self.external_list = self.create_task_list("External Tasks")
        self.completed_list = self.create_task_list("Completed Tasks")

        list_layout.addWidget(self.remaining_list["group"])
        list_layout.addWidget(self.external_list["group"])
        list_layout.addWidget(self.completed_list["group"])

        # Right: Task form
        form_group = QGroupBox("New Task")
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.parent_dropdown = QComboBox()
        self.external_check = QCheckBox("External Task")
        self.submit_btn = QPushButton("Add Task")
        self.tree_btn = QPushButton("Open Task Tree")

        self.submit_btn.clicked.connect(self.submit_task)
        self.tree_btn.clicked.connect(self.show_tree)

        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Description:", self.desc_input)
        form_layout.addRow("Depends on:", self.parent_dropdown)
        form_layout.addRow("", self.external_check)
        form_layout.addRow("", self.submit_btn)
        form_layout.addRow("", self.tree_btn)

        form_group.setLayout(form_layout)

        layout.addLayout(list_layout, 2)
        layout.addWidget(form_group, 1)

        self.setStyleSheet(self.dark_theme())

    def create_task_list(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        group.setLayout(layout)

        list_widget.itemClicked.connect(lambda item: self.load_task_from_title(item.text()))

        return {"group": group, "list": list_widget}

    def load_task_from_title(self, title):
        for task in self.tm.tasks.values():
            if task.title == title:
                self.selected_task = task
                self.title_input.setText(task.title)
                self.desc_input.setText(task.description)
                self.external_check.setChecked(task.state == TaskState.EXTERNAL)
                self.submit_btn.setText("Save Changes")
                break

    def submit_task(self):
        title = self.title_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        is_external = self.external_check.isChecked()
        parent_title = self.parent_dropdown.currentText()

        if not title:
            return

        if self.selected_task:
            self.selected_task.title = title
            self.selected_task.description = desc
            self.selected_task.state = TaskState.EXTERNAL if is_external else TaskState.PENDING
        else:
            task = Task(title=title, description=desc)
            task.state = TaskState.EXTERNAL if is_external else TaskState.PENDING

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
        self.selected_task = None
        self.submit_btn.setText("Add Task")

        self.refresh_lists()

    def refresh_lists(self):
        self.remaining_list["list"].clear()
        self.external_list["list"].clear()
        self.completed_list["list"].clear()
        self.parent_dropdown.clear()
        self.parent_dropdown.addItem("")

        for task in self.tm.tasks.values():
            if task.state == TaskState.PENDING:
                self.remaining_list["list"].addItem(task.title)
                self.parent_dropdown.addItem(task.title)
            elif task.state == TaskState.EXTERNAL:
                self.external_list["list"].addItem(task.title)
            elif task.state == TaskState.COMPLETED:
                self.completed_list["list"].addItem(task.title)

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
        QListWidget {
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
