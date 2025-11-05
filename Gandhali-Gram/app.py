from flask import Flask, render_template, request, redirect, session, flash, url_for
import pymysql
from werkzeug.security import check_password_hash
import random, os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ------------------- DATABASE CONFIG -------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Shrikant',
    'database': 'gandhali'
}

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        print("DB Connection Error:", e)
        return None


# ------------------- PUBLIC PAGES -------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/schemes")
def schemes():
    return render_template("schemes.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# ------------------- COMPLAINT PAGE -------------------
# ✅ SHOW COMPLAINTS PAGE (RENAMED)
@app.route("/complaints")
def complaints_page():
    conn = get_db_connection()
    cursor = conn.cursor()   # ✅ No dictionary=True needed

    cursor.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cursor.fetchall()  # ✅ Already dictionaries

    cursor.close()
    conn.close()

    return render_template("complaints.html", complaints=complaints)



# ✅ SUBMIT COMPLAINT
@app.route("/complaints/submit", methods=["POST"])
def complaint_submit():

    name = request.form["name"]
    phone = request.form["phone"]
    address = request.form["address"]
    email = request.form.get("email")
    category = request.form["category"]
    description = request.form["description"]
    photo = request.files.get("photo")

    filename = None

    if photo and photo.filename != "":
        filename = f"complaint_{random.randint(1000,9999)}.jpg"
        save_path = os.path.join("static/uploads", filename)
        photo.save(save_path)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints(name, phone, email, address, category, description, photo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, phone, email, address, category, description, filename))

    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ आपली तक्रार यशस्वीरित्या नोंदवली गेली!", "success")
    return redirect(url_for("complaints_page"))


# ✅ RESOLVE COMPLAINT
@app.route("/resolve/<int:id>")
def resolve(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE complaints SET status='Resolved' WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/complaints")


# ✅ DELETE COMPLAINT
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaints WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/complaints")
# ------------------- LOGIN PAGE -------------------
@app.route("/admin")
def admin_login_page():
    return render_template("login.html")

# ------------------- LOGIN AUTH -------------------
@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db_connection()
    if not conn:
        flash("❌ DB Connection Failed", "danger")
        return redirect("/admin")

    cursor = conn.cursor()

    # ✅ Fetch admin user
    cursor.execute("SELECT * FROM users WHERE username=%s AND role='admin'", (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    # ✅ Password check
    if user and check_password_hash(user["password"], password):

        session["admin_id"] = user["id"]
        session["admin_name"] = user["username"]

        flash("✅ Login Successful!", "success")
        return redirect("/admin/dashboard")

    else:
        flash("❌ Invalid Username or Password!", "danger")
        return redirect("/admin")



# ------------------- ADMIN DASHBOARD -------------------
@app.route("/admin/dashboard")
def admin_dashboard():

    # ✅ Access control
    if "admin_id" not in session:
        flash("⚠ Please login first!", "warning")
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Total complaints
    cursor.execute("SELECT COUNT(*) AS total FROM complaints")
    total_complaints = cursor.fetchone()["total"]

    # ✅ Total team members
    cursor.execute("SELECT COUNT(*) AS total FROM team")
    total_team = cursor.fetchone()["total"]

    # ✅ Total announcements
    cursor.execute("SELECT COUNT(*) AS total FROM announcements")
    total_announcements = cursor.fetchone()["total"]

    # ✅ Fetch all complaints dynamically
    cursor.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # ✅ Send data to dashboard
    return render_template(
        "dashboard.html",
        total_complaints=total_complaints,
        total_team=total_team,
        total_announcements=total_announcements,
        complaints=complaints_data
    )



# ------------------- LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully!", "info")
    return redirect("/admin")



# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app.run(debug=True)
