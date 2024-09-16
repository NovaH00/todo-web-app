from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
from datetime import datetime, date, timedelta, time
import sqlite3
from functools import wraps
import time 
import threading

app = Flask(__name__)
app.secret_key = 'this_is_a_very_secret_key'

# DATABASE_DIR = "/home/novah00/todo-web-app/data/database.db"
# BACKUP_DATABASE_DIR = "/home/novah00/todo-web-app/data/backup_database.db"

DATABASE_DIR = "data/database.db"
BACKUP_DATABASE_DIR = "data/backup_database.db"


tasks = []

def format_date(date_string):
    date_obj = datetime.strptime(date_string, '%d-%m-%Y')
    return date_obj.strftime('%d/%m/%Y')

app.jinja_env.globals.update(format_date=format_date)

def backup_database():
    try:
        # Connect to the original database
        connection = sqlite3.connect(DATABASE_DIR)
        
        # Create a new connection to the backup database
        with sqlite3.connect(BACKUP_DATABASE_DIR) as backup_connection:
            # Perform the backup
            connection.backup(backup_connection)
            print("Database backup completed successfully.")

        # Close the connection to the original database
        connection.close()
    
    except Exception as e:
        print(f"An error occurred during the backup: {e}")

def backup_database_with_delay():
    global last_backup_time
    while True:
        try:
            # Connect to the original database
            connection = sqlite3.connect(DATABASE_DIR)
            
            # Create a new connection to the backup database
            with sqlite3.connect(BACKUP_DATABASE_DIR) as backup_connection:
                # Perform the backup
                connection.backup(backup_connection)
                print("Database backup completed successfully.")
            
            # Close the connection to the original database
            connection.close()
            
            last_backup_time = datetime.now()
        
        except Exception as e:
            print(f"An error occurred during the backup: {e}")
        
        # Wait for 1 hours before running the next backup

        time.sleep(24*60*60)



# Function to start the backup thread
def start_backup_thread():
    backup_thread = threading.Thread(target=backup_database_with_delay)
    backup_thread.daemon = True  # Daemon thread will exit when the main program exits
    backup_thread.start()

# Start the backup thread when the Flask app starts
with app.app_context():
    start_backup_thread()


def get_db():
    conn = sqlite3.connect(DATABASE_DIR)
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
        # Convert task['start_date'] to a datetime object (assuming format is 'DD-MM-YYYY')
        task_start_date = datetime.strptime(task['start_date'], '%d-%m-%Y').date()
        
        # Compare with today's date
        if task_start_date <= date.today():
            current_tasks.append(task)
        else:
            future_tasks.append(task)

    return current_tasks, future_tasks


# Decorator to require login for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Phải đăng nhập để tiếp tục.', 'login')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/remaining_time')
def get_remaining_time():
    global last_backup_time
    now = datetime.now()
    twenty_four_hours = timedelta(hours=24)
    remaining_time = twenty_four_hours-(now - last_backup_time)
    
    if remaining_time.total_seconds() < 0:
        remaining_time = timedelta(0)  # In case backup is overdue

    return jsonify({
        'hours': remaining_time.seconds // 3600,
        'minutes': (remaining_time.seconds % 3600) // 60,
        'seconds': remaining_time.seconds % 60
    })

@app.route('/backup_info', methods=["POST", "GET"])
def backup_info():
    print("called")
    return render_template('backup_info.html')

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
        flash('Tên người dùng hoặc mật khẩu không đúng', 'login')
        return redirect(url_for('index'))


import sqlite3

def copy_row_from_backup(username):
    # Connect to the backup database
    backup_conn = sqlite3.connect(BACKUP_DATABASE_DIR)
    backup_cursor = backup_conn.cursor()

    # Connect to the main database
    main_conn = sqlite3.connect(DATABASE_DIR)
    main_cursor = main_conn.cursor()

    try:
        # Fetch the specific row from the backup database
        backup_cursor.execute('SELECT id, username, password, tasks FROM users WHERE username = ?', (username,))
        row = backup_cursor.fetchone()

        if row:
            # Insert the row into the main database
            main_cursor.execute('INSERT OR REPLACE INTO users (id, username, password, tasks) VALUES (?, ?, ?, ?)', row)
            main_conn.commit()
            print(f"{username} copied successfully.")
        else:
            print(f"No row found with username {username} in the backup database.")
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connections
        backup_conn.close()
        main_conn.close()


@app.route('/roll_back', methods=['POST'])
@login_required
def roll_back():
    username = session['username']
    copy_row_from_backup(username)
    get_tasks(username)
    
    return redirect(url_for('roll_back_success'))

@app.route('/confirm_roll_back')
def confirm_roll_back():
    return render_template('confirm_roll_back.html')

@app.route('/roll_back_success')
def roll_back_success():
    return render_template('roll_back_success.html')
    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove the username from the session
    flash('Bạn đã đăng xuất', 'login')
    return redirect(url_for('index'))

@app.route('/home', methods=["POST", "GET"])
@login_required  # Use the login_required decorator
def home():
    current_tasks, future_tasks = get_sorted_tasks()
    return render_template('home.html', current_tasks=current_tasks, future_tasks=future_tasks)

@app.route('/login_success')
def login_success():
    return render_template('login_success.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
    if cursor.fetchone()[0] > 0:
        flash('Tên đăng nhập đã tồn tại', 'signup')
        return redirect(url_for('index') + '#signup')
    
    cursor.execute('INSERT INTO users (username, password, tasks) VALUES (?, ?, ?)', (username, password, '[]'))
    conn.commit()
    
    flash('Đăng ký thành công, hãy đăng nhập để tiếp tục', 'login')
    return redirect(url_for('index') + '#login')

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


@app.route('/change_password_btn')
def change_password_btn():
    return render_template('change_password.html') 

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    username = session['username']
    current_pass = request.form.get('current_password')
    new_pass = request.form.get('new_password')
    confirm_new_pass = request.form.get('confirm_new_password')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username, )) 
    old_password = cursor.fetchone()[0]
    
    
    if current_pass != old_password:
        flash("Sai mật khẩu", 'error')
        conn.close()
        return redirect(url_for('change_password_btn'))
    elif new_pass != confirm_new_pass:
        flash("Mật khẩu nhập lại khác mật khẩu mới", 'error')
        conn.close()
        return redirect(url_for('change_password_btn'))
    else:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass, username))
        conn.commit()
        conn.close()
        backup_database()
        flash("Đổi mật khẩu thành công", "")
        return redirect(url_for('change_password_btn'))
    


def fetch_users_as_dict():
    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE_DIR)
    
    # To return rows as dictionaries
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Execute a query to get all users
    cursor.execute("SELECT * FROM users")
    
    # Fetch all rows from the 'users' table
    rows = cursor.fetchall()

    # Convert each row to a dictionary and store in a list
    users_list = [dict(row) for row in rows]

    # Close the connection
    conn.close()

    return users_list


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if 'username' in session and session['username'] == 'admin':
        users = fetch_users_as_dict()
        return render_template('admin.html', users=users)
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
