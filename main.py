from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import re
import hashlib

app = Flask(__name__)
DB_NAME = "users.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )''')
        conn.commit()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def validate_input(username, email, password):
    if not username or not email or not password:
        return "All fields are required."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email format."
    if len(password) < 6:
        return "Password must be at least 6 characters."
    return None

@app.route("/", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password")
        error = validate_input(username, email, password)
        if not error:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                              (username, email, hash_password(password)))
                    conn.commit()
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                error = "Email already exists!"
    return render_template_string(SIGNUP_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, email FROM users")
        users = c.fetchall()
    return render_template_string(DASHBOARD_HTML, users=users)

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return redirect(url_for("dashboard"))

SIGNUP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Signup</title>
</head>
<body>
    <h2>Signup Form</h2>
    {% if error %}
        <p style="color:red;">{{ error }}</p>
    {% endif %}
    <form method="post">
        <label>Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Email:</label><br>
        <input type="email" name="email"><br><br>
        <label>Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit">Sign Up</button>
    </form>
    <br>
    <a href="{{ url_for('dashboard') }}">Go to Dashboard</a>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
</head>
<body>
    <h2>Registered Users</h2>
    <table border="1" cellpadding="10">
        <tr>
            <th>ID</th><th>Username</th><th>Email</th><th>Action</th>
        </tr>
        {% for user in users %}
        <tr>
            <td>{{ user[0] }}</td>
            <td>{{ user[1] }}</td>
            <td>{{ user[2] }}</td>
            <td><a href="{{ url_for('delete_user', user_id=user[0]) }}">Delete</a></td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="{{ url_for('signup') }}">Back to Signup</a>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
