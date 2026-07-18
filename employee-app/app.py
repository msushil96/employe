import os
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---- DB config (all from environment variables) ----
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "app_user"),
    "password": os.getenv("DB_PASSWORD", "app_password"),
    "database": os.getenv("DB_NAME", "employee_directory"),
}

# Connection pool so the app doesn't open a new TCP connection per request
pool = None

def get_pool():
    global pool
    if pool is None:
        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="app_pool",
            pool_size=5,
            **DB_CONFIG
        )
    return pool


def get_connection():
    return get_pool().get_connection()


# ---- Health check endpoint (for load balancer / k8s probes) ----
@app.route("/health")
def health():
    try:
        conn = get_connection()
        conn.ping(reconnect=False)
        conn.close()
        return jsonify(status="ok", db="connected"), 200
    except Exception as e:
        return jsonify(status="error", db="unreachable", detail=str(e)), 503


# ---- Readiness endpoint (optional, separate from liveness) ----
@app.route("/ready")
def ready():
    return jsonify(status="ready"), 200


# ---- UI ----
@app.route("/")
def index():
    return render_template("index.html")


# ---- API: list employees ----
@app.route("/api/employees", methods=["GET"])
def list_employees():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, role, department, email FROM employees ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


# ---- API: add employee ----
@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    required = ["name", "role", "department", "email"]
    if not all(k in data and data[k] for k in required):
        return jsonify(error="Missing required fields"), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, role, department, email) VALUES (%s, %s, %s, %s)",
        (data["name"], data["role"], data["department"], data["email"])
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify(id=new_id), 201


# ---- API: delete employee ----
@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected == 0:
        return jsonify(error="Not found"), 404
    return jsonify(deleted=emp_id), 200


if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
