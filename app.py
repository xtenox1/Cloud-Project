from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "cloudproject123"

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    user TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM files")
    files = c.fetchall()

    conn.close()

    return render_template("home.html", files=files)


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                  (username,password,"user"))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username,password))

        user = c.fetchone()

        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[3]

            if user[3] == "admin":
                return redirect("/admin")

            return redirect("/")

    return render_template("login.html")


@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    file = request.files["file"]
    filename = file.filename

    file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO files(filename,user) VALUES(?,?)",
              (filename,session["user"]))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/delete/<int:file_id>")
def delete(file_id):

    if session.get("role") != "admin":
        return "Access denied"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM files WHERE id=?",(file_id,))
    conn.commit()

    conn.close()

    return redirect("/admin")


@app.route("/search")
def search():

    query = request.args.get("q")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM files WHERE filename LIKE ?",('%'+query+'%',))
    files = c.fetchall()

    conn.close()

    return render_template("home.html", files=files)


@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return "Access denied"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    c.execute("SELECT * FROM files")
    files = c.fetchall()

    conn.close()

    return render_template("admin.html", users=users, files=files)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


app.run(debug=True)