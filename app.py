from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "cloudproject123"

# مجلد Upload دائم داخل المشروع
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# الاتصال بقاعدة البيانات PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")  # هذا يأتي من Render

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# إنشاء الجداول إذا لم تكن موجودة
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS files(
        id SERIAL PRIMARY KEY,
        filename TEXT,
        username TEXT
    );
    """)
    conn.commit()
    c.close()
    conn.close()

init_db()

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM files")
    files = c.fetchall()
    c.close()
    conn.close()
    return render_template("home.html", files=files)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users(username,password,role) VALUES(%s,%s,%s)", (username,password,"user"))
        conn.commit()
        c.close()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username,password))
        user = c.fetchone()
        c.close()
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
    file = request.files.get("file")
    if file and file.filename:
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO files(filename, username) VALUES(%s,%s)", (filename, session["user"]))
        conn.commit()
        c.close()
        conn.close()
    return redirect("/")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/delete/<int:file_id>")
def delete(file_id):
    if session.get("role") != "admin":
        return "Access denied"
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id=%s", (file_id,))
    conn.commit()
    c.close()
    conn.close()
    return redirect("/admin")

@app.route("/search")
def search():
    query = request.args.get("q", "")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE filename ILIKE %s", ('%'+query+'%',))
    files = c.fetchall()
    c.close()
    conn.close()
    return render_template("home.html", files=files)

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access denied"
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM files")
    files = c.fetchall()
    c.close()
    conn.close()
    return render_template("admin.html", users=users, files=files)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)