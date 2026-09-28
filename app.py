from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "evcharge-dev-secret-change-later"
DB = "evcharge.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # Safe migration for the Phase 3 database
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    conn.execute("""CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        location TEXT NOT NULL, charger_type TEXT NOT NULL,
        speed INTEGER NOT NULL, price REAL NOT NULL,
        available_slots INTEGER NOT NULL, status TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        station_id INTEGER NOT NULL, booking_date TEXT NOT NULL,
        booking_time TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Confirmed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(station_id) REFERENCES stations(id))""")
    bcols = [r["name"] for r in conn.execute("PRAGMA table_info(bookings)").fetchall()]
    if "status" not in bcols:
        conn.execute("ALTER TABLE bookings ADD COLUMN status TEXT NOT NULL DEFAULT 'Confirmed'")

    if conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0] == 0:
        stations = [
            ("GreenVolt Station","Andheri East, Mumbai","CCS2",60,18,5,"Available"),
            ("ChargePoint Hub","Bandra West, Mumbai","CCS2",120,20,3,"Available"),
            ("EcoCharge Point","Powai, Mumbai","Type 2",40,16,2,"Available"),
            ("PowerGrid EV Hub","Thane West, Mumbai","CCS2",100,19,4,"Available"),
            ("VoltWay Station","Vashi, Navi Mumbai","Type 2",50,17,0,"Busy")
        ]
        conn.executemany("""INSERT INTO stations
            (name,location,charger_type,speed,price,available_slots,status)
            VALUES (?,?,?,?,?,?,?)""", stations)

    # Demo admin for the mini-project
    admin = conn.execute("SELECT id FROM users WHERE email=?", ("admin@evcharge.com",)).fetchone()
    if not admin:
        conn.execute("""INSERT INTO users (name,email,password,role)
                        VALUES (?,?,?,?)""",
                     ("EVCharge Admin","admin@evcharge.com",
                      generate_password_hash("Admin@123"),"admin"))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session["user"].get("role") != "admin":
            flash("Admin access required.")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        if not name or not email or len(password)<6:
            flash("Enter valid details. Password must be at least 6 characters.")
            return redirect(url_for("register"))
        conn=get_db()
        try:
            conn.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                         (name,email,generate_password_hash(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close(); flash("An account with this email already exists.")
            return redirect(url_for("register"))
        conn.close(); flash("Account created successfully. Please log in.")
        return redirect(url_for("login"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        conn=get_db()
        user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"],password):
            session["user"]={"id":user["id"],"name":user["name"],
                             "email":user["email"],"role":user["role"]}
            return redirect(url_for("admin" if user["role"]=="admin" else "dashboard"))
        flash("Invalid email or password.")
        return redirect(url_for("login"))
    return render_template("auth.html", mode="login")

@app.route("/dashboard")
@login_required
def dashboard():
    conn=get_db()
    bookings=conn.execute("""SELECT b.*,s.name station_name,s.location,s.charger_type,s.price
        FROM bookings b JOIN stations s ON b.station_id=s.id
        WHERE b.user_id=? ORDER BY b.id DESC""",(session["user"]["id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", user=session["user"], bookings=bookings)

@app.route("/stations")
@login_required
def stations():
    q=request.args.get("q","").strip()
    charger=request.args.get("charger","")
    availability=request.args.get("availability","")
    conn=get_db()
    sql="SELECT * FROM stations WHERE 1=1"; params=[]
    if q:
        sql+=" AND (name LIKE ? OR location LIKE ?)"; params += [f"%{q}%",f"%{q}%"]
    if charger:
        sql+=" AND charger_type=?"; params.append(charger)
    if availability=="available":
        sql+=" AND available_slots>0"
    elif availability=="busy":
        sql+=" AND available_slots=0"
    sql+=" ORDER BY available_slots DESC, name"
    rows=conn.execute(sql,params).fetchall()
    conn.close()
    return render_template("stations.html", stations=rows, q=q, charger=charger, availability=availability)

@app.route("/book/<int:station_id>", methods=["GET","POST"])
@login_required
def book(station_id):
    conn=get_db()
    station=conn.execute("SELECT * FROM stations WHERE id=?",(station_id,)).fetchone()
    if not station:
        conn.close(); flash("Station not found."); return redirect(url_for("stations"))
    if request.method=="POST":
        date=request.form["booking_date"]; time=request.form["booking_time"]
        if station["available_slots"]<=0:
            conn.close(); flash("No slots available at this station."); return redirect(url_for("stations"))
        conn.execute("""INSERT INTO bookings
            (user_id,station_id,booking_date,booking_time,status)
            VALUES (?,?,?,?,?)""",
            (session["user"]["id"],station_id,date,time,"Confirmed"))
        conn.execute("""UPDATE stations
            SET available_slots=available_slots-1,
                status=CASE WHEN available_slots-1=0 THEN 'Busy' ELSE 'Available' END
            WHERE id=?""",(station_id,))
        conn.commit(); conn.close()
        flash("Booking confirmed successfully.")
        return redirect(url_for("dashboard"))
    conn.close()
    return render_template("book.html", station=station)

@app.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    conn=get_db()
    booking=conn.execute("""SELECT * FROM bookings
        WHERE id=? AND user_id=?""",(booking_id,session["user"]["id"])).fetchone()
    if not booking:
        conn.close(); flash("Booking not found."); return redirect(url_for("dashboard"))
    if booking["status"] != "Confirmed":
        conn.close(); flash("Only confirmed bookings can be cancelled."); return redirect(url_for("dashboard"))
    conn.execute("UPDATE bookings SET status='Cancelled' WHERE id=?",(booking_id,))
    conn.execute("""UPDATE stations SET available_slots=available_slots+1,
        status='Available' WHERE id=?""",(booking["station_id"],))
    conn.commit(); conn.close()
    flash("Booking cancelled and the slot was released.")
    return redirect(url_for("dashboard"))

@app.route("/admin")
@admin_required
def admin():
    conn=get_db()
    stats = {
        "users": conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0],
        "stations": conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0],
        "bookings": conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
        "active": conn.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'").fetchone()[0]
    }
    bookings=conn.execute("""SELECT b.*,u.name user_name,u.email,
        s.name station_name,s.location
        FROM bookings b
        JOIN users u ON b.user_id=u.id
        JOIN stations s ON b.station_id=s.id
        ORDER BY b.id DESC LIMIT 12""").fetchall()
    stations_list=conn.execute("SELECT * FROM stations ORDER BY id").fetchall()
    conn.close()
    return render_template("admin.html", stats=stats, bookings=bookings, stations=stations_list, user=session["user"])

@app.route("/admin/station/add", methods=["POST"])
@admin_required
def add_station():
    name=request.form["name"].strip()
    location=request.form["location"].strip()
    charger=request.form["charger_type"].strip()
    speed=int(request.form["speed"])
    price=float(request.form["price"])
    slots=int(request.form["available_slots"])
    status="Available" if slots>0 else "Busy"
    conn=get_db()
    conn.execute("""INSERT INTO stations
        (name,location,charger_type,speed,price,available_slots,status)
        VALUES (?,?,?,?,?,?,?)""",(name,location,charger,speed,price,slots,status))
    conn.commit(); conn.close()
    flash("Station added successfully.")
    return redirect(url_for("admin"))

@app.route("/admin/station/<int:station_id>/delete", methods=["POST"])
@admin_required
def delete_station(station_id):
    conn=get_db()
    count=conn.execute("SELECT COUNT(*) FROM bookings WHERE station_id=? AND status='Confirmed'",(station_id,)).fetchone()[0]
    if count:
        conn.close(); flash("Cannot delete a station with active bookings."); return redirect(url_for("admin"))
    conn.execute("DELETE FROM stations WHERE id=?",(station_id,))
    conn.commit(); conn.close()
    flash("Station deleted.")
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
