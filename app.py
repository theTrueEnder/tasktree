from flask import Flask, render_template, request, redirect, url_for
from task_manager import TaskManager
from models import Task, TaskState

app = Flask(__name__)
tm = TaskManager()

@app.route("/")
def index():
    return render_template("index.html",
        pending=tm.get_tasks_by_state("PENDING"),
        external=tm.get_tasks_by_state("EXTERNAL"),
        completed=tm.get_tasks_by_state("COMPLETED")
    )

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    is_external = request.form.get("is_external") == "on"
    if title:
        task = Task(title=title, description=description)
        if is_external:
            task.state = TaskState.EXTERNAL
        tm.add_task(task)
    return redirect(url_for("index"))

@app.route("/complete/<task_id>")
def complete_task(task_id):
    tm.complete_task(task_id)
    return redirect(url_for("index"))

@app.route("/tree")
def task_tree():
    return render_template("tree.html")

if __name__ == "__main__":
    app.run(debug=True)
