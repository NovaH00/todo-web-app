from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime, date

app = Flask(__name__)

# Path to the JSON file
TASKS_FILE = r'data\tasks.json'

# Global list to hold the tasks
tasks = []

# Helper function to format the date
def format_date(date_string):
    date_obj = datetime.strptime(date_string, '%Y-%m-%d')  # Parse the date string
    return date_obj.strftime('%d/%m/%Y')  # Format it to 'dd/mm/yyyy'

app.jinja_env.globals.update(format_date=format_date)

# Load tasks from the JSON file into the globheheal `tasks` list
def load_tasks():
    global tasks
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as file:
                tasks = json.load(file)
        except json.JSONDecodeError:
            # If JSON is invalid or the file is empty, initialize an empty list
            tasks = []
    else:
        tasks = []


# Save the global `tasks` list to the JSON file
def save_tasks():
    with open(TASKS_FILE, 'w') as file:
        json.dump(tasks, file)

# Get sorted tasks (current and future)
def get_sorted_tasks():
    current_tasks = []
    future_tasks = []

    # Separate tasks based on the start date
    for task in tasks:
        if task['start_date'] <= str(date.today()):
            current_tasks.append(task)
        else:
            future_tasks.append(task)

    return current_tasks, future_tasks

@app.route('/')
def index():
    current_tasks, future_tasks = get_sorted_tasks()
    return render_template('index.html', current_tasks=current_tasks, future_tasks=future_tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    global tasks
    task_name = request.form['task_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    description = request.form['description']
    # Add the new task
    new_task = {
        'name': task_name,
        'start_date': start_date,
        'end_date': end_date,
        'start_time': start_time,
        'end_time': end_time,
        'description': description
    }
    tasks.append(new_task)

    # Save updated task list
    save_tasks()

    return redirect(url_for('index'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    global tasks
    task_id = int(request.form['task_id'])

    # Delete the specified task
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)

    # Save updated task list
    save_tasks()

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Load tasks at the start of the application
    load_tasks()
    app.run(host='0.0.0.0', port=5000)
