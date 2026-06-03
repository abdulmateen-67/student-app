from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import redis
import json

app = Flask(__name__)
CORS(app)

# -------------------------
# PostgreSQL connection
# -------------------------
def get_db():
    return psycopg2.connect(
        host="db",
        database="students",
        user="postgres",
        password="postgres"
    )

# -------------------------
# Redis connection
# -------------------------
cache = redis.Redis(host="redis", port=6379, decode_responses=True)

# -------------------------
# CREATE TABLE (runs once)
# -------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT,
            roll TEXT,
            dept TEXT,
            semester TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# -------------------------
# POST - Add Student
# -------------------------
@app.route("/students", methods=["POST"])
def add_student():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO students (name, roll, dept, semester) VALUES (%s, %s, %s, %s)",
        (data["name"], data["roll"], data["dept"], data["semester"])
    )

    conn.commit()

    cur.close()
    conn.close()

    # Clear cache when new data is added
    cache.delete("students")

    return jsonify({"message": "Student added successfully"})


# -------------------------
# GET - All Students (with Redis cache)
# -------------------------
@app.route("/students", methods=["GET"])
def get_students():

    # Check cache first
    cached_data = cache.get("students")

    if cached_data:
        return jsonify(json.loads(cached_data))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # store in cache
    cache.set("students", json.dumps(rows))

    return jsonify(rows)


# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
