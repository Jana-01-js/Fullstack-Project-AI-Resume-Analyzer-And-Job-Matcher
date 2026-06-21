from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os, re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "change-this-secret"

DB = "resume_analyzer.db"
UPLOADS = "uploads"
os.makedirs(UPLOADS, exist_ok=True)

SKILLS = [
    "python","java","c++","sql","html","css","javascript","react",
    "flask","django","machine learning","opencv","azure","mysql"
]

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def score_resume(text):
    text = text.lower()
    found = [s for s in SKILLS if s in text]
    score = round((len(found) / len(SKILLS)) * 100, 2)
    missing = [s for s in SKILLS if s not in found]
    return score, found, missing

HOME = """
<!doctype html>
<html><head><title>AI Resume Analyzer</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;padding:40px}
.card{max-width:800px;margin:auto;background:#1e293b;padding:25px;border-radius:12px}
input,button{padding:10px;margin:5px}
button{background:#38bdf8;border:none}
a{color:#38bdf8}
</style></head><body>
<div class="card">
<h1>AI Resume Analyzer</h1>
{% if user %}
<p>Welcome {{user}} | <a href="/logout">Logout</a></p>
<form method="post" enctype="multipart/form-data" action="/analyze">
<input type="file" name="resume" required>
<button>Analyze Resume</button>
</form>
{% if result %}
<hr>
<h2>ATS Score: {{result.score}}%</h2>
<p><b>Skills Found:</b> {{result.found}}</p>
<p><b>Missing Skills:</b> {{result.missing}}</p>
{% endif %}
{% else %}
<a href="/login">Login</a> | <a href="/register">Register</a>
{% endif %}
</div></body></html>
"""

AUTH = """
<!doctype html><html><body style="font-family:Arial;padding:40px">
<h2>{{title}}</h2>
<form method="post">
<input name="username" placeholder="Username"><br><br>
<input type="password" name="password" placeholder="Password"><br><br>
<button>Submit</button>
</form>
<a href="/">Home</a>
</body></html>
"""

@app.route("/")
def home():
    return render_template_string(HOME, user=session.get("user"), result=None)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            conn = sqlite3.connect(DB)
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)",
                         (request.form["username"], request.form["password"]))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return "User already exists"
    return render_template_string(AUTH, title="Register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                    (request.form["username"], request.form["password"]))
        user = cur.fetchone()
        conn.close()
        if user:
            session["user"] = request.form["username"]
            return redirect("/")
        return "Invalid credentials"
    return render_template_string(AUTH, title="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    f = request.files["resume"]
    path = os.path.join(UPLOADS, secure_filename(f.filename))
    f.save(path)

    try:
        text = open(path, "rb").read().decode(errors="ignore")
    except:
        text = ""

    score, found, missing = score_resume(text)

    result = {
        "score": score,
        "found": ", ".join(found) if found else "None",
        "missing": ", ".join(missing[:10])
    }

    return render_template_string(HOME,
                                  user=session.get("user"),
                                  result=result)

if __name__ == "__main__":
    app.run(debug=True)
