from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
from datetime import datetime, date
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'this_is_a_very_secret_key'

tasks = []

def format_date(date_string):
    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
    return date_obj.strftime('%d/%m/%Y')

app.jinja_env.globals.update(format_date=format_date)

def get_db():
    conn = sqlite3.connect("data/database.db")
    return conn

def get_tasks(username):
    global tasks
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT tasks FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    
    if row:
        tasks_json = row[0]
        tasks = json.loads(tasks_json)
    else:
        tasks = []

# Get sorted tasks (current and future)
def get_sorted_tasks():
    current_tasks = []
    future_tasks = []

    for task in tasks:
        if task['start_date'] <= str(date.today()):
            current_tasks.append(task)
        else:
            future_tasks.append(task)

    return current_tasks, future_tasks

# Decorator to require login for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in to access this page.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    
    if row and password == row[0]:
        session['username'] = username  # Store username in session
        get_tasks(username)
        return redirect(url_for('home'))
    else:
        flash('Tên người dùng hoặc mật khẩu không đúng')
        return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove the username from the session
    flash('Bạn đã đăng xuất')
    return redirect(url_for('index'))

@app.route('/home')
@login_required  # Use the login_required decorator
def home():
    current_tasks, future_tasks = get_sorted_tasks()
    return render_template('home.html', current_tasks=current_tasks, future_tasks=future_tasks)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
    if cursor.fetchone()[0] > 0:
        flash('Tên đăng nhập đã tồn tại')
        return redirect(url_for('index'))
    
    cursor.execute('INSERT INTO users (username, password, tasks) VALUES (?, ?, ?)', (username, password, '[]'))
    conn.commit()
    
    flash('Đăng ký thành công, hãy đăng nhập để tiếp tục')
    return redirect(url_for('index'))

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))  # Redirect to home if already logged in
    return render_template('index.html')

@app.route('/add_task', methods=['POST'])
@login_required  # Use the login_required decorator
def add_task():
    global tasks
    username = session['username']  # Get username from session
    
    task_name = request.form['task_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    description = request.form['description']
    
    new_task = {
        'name': task_name,
        'start_date': start_date,
        'end_date': end_date,
        'start_time': start_time,
        'end_time': end_time,
        'description': description
    }
    
    tasks.append(new_task)
    tasks_json = json.dumps(tasks)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET tasks = ?
        WHERE username = ?
    ''', (tasks_json, username))
    conn.commit()
    
    return redirect(url_for('home'))

@app.route('/delete_task', methods=['POST'])
@login_required  # Use the login_required decorator
def delete_task():
    global tasks
    task_id = int(request.form['task_id'])
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        
    username = session['username']
    tasks_json = json.dumps(tasks)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET tasks = ?
        WHERE username = ?
    ''', (tasks_json, username))
    conn.commit()

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
