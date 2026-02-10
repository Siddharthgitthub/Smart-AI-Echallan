import os
import cv2
import easyocr
import re
from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from config import get_db_connection
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["admin"] = username
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM challans")
    total = cur.fetchone()[0]

    cur.execute("SELECT SUM(fine) FROM challans")
    total_fine = cur.fetchone()[0]
    if total_fine is None:
        total_fine = 0

    cur.execute("SELECT COUNT(*) FROM challans WHERE status='Paid'")
    paid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM challans WHERE status='Unpaid'")
    unpaid = cur.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",
                           total=total,
                           total_fine=total_fine,
                           paid=paid,
                           unpaid=unpaid)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin",None)
    return redirect("/")

# ---------------- AI NUMBER DETECTION ----------------
@app.route("/detect_number", methods=["POST"])
def detect_number():
    if 'image' not in request.files:
        return jsonify({"number":""})

    file = request.files['image']
    if file.filename == "":
        return jsonify({"number":""})

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    if img is None:
        return jsonify({"number":""})

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(gray)

    detected=""
    pattern = r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}'

    for (bbox, text, prob) in results:
        text = text.upper().replace(" ","")

        # OCR corrections
        text = text.replace("I","1")
        text = text.replace("Z","2")
        text = text.replace("O","0")
        text = text.replace("S","5")

        match = re.findall(pattern, text)
        if match:
            detected = match[0]
            break

    print("Detected:", detected)
    return jsonify({"number":detected})

# ---------------- GENERATE CHALLAN ----------------
@app.route("/generate", methods=["POST"])
def generate():
    if "admin" not in session:
        return redirect("/")

    vehicle = request.form["vehicle"]
    owner = request.form["owner"]
    vehicle_type = request.form["vehicle_type"]
    violation = request.form["violation"]
    fine = request.form["fine"]

    if violation == "Others":
        violation = request.form["other_reason"]
        fine = request.form["other_fine"]

    date = datetime.now().strftime("%d-%m-%Y %H:%M")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO challans(vehicle_no,owner_name,violation,fine,status,date) VALUES(%s,%s,%s,%s,%s,%s)",
        (vehicle+" ("+vehicle_type+")", owner, violation, fine, "Unpaid", date)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- VIEW ALL ----------------
@app.route("/view_all")
def view_all():
    if "admin" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM challans ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()

    return render_template("view_all.html", data=data)

# ---------------- MARK PAID ----------------
@app.route("/mark_paid/<int:id>")
def mark_paid(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE challans SET status='Paid' WHERE id=%s",(id,))
    conn.commit()
    conn.close()
    return redirect("/view_all")

# ---------------- DOWNLOAD PDF ----------------
@app.route("/download/<int:id>")
def download(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM challans WHERE id=%s",(id,))
    data = cur.fetchone()
    conn.close()

    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"GOVERNMENT OF INDIA",ln=True,align="C")
    pdf.cell(0,10,"TRAFFIC POLICE DEPARTMENT",ln=True,align="C")
    pdf.ln(5)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"E-CHALLAN RECEIPT",ln=True,align="C")
    pdf.ln(10)

    pdf.set_font("Arial","",12)

    pdf.cell(50,10,"Challan ID",1)
    pdf.cell(0,10,str(data[0]),1,ln=True)

    pdf.cell(50,10,"Vehicle Number",1)
    pdf.cell(0,10,data[1],1,ln=True)

    pdf.cell(50,10,"Owner Name",1)
    pdf.cell(0,10,data[2],1,ln=True)

    pdf.cell(50,10,"Violation",1)
    pdf.cell(0,10,data[3],1,ln=True)

    pdf.cell(50,10,"Fine Amount",1)
    pdf.cell(0,10,"Rs "+str(data[4]),1,ln=True)

    pdf.cell(50,10,"Payment Status",1)
    pdf.cell(0,10,data[6],1,ln=True)

    pdf.cell(50,10,"Date & Time",1)
    pdf.cell(0,10,data[5],1,ln=True)

    pdf.ln(15)

    pdf.set_font("Arial","B",12)
    pdf.cell(0,10,"Pay within 7 days to avoid penalty.",ln=True)

    pdf.ln(20)
    pdf.cell(0,10,"Authorized Traffic Officer",ln=True,align="R")

    filename=f"pdfs/challan_{id}.pdf"
    pdf.output(filename)

    return send_file(filename, as_attachment=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
