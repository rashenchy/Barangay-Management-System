from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
CORS(app)


# ------------------------------
# DATABASE CONNECTION
# ------------------------------
def get_db():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="brgy_db"
    )


# ==================== AUTHENTICATION ====================
@app.post("/register")
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "Staff")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    pw_hash = generate_password_hash(password)
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                    (username, pw_hash, role))
        db.commit()
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        cur.close()
        db.close()

    return jsonify({"status": "registered"})


@app.post("/login")
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    db.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"status": "ok", "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})


# ==================== DASHBOARD ANALYTICS ====================
@app.get("/dashboard-stats")
def get_dashboard_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 1. Total Population
    cur.execute("SELECT COUNT(*) as count FROM residents")
    pop_count = cur.fetchone()['count']

    # 2. Voters
    cur.execute("SELECT COUNT(*) as count FROM residents WHERE voter_status='Voter'")
    voter_count = cur.fetchone()['count']

    # 3. Gender Stats
    cur.execute("SELECT COUNT(*) as count FROM residents WHERE gender='Male'")
    male_count = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM residents WHERE gender='Female'")
    female_count = cur.fetchone()['count']

    # 4. Active Blotter Cases
    try:
        cur.execute("SELECT COUNT(*) as count FROM blotters WHERE status != 'Closed' AND status != 'Settled'")
        active_cases = cur.fetchone()['count']
    except:
        active_cases = 0

    cur.close()
    db.close()

    return jsonify({
        "population": pop_count,
        "voters": voter_count,
        "males": male_count,
        "females": female_count,
        "active_cases": active_cases
    })


# ==================== RESIDENTS ====================

@app.get("/residents")
def get_residents():
    q = request.args.get("q", "").strip()
    db = get_db()
    cur = db.cursor(dictionary=True)

    if q:
        like = f"%{q}%"
        sql = """
        SELECT * FROM residents
         WHERE first_name LIKE %s 
            OR middle_name LIKE %s 
            OR last_name LIKE %s
            OR CAST(id as CHAR) LIKE %s 
            OR purok LIKE %s
            OR gender LIKE %s 
            OR voter_status LIKE %s 
            OR civil_status LIKE %s
        ORDER BY last_name, first_name
        """
        cur.execute(sql, [like] * 8)
    else:
        cur.execute("SELECT * FROM residents ORDER BY last_name, first_name")

    rows = cur.fetchall()

    # Normalize dates
    for r in rows:
        if r.get("birthdate"): r["birthdate"] = str(r["birthdate"])

    cur.close()
    db.close()
    return jsonify(rows)

@app.post("/resident")
def add_resident():
    data = request.json
    db = get_db()
    cur = db.cursor()
    sql = """
        INSERT INTO residents 
        (first_name, middle_name, last_name, extension, gender, birthdate, 
         civil_status, contact, occupation, voter_status, emergency_contact, purok)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    params = (
        data.get("first_name"), data.get("middle_name"), data.get("last_name"),
        data.get("extension", "N/A"), data.get("gender"), data.get("birthdate"),
        data.get("civil_status"), data.get("contact"), data.get("occupation"),
        data.get("voter_status"), data.get("emergency_contact"), data.get("purok"),
    )
    try:
        cur.execute(sql, params)
        db.commit()
        return jsonify({"status": "success", "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        db.close()


@app.put("/resident/<rid>")
def update_resident(rid):
    data = request.json
    db = get_db()
    cur = db.cursor()
    sql = """
    UPDATE residents SET
      first_name=%s, middle_name=%s, last_name=%s, extension=%s, gender=%s,
      birthdate=%s, civil_status=%s, contact=%s, occupation=%s,
      voter_status=%s, emergency_contact=%s, purok=%s
    WHERE id=%s
    """
    params = (
        data.get("first_name"), data.get("middle_name"), data.get("last_name"),
        data.get("extension"), data.get("gender"), data.get("birthdate"),
        data.get("civil_status"), data.get("contact"), data.get("occupation"),
        data.get("voter_status"), data.get("emergency_contact"), data.get("purok"), rid,
    )
    cur.execute(sql, params)
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "updated"})


@app.delete("/resident/<rid>")
def delete_resident(rid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM residents WHERE id=%s", (rid,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "deleted"})


# ==================== BLOTTERS ====================
@app.get("/blotters")
def get_blotters():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM blotters ORDER BY id DESC")
    except:
        cur.execute("SELECT * FROM blotters ORDER BY id DESC")
    rows = cur.fetchall()
    for r in rows:
        if r.get("last_incident"): r["last_incident"] = str(r["last_incident"])
        if r.get("hearing_schedule"): r["hearing_schedule"] = str(r["hearing_schedule"])
    cur.close()
    db.close()
    return jsonify(rows)


@app.post("/blotter")
def save_blotter():
    data = request.json
    comp = data.get("complainant_name")
    defe = data.get("defendant_name")
    inc_date = data.get("incident_date")
    details = data.get("details", "")
    c_stmt = data.get("complainant_statement", "")
    d_stmt = data.get("defendant_statement", "")
    status = data.get("status", "Active")
    hearing = data.get("hearing_schedule")

    # NEW FIELDS
    nature = data.get("nature_of_case", "")
    remarks = data.get("remarks", "")
    same_inc = data.get("same_incident")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Check Existing
    cur.execute("SELECT * FROM blotters WHERE complainant_name=%s AND defendant_name=%s LIMIT 1", (comp, defe))
    existing = cur.fetchone()
    blotter_id = None

    if not existing:
        cur2 = db.cursor()
        sql = """INSERT INTO blotters 
                   (complainant_name, defendant_name, nature_of_case, last_incident, total_incidents, status, hearing_schedule, remarks,
                   complainant_address, complainant_contact, defendant_address, defendant_contact) 
                   VALUES (%s,%s,%s,%s,1,%s,%s,%s, %s,%s,%s,%s)"""
        cur2.execute(sql, (
            comp, defe, nature, inc_date, status, hearing, remarks,
            data.get("complainant_address"), data.get("complainant_contact"),
            data.get("defendant_address"), data.get("defendant_contact")
        ))
        db.commit()
        blotter_id = cur2.lastrowid

        # Add Initial Incident
        cur2.execute(
            "INSERT INTO blotters_incidents (blotter_id, incident_date, details, speaker) VALUES (%s,%s,%s,'both')",
            (blotter_id, inc_date, details))
        db.commit()

    else:
        blotter_id = existing["id"]
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE blotters 
            SET status=%s, hearing_schedule=%s, nature_of_case=%s, remarks=%s 
            WHERE id=%s
        """, (status, hearing, nature, remarks, blotter_id))

        if same_inc is True:
            cur.execute("SELECT * FROM blotters_incidents WHERE blotter_id=%s ORDER BY id DESC LIMIT 1", (blotter_id,))
            last_inc = cur.fetchone()
            prev = last_inc.get("details") or ""
            new_det = prev + f"\n\n--- Update ({inc_date}) ---\n{details}"
            cur2.execute("UPDATE blotters_incidents SET details=%s WHERE id=%s", (new_det, last_inc["id"]))
        else:
            cur2.execute(
                "INSERT INTO blotters_incidents (blotter_id, incident_date, details, speaker) VALUES (%s,%s,%s,'both')",
                (blotter_id, inc_date, details))
            cur2.execute("UPDATE blotters SET last_incident=%s, total_incidents=total_incidents+1 WHERE id=%s",
                         (inc_date, blotter_id))
        db.commit()

    # Statements
    cur3 = db.cursor(dictionary=True)  # Siguraduhing naka-dictionary=True para mas madali

    if c_stmt:
        cur3.execute("""
            SELECT statement FROM blotters_incidents 
            WHERE blotter_id=%s AND speaker='complainant' 
            ORDER BY id DESC LIMIT 1
        """, (blotter_id,))
        last_c = cur3.fetchone()

        if not last_c or last_c['statement'] != c_stmt:
            cur3.execute(
                "INSERT INTO blotters_incidents (blotter_id, incident_date, statement, speaker) VALUES (%s,%s,%s,'complainant')",
                (blotter_id, inc_date, c_stmt))

    if d_stmt:
        cur3.execute("""
            SELECT statement FROM blotters_incidents 
            WHERE blotter_id=%s AND speaker='defendant' 
            ORDER BY id DESC LIMIT 1
        """, (blotter_id,))
        last_d = cur3.fetchone()

        if not last_d or last_d['statement'] != d_stmt:
            cur3.execute(
                "INSERT INTO blotters_incidents (blotter_id, incident_date, statement, speaker) VALUES (%s,%s,%s,'defendant')",
                (blotter_id, inc_date, d_stmt))

    db.commit()
    cur3.close()
    db.close()

    return jsonify({"status": "saved", "id": blotter_id})


@app.get("/blotter/<int:bid>/incidents")
def get_incidents(bid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM blotters WHERE id=%s", (bid,))
    blotter = cur.fetchone()
    cur.execute("SELECT * FROM blotters_incidents WHERE blotter_id=%s ORDER BY id ASC", (bid,))
    incidents = cur.fetchall()

    if blotter and blotter.get("hearing_schedule"): blotter["hearing_schedule"] = str(blotter["hearing_schedule"])
    for i in incidents:
        if i.get("incident_date"): i["incident_date"] = str(i["incident_date"])

    cur.close()
    db.close()
    return jsonify({"blotter": blotter, "incidents": incidents})


@app.delete("/blotter/<int:bid>")
def delete_blotter(bid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM blotters_incidents WHERE blotter_id=%s", (bid,))
    cur.execute("DELETE FROM blotters WHERE id=%s", (bid,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "deleted"})


# ==================== HOUSEHOLDS & VOTERS ====================

@app.get("/households")
def get_households():
    db = get_db()
    cur = db.cursor(dictionary=True)
    sql = """
        SELECT h.household_id as id, h.purok, 
               r.first_name, r.middle_name, r.last_name, r.extension,
        (SELECT COUNT(*) FROM household_members WHERE household_id=h.household_id) as members
        FROM households h
        LEFT JOIN residents r ON r.id = h.head_id
    """
    cur.execute(sql)
    rows = cur.fetchall()

    # --- Format name to include Middle Name and Extension ---
    for r in rows:
        parts = [
            r.get("first_name", ""),
            r.get("middle_name", ""),
            r.get("last_name", ""),
            r.get("extension", "")
        ]
        clean_parts = [str(p).strip() for p in parts if p and str(p).strip() not in ["N/A", "None", ""]]
        r["head_name"] = " ".join(clean_parts)

    cur.close()
    db.close()
    return jsonify(rows)


@app.get("/household/<int:hid>")
def get_household_detail(hid):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 1. Get Header (Head of Household)
    cur.execute("""
        SELECT h.household_id as id, h.purok, 
               r.first_name, r.middle_name, r.last_name, r.extension, 
               r.id as head_resident_id
        FROM households h 
        LEFT JOIN residents r ON r.id = h.head_id
        WHERE h.household_id=%s
    """, (hid,))
    head = cur.fetchone()

    if not head:
        return jsonify({"error": "Not found"}), 404

    # --- FIXED: Format Head Name ---
    parts = [
        head.get("first_name", ""),
        head.get("middle_name", ""),
        head.get("last_name", ""),
        head.get("extension", "")
    ]
    clean_parts = [str(p).strip() for p in parts if p and str(p).strip() not in ["N/A", "None", ""]]
    head["head_name"] = " ".join(clean_parts)

    # 2. Get Members
    cur.execute("""
        SELECT m.id, m.resident_id, m.relationship, 
               r.first_name, r.middle_name, r.last_name, r.extension
        FROM household_members m
        JOIN residents r ON r.id = m.resident_id
        WHERE m.household_id=%s
    """, (hid,))
    members = cur.fetchall()

    # --- FIXED: Format Member Names ---
    for m in members:
        m_parts = [
            m.get("first_name", ""),
            m.get("middle_name", ""),
            m.get("last_name", ""),
            m.get("extension", "")
        ]
        m_clean = [str(p).strip() for p in m_parts if p and str(p).strip() not in ["N/A", "None", ""]]
        m["full_name"] = " ".join(m_clean)

    head["members"] = members
    cur.close()
    db.close()
    return jsonify(head)

@app.post("/household")
def add_household():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO households (head_id, purok) VALUES (%s,%s)", (data['head_id'], data['purok']))
    db.commit()
    return jsonify({"status": "created", "id": cur.lastrowid})


@app.put("/household/<int:hid>")
def update_household(hid):
    data = request.json
    head_id = data.get('head_id')
    purok = data.get('purok')
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("UPDATE households SET head_id=%s, purok=%s WHERE household_id=%s",
                    (head_id, purok, hid))
        db.commit()
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        db.close()


@app.post("/household/<int:hid>/member")
def add_member(hid):
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO household_members (household_id, resident_id, relationship) VALUES (%s,%s,%s)",
                (hid, data['resident_id'], data['relationship']))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "ok"})


@app.put("/household/<int:hid>/member/<int:rid>")
def update_member_relationship(hid, rid):
    data = request.json
    relationship = data.get('relationship')
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE household_members 
            SET relationship=%s 
            WHERE household_id=%s AND resident_id=%s
        """, (relationship, hid, rid))
        db.commit()
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        db.close()


@app.delete("/household/<int:hid>/member/<int:mid>")
def remove_member(hid, mid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM household_members WHERE id=%s", (mid,))  # Note: using unique member ID
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "ok"})


@app.delete("/household/<int:hid>")
def delete_household(hid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM household_members WHERE household_id=%s", (hid,))
    cur.execute("DELETE FROM households WHERE household_id=%s", (hid,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "ok"})

@app.get("/voters")
def get_voters():
    q = request.args.get("q", "")
    purok = request.args.get("purok", "")
    status = request.args.get("status", "Voter")

    db = get_db()
    cur = db.cursor(dictionary=True)

    sql = "SELECT * FROM residents WHERE 1=1"
    params = []

    # 1. Filter by Status
    if status and status != "All":
        sql += " AND voter_status = %s"
        params.append(status)

    # 2. Filter by Purok
    if purok and purok != "All":
        sql += " AND purok = %s"
        params.append(purok)

    # 3. Search by Name
    if q:
        sql += " AND (CAST(id as CHAR) LIKE %s OR first_name LIKE %s OR middle_name LIKE %s OR last_name LIKE %s)"
        like_q = f"%{q}%"
        params.append(like_q)
        params.append(like_q)
        params.append(like_q)
        params.append(like_q)

    sql += " ORDER BY purok, last_name"

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(rows)

# ==================== NEW: OFFICIALS MANAGEMENT ====================
@app.get("/officials")
def get_officials():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM officials")
    rows = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(rows)


@app.post("/officials/update")
def update_officials():
    data = request.json
    db = get_db()
    cur = db.cursor()

    if isinstance(data, list):
        for off in data:
            pos = off.get("position")
            name = off.get("full_name")
            # Check if exists
            cur.execute("SELECT id FROM officials WHERE position=%s", (pos,))
            exist = cur.fetchone()
            if exist:
                cur.execute("UPDATE officials SET full_name=%s WHERE position=%s", (name, pos))
            else:
                cur.execute("INSERT INTO officials (position, full_name) VALUES (%s, %s)", (pos, name))

    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "updated"})


# ==================== NEW: CERTIFICATES ====================

@app.get("/certificate/next-or")
def get_next_or():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT MAX(CAST(or_number AS UNSIGNED)) FROM certificate_logs")
    max_or = cur.fetchone()[0]
    cur.close()
    db.close()

    if max_or:
        next_val = int(max_or) + 1
    else:
        next_val = 1001

    return jsonify({"next_or": next_val})


@app.post("/certificate/log")
def log_certificate():
    data = request.json
    db = get_db()
    cur = db.cursor()
    sql = """
        INSERT INTO certificate_logs (resident_id, certificate_type, purpose, or_number, amount_paid, issued_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get("resident_id"), data.get("certificate_type"), data.get("purpose"),
        data.get("or_number"), data.get("amount_paid"), data.get("issued_by")
    )
    cur.execute(sql, params)
    db.commit()
    cur.close()
    db.close()
    return jsonify({"status": "logged"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)